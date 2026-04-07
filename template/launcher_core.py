import os
import atexit
import winreg
import ctypes
import sys
import threading
import time
import json
import datetime
import concurrent.futures
from pathlib import Path
from typing import Optional, List, Set, Callable


class SelfUpdater:
    """
    自我更新器 — 将扫描到的路径嵌入 EXE 尾部，实现"一次找到，永久秒开"。

    v3.0 改进：
    - 使用 atexit + os.replace 替代释放 .bat 脚本，降低杀软启发式报警。
    - 使用 MoveFileExW(MOVEFILE_DELAY_UNTIL_REBOOT) 作为 fallback。
    """

    MARKER: bytes = b'<<PROPAGATION_DATA>>'

    def __init__(self) -> None:
        self.exe_path: str = sys.executable
        self.original_data: Optional[bytes] = None
        self.known_paths: List[str] = []
        self.loaded: bool = False
        self._tmp_path: Optional[str] = None  # 临时文件路径，供 atexit 使用

    def load(self) -> None:
        """从自身 EXE 尾部加载已知路径数据。"""
        if not getattr(sys, 'frozen', False):
            return

        try:
            with open(self.exe_path, 'rb') as f:
                content = f.read()

            parts = content.split(self.MARKER)
            self.original_data = parts[0]

            if len(parts) > 1:
                try:
                    last_part = parts[-1]
                    json_str = last_part.decode('utf-8', errors='ignore').strip().strip('\0')
                    if json_str:
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            self.known_paths = data
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                    pass

            self.loaded = True
        except (OSError, IOError) as e:
            print(f"Update load failed: {e}")

    def update(self, new_paths: List[str]) -> None:
        """
        计划在进程退出时更新自身 EXE 的嵌入数据。

        不再释放 .bat 脚本，而是通过 atexit 钩子在退出时直接执行原子替换。
        """
        if not self.loaded or not self.original_data:
            return

        # 合并路径
        current_set: Set[str] = set(self.known_paths)
        has_new = False
        for p in new_paths:
            if p and p not in current_set:
                current_set.add(p)
                has_new = True

        if not has_new:
            return

        final_paths = list(current_set)
        print(f"Scheduling self-update with {len(final_paths)} paths...")

        try:
            # 准备新文件内容
            json_data = json.dumps(final_paths).encode('utf-8')
            new_content = self.original_data + self.MARKER + json_data

            self._tmp_path = self.exe_path + ".tmp"
            with open(self._tmp_path, 'wb') as f:
                f.write(new_content)

            # 注册 atexit 钩子，在进程退出时执行替换
            atexit.register(self._do_replace)

        except (OSError, IOError) as e:
            print(f"Update prepare failed: {e}")

    def _do_replace(self) -> None:
        """
        atexit 回调：尝试将 .tmp 文件原子替换为当前 EXE。

        策略：
        1. 优先使用 os.replace() 进行原子替换（如果进程文件锁已释放）。
        2. 若失败，使用 Windows API MoveFileExW + MOVEFILE_DELAY_UNTIL_REBOOT
           让系统在下次重启时完成替换。
        3. 任何阶段失败都静默忽略，不影响正常退出。
        """
        if not self._tmp_path or not os.path.exists(self._tmp_path):
            return

        try:
            # 策略 1：直接原子替换
            os.replace(self._tmp_path, self.exe_path)
            print("Self-update: replaced successfully via os.replace.")
            return
        except PermissionError:
            pass  # 文件仍被锁定，尝试 fallback
        except OSError:
            pass

        try:
            # 策略 2：注册系统级延迟替换（下次重启生效）
            MOVEFILE_DELAY_UNTIL_REBOOT = 0x4
            MOVEFILE_REPLACE_EXISTING = 0x1
            flags = MOVEFILE_DELAY_UNTIL_REBOOT | MOVEFILE_REPLACE_EXISTING

            result = ctypes.windll.kernel32.MoveFileExW(
                self._tmp_path,
                self.exe_path,
                flags
            )
            if result:
                print("Self-update: scheduled for next reboot via MoveFileExW.")
            else:
                # 静默忽略 — 可能权限不足
                pass
        except (OSError, AttributeError):
            # 静默忽略
            pass


