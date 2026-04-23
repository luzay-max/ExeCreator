# -*- coding: utf-8 -*-
"""
恶搞启动器核心模块 — v3.1 模块化重构版

v3.1 改进：
- 扫描逻辑拆分到 scanner/ 子包（CacheScanner、RegistryScanner、DriveScanner）。
- GameScanner 作为编排层，按优先级调度各子扫描器。
- SelfUpdater / PathCache 保持不变。
"""
import atexit
import ctypes
import datetime
import json
import os
import sys
from typing import Callable, List, Optional, Set

# ======================================================================= #
#  在合并打包时，scanner/ 子包的代码会被内联到此文件中。
#  开发环境下使用相对导入。
# ======================================================================= #
try:
    from scanner import CacheScanner, DriveScanner, RegistryScanner
except ImportError:
    # 合并打包后这些类已经在同一文件中，无需导入
    pass


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


class GameScanner:
    """
    游戏/程序扫描器 — 编排层。

    v3.1 改进：
    - 扫描逻辑委托给 scanner/ 子包中的模块化扫描器。
    - GameScanner 仅负责按优先级调度、汇总结果，以及管理自更新。
    """

    def __init__(self, target_exe: str, target_name: str) -> None:
        self.target_exe: str = target_exe
        self.target_name: str = target_name
        self.found_path: Optional[str] = None
        self.stop_flag: bool = False
        self.log_callback: Optional[Callable[[str], None]] = None
        self.logs: List[str] = []

        # 初始化自我更新器
        self.self_updater: SelfUpdater = SelfUpdater()
        self.self_updater.load()

        # 初始化子扫描器
        self._cache_scanner = CacheScanner(
            target_exe, target_name,
            known_paths=self.self_updater.known_paths
        )
        self._registry_scanner = RegistryScanner(target_exe, target_name)
        self._drive_scanner = DriveScanner(target_exe, target_name)

        self._all_scanners = [
            self._cache_scanner,
            self._registry_scanner,
            self._drive_scanner,
        ]

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self.log_callback = callback
        for s in self._all_scanners:
            s.set_log_callback(callback)

    def log(self, message: str) -> None:
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

        扫描顺序：缓存/自身数据 → 注册表 → 常用路径 → 全盘扫描
        """
        self.log(f"开始寻找 {self.target_name} ({self.target_exe})...")

        # 1. 缓存 + 自身嵌入数据（最快）
        result = self._cache_scanner.scan()
        if result:
            self.found_path = str(result)
            return str(result)

        # 2. 注册表
        result = self._registry_scanner.scan()
        if result:
            self.found_path = str(result)
            self._update_cache()
            return str(result)

        # 3. 常用路径 + 全盘扫描（最慢）
        result = self._drive_scanner.scan()
        if result:
            self.found_path = str(result)
            self._update_cache()
            return str(result)

        return None

    def _update_cache(self) -> None:
        if self.found_path:
            self.log(f"更新本地缓存: {self.found_path}")
            self._cache_scanner.update_cache(self.found_path)
            self.self_updater.update([self.found_path])

    # ------------------------------------------------------------------ #
    #  启动 & 日志 & 停止
    # ------------------------------------------------------------------ #

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
        # 合并子扫描器的日志
        all_logs = list(self.logs)
        for s in self._all_scanners:
            all_logs.extend(s.logs)

        try:
            log_file = "scan_log.txt"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"=== 扫描日志 ({datetime.datetime.now()}) ===\n")
                f.write(f"目标: {self.target_name} ({self.target_exe})\n")
                f.write(f"结果: {'成功' if self.found_path else '失败'}\n")
                if self.found_path:
                    f.write(f"路径: {self.found_path}\n")
                f.write("\n=== 详细记录 ===\n")
                f.write("\n".join(all_logs))
        except OSError as e:
            print(f"写入日志失败: {e}")

    def stop(self) -> None:
        """停止所有扫描。"""
        self.stop_flag = True
        for s in self._all_scanners:
            s.stop()