class PathCache:
    """管理本地路径缓存，实现'一次找到，永久秒开'。"""

    def __init__(self) -> None:
        self.cache_dir: str = os.path.join(
            os.environ.get("LOCALAPPDATA", "."), "FakeLauncherCache"
        )
        self.cache_file: str = os.path.join(self.cache_dir, "known_paths.json")
        self._ensure_dir()
        self.cache: dict = self._load_cache()

    def _ensure_dir(self) -> None:
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except OSError:
                pass

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, ValueError):
                return {}
        return {}

    def get_path(self, exe_name: str) -> Optional[str]:
        path = self.cache.get(exe_name.lower())
        if path and os.path.exists(path):
            return path
        return None

    def update_path(self, exe_name: str, path: str) -> None:
        self.cache[exe_name.lower()] = path
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except OSError:
            pass


class GameScanner:
    """
    游戏/程序扫描器。

    v3.0 改进：
    - scan_drives() 和 scan_common_paths() 使用 ThreadPoolExecutor 并发扫描。
    - 使用 threading.Event 实现"一处发现，全盘停止"。
    - 精确的异常捕获（PermissionError, OSError），不再使用裸 except。
    """

    def __init__(self, target_exe: str, target_name: str) -> None:
        self.target_exe: str = target_exe
        self.target_name: str = target_name
        self.found_path: Optional[str] = None
        self.stop_flag: bool = False
        self.log_callback: Optional[Callable[[str], None]] = None
        self.logs: List[str] = []
        self.cache: PathCache = PathCache()

        # 并发扫描用的全局"已找到"事件
        self._found_event: threading.Event = threading.Event()
        # 线程安全锁，保护 found_path 写入
        self._lock: threading.Lock = threading.Lock()

        # 初始化自我更新器
        self.self_updater: SelfUpdater = SelfUpdater()
        self.self_updater.load()

        # 扫描黑名单（小写，用于忽略系统目录）
        self.blacklist_dirs: Set[str] = {
            'windows', 'programdata', 'system volume information',
            '$recycle.bin', 'msocache', 'config.msi', 'recovery',
            'documents and settings', 'perflogs', 'boot',
            'common files', 'internet explorer', 'windows defender',
            'microsoft.net'
        }

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """设置日志回调函数 func(message)"""
        self.log_callback = callback

    def log(self, message: str) -> None:
        """记录带时间戳的日志。"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)

        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    # ------------------------------------------------------------------ #
    #  主扫描入口
    # ------------------------------------------------------------------ #

    def scan(self) -> Optional[str]:
        """
        按优先级依次扫描，返回找到的目标路径或 None。

        扫描顺序：缓存 → 自身数据 → 注册表 → 常用路径 → 全盘扫描
        """
        self.log(f"开始寻找 {self.target_name} ({self.target_exe})...")

        # 0. 优先检查本地缓存 (最高优先级)
        if self.scan_cache():
            return self.found_path

        # 0.5 检查自身携带的数据 (自我繁殖数据)
        if self.scan_self_data():
            self._update_cache()
            return self.found_path

        # 1. 扫描注册表
        if self.scan_registry():
            self._update_cache()
            return self.found_path

        # 2. 扫描常用路径 (Program Files 等) — 并发
        if self.scan_common_paths():
            self._update_cache()
            return self.found_path

        # 3. 全盘扫描 — 并发
        if self.scan_drives():
            self._update_cache()
            return self.found_path

        return None

    def _update_cache(self) -> None:
        if self.found_path:
            self.log(f"更新本地缓存: {self.found_path}")
            self.cache.update_path(self.target_exe, self.found_path)
            self.self_updater.update([self.found_path])

    # ------------------------------------------------------------------ #
    #  快速路径：缓存 / 自身数据
    # ------------------------------------------------------------------ #

    def scan_cache(self) -> bool:
        self.log("检查本地缓存记录...")
        cached_path = self.cache.get_path(self.target_exe)
        if cached_path:
            self.log(f"在缓存中快速定位到: {cached_path}")
            self.found_path = cached_path
            return True
        return False

    def scan_self_data(self) -> bool:
        """检查 EXE 自身携带的数据。"""
        if not self.self_updater.known_paths:
            return False

        self.log(f"检查自身携带的 {len(self.self_updater.known_paths)} 条记录...")
        for path in self.self_updater.known_paths:
            check_path = path
            if not path.lower().endswith(self.target_exe.lower()):
                check_path = os.path.join(path, self.target_exe)

            if os.path.exists(check_path) and os.path.isfile(check_path):
                self.log(f"在自身记录中发现: {check_path}")
                self.found_path = check_path
                return True
        return False

    # ------------------------------------------------------------------ #
    #  注册表扫描
    # ------------------------------------------------------------------ #

    def scan_registry(self) -> bool:
        self.log("正在扫描系统注册表...")
        registry_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]

        for hkey_root, reg_path in registry_roots:
            if self.stop_flag or self._found_event.is_set():
                return False
            try:
                with winreg.OpenKey(hkey_root, reg_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if self.target_name.lower() in str(display_name).lower():
                                        self.log(f"在注册表中发现疑似项: {display_name}")
                                        try:
                                            install_loc = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                            if install_loc:
                                                if self.check_file_in_dir(install_loc):
                                                    return True
                                        except OSError:
                                            pass
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue
        return False

    # ------------------------------------------------------------------ #
    #  常用路径扫描 — 并发版
    # ------------------------------------------------------------------ #

    def scan_common_paths(self) -> bool:
        """并发扫描常用安装目录。"""
        self.log("扫描常用安装目录...")

        user_home = os.environ.get("USERPROFILE")
        local_appdata = os.environ.get("LOCALAPPDATA")
        roaming_appdata = os.environ.get("APPDATA")

        common_dirs: List[str] = [
            os.environ.get("ProgramFiles", ""),
            os.environ.get("ProgramFiles(x86)", ""),
            local_appdata or "",
            roaming_appdata or "",
            os.path.join(local_appdata, "Programs") if local_appdata else "",
            os.path.join(user_home, "Desktop") if user_home else "",
            os.path.join(user_home, "Downloads") if user_home else "",
        ]

        # 其他盘符的常见目录
        drives = self.get_available_drives()
        for drive in drives:
            if drive.lower().startswith("c:"):
                continue
            common_dirs.extend([
                os.path.join(drive, "Program Files"),
                os.path.join(drive, "Program Files (x86)"),
                os.path.join(drive, "Games"),
                os.path.join(drive, "Game"),
                os.path.join(drive, "Software"),
            ])

        # 去重并过滤空值和不存在的路径
        common_dirs = list({d for d in common_dirs if d and os.path.exists(d)})

        if not common_dirs:
            return False

        # 重置 found_event（确保干净状态）
        self._found_event.clear()

        # 并发扫描所有常用目录
        max_workers = min(len(common_dirs), 8)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_directory, base_dir, max_depth=4): base_dir
                for base_dir in common_dirs
            }

            for future in concurrent.futures.as_completed(futures):
                base_dir = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.log(f"在常用路径中发现: {result}")
                        with self._lock:
                            if not self.found_path:
                                self.found_path = result
                        # 取消剩余任务
                        for f in futures:
                            f.cancel()
                        return True
                except (PermissionError, OSError):
                    pass

        return False

    # ------------------------------------------------------------------ #
    #  全盘扫描 — 并发版
    # ------------------------------------------------------------------ #

    def scan_drives(self) -> bool:
        """并发扫描所有驱动器（每个驱动器一个线程）。"""
        self.log("开始全盘深度扫描...")
        drives = self.get_available_drives()

        if not drives:
            return False

        # 重置 found_event
        self._found_event.clear()

        # 每个驱动器一个线程
        max_workers = len(drives)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_single_drive, drive): drive
                for drive in drives
            }

            for future in concurrent.futures.as_completed(futures):
                drive = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.log(f"全盘扫描发现: {result}")
                        with self._lock:
                            if not self.found_path:
                                self.found_path = result
                        # 取消剩余任务
                        for f in futures:
                            f.cancel()
                        return True
                except (PermissionError, OSError):
                    pass

        return False

    def _scan_single_drive(self, drive: str) -> Optional[str]:
        """
        扫描单个驱动器（在 worker 线程中执行）。

        通过 _found_event 和 stop_flag 实现"一处发现，全盘停止"。
        """
        self.log(f"正在扫描驱动器 {drive} ...")
        try:
            for root, dirs, files in os.walk(drive):
                # 检查是否应该提前终止
                if self.stop_flag or self._found_event.is_set():
                    return None

                # --- 智能过滤逻辑 ---
                current_dir_name = os.path.basename(root).lower()
                if current_dir_name in self.blacklist_dirs:
                    dirs.clear()
                    continue

                # 预先过滤子目录，反向遍历移除黑名单目录
                for i in range(len(dirs) - 1, -1, -1):
                    if dirs[i].lower() in self.blacklist_dirs:
                        del dirs[i]

                # 检查当前目录的文件
                if self.target_exe in files:
                    full_path = os.path.join(root, self.target_exe)
                    self._found_event.set()  # 通知其他线程停止
                    return full_path

        except PermissionError:
            pass  # 驱动器根目录权限异常，静默跳过
        except OSError as e:
            self.log(f"扫描驱动器 {drive} 时出错: {e}")

        return None

    def _scan_directory(self, base_dir: str, max_depth: int = 4) -> Optional[str]:
        """
        扫描单个目录（带深度限制，在 worker 线程中执行）。

        Args:
            base_dir: 要扫描的根目录
            max_depth: 最大递归深度
        """
        try:
            for root, dirs, files in os.walk(base_dir):
                if self.stop_flag or self._found_event.is_set():
                    return None

                # 检查当前目录的文件
                if self.target_exe in files:
                    full_path = os.path.join(root, self.target_exe)
                    self._found_event.set()
                    return full_path

                # 深度限制
                try:
                    rel_path = os.path.relpath(root, base_dir)
                    depth = len(Path(rel_path).parts)
                    if depth > max_depth:
                        dirs.clear()
                except ValueError:
                    # os.path.relpath 在跨驱动器时会抛出 ValueError
                    dirs.clear()

        except PermissionError:
            pass
        except OSError:
            pass

        return None

    # ------------------------------------------------------------------ #
    #  工具方法
    # ------------------------------------------------------------------ #

    def get_available_drives(self) -> List[str]:
        """获取所有可用的驱动器盘符。"""
        drives: List[str] = []
        for drive_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                drives.append(drive_path)
        return drives

    def check_file_in_dir(self, directory: str) -> bool:
        """检查目录下（及其子目录）是否存在目标文件。"""
        # 简单检查当前目录
        potential = os.path.join(directory, self.target_exe)
        if os.path.exists(potential):
            self.found_path = potential
            return True

        # 带深度的递归检查
        try:
            for root, _, files in os.walk(directory):
                if self.target_exe in files:
                    self.found_path = os.path.join(root, self.target_exe)
                    return True
        except (PermissionError, OSError):
            pass

        return False

    def launch_game(self) -> bool:
        """以管理员权限启动找到的目标程序。"""
        if not self.found_path:
            return False

        self.log(f"准备启动: {self.found_path}")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(self.found_path), None, None, 1
            )
            return True
        except OSError as e:
            self.log(f"启动失败: {e}")
            return False

    def save_scan_log(self) -> None:
        """保存扫描日志到文件。"""
        try:
            log_file = "scan_log.txt"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"=== 扫描日志 ({datetime.datetime.now()}) ===\n")
                f.write(f"目标: {self.target_name} ({self.target_exe})\n")
                f.write(f"结果: {'成功' if self.found_path else '失败'}\n")
                if self.found_path:
                    f.write(f"路径: {self.found_path}\n")
                f.write("\n=== 详细记录 ===\n")
                f.write("\n".join(self.logs))
        except OSError as e:
            print(f"写入日志失败: {e}")

    def stop(self) -> None:
        """停止所有扫描。"""
        self.stop_flag = True
        self._found_event.set()  # 同时触发事件，确保所有 worker 退出
