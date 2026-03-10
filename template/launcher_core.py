import os
import winreg
import ctypes
import sys
import threading
import time
import json
import datetime
import subprocess
from pathlib import Path

class SelfUpdater:
    MARKER = b'<<PROPAGATION_DATA>>'
    
    def __init__(self):
        self.exe_path = sys.executable
        self.original_data = None
        self.known_paths = []
        self.loaded = False
        
    def load(self):
        # 仅在打包环境下工作
        if not getattr(sys, 'frozen', False):
            return
            
        try:
            # 读取自身文件
            with open(self.exe_path, 'rb') as f:
                content = f.read()
                
            # 查找标记
            parts = content.split(self.MARKER)
            
            # 第一部分被认为是原始数据（或者已经包含了一些数据的原始数据）
            # 这里我们假设文件结构总是 [Original_EXE] + [MARKER] + [JSON]
            # 如果多次追加，可能会有多个 MARKER，我们取最后一个有效数据？
            # 不，为了保持清洁，我们总是取第一个 MARKER 之前的内容作为 Base
            self.original_data = parts[0]
            
            if len(parts) > 1:
                # 尝试解析最后一部分的数据
                try:
                    last_part = parts[-1]
                    # 有可能后面跟了 null bytes 或者其他东西，尝试清理
                    json_str = last_part.decode('utf-8', errors='ignore').strip().strip('\0')
                    if json_str:
                        data = json.loads(json_str)
                        if isinstance(data, list):
                            self.known_paths = data
                except:
                    pass
            
            self.loaded = True
        except Exception as e:
            print(f"Update load failed: {e}")

    def update(self, new_paths):
        """计划在退出时更新自身"""
        if not self.loaded or not self.original_data:
            return
            
        # 合并路径
        current_set = set(self.known_paths)
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
            
            tmp_exe = self.exe_path + ".tmp"
            with open(tmp_exe, 'wb') as f:
                f.write(new_content)
                
            # 创建更新脚本
            bat_path = os.path.join(os.path.dirname(self.exe_path), "update_self.bat")
            exe_name = os.path.basename(self.exe_path)
            
            # 批处理脚本：等待 -> 删除原文件 -> 移动新文件 -> 删除脚本
            bat_content = f"""
@echo off
ping 127.0.0.1 -n 2 > nul
:try_delete
del "{exe_name}"
if exist "{exe_name}" goto try_delete
move "{exe_name}.tmp" "{exe_name}"
del "%~f0"
"""
            with open(bat_path, 'w') as f:
                f.write(bat_content)
                
            # 启动隐藏的更新进程
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.Popen(
                bat_path, 
                shell=True, 
                cwd=os.path.dirname(self.exe_path),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
            )
            
        except Exception as e:
            print(f"Update prepare failed: {e}")

class PathCache:
    """管理本地路径缓存，实现'一次找到，永久秒开'"""
    def __init__(self):
        # 在用户 LocalAppData 下建立隐蔽的缓存目录
        self.cache_dir = os.path.join(os.environ.get("LOCALAPPDATA", "."), "FakeLauncherCache")
        self.cache_file = os.path.join(self.cache_dir, "known_paths.json")
        self._ensure_dir()
        self.cache = self._load_cache()

    def _ensure_dir(self):
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except:
                pass

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def get_path(self, exe_name):
        path = self.cache.get(exe_name.lower())
        if path and os.path.exists(path):
            return path
        return None

    def update_path(self, exe_name, path):
        self.cache[exe_name.lower()] = path
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except:
            pass

class GameScanner:
    def __init__(self, target_exe, target_name):
        self.target_exe = target_exe
        self.target_name = target_name
        self.found_path = None
        self.stop_flag = False
        self.log_callback = None
        self.logs = [] # 存储日志记录
        self.cache = PathCache()
        
        # 初始化自我更新器
        self.self_updater = SelfUpdater()
        self.self_updater.load() # 尝试读取自身携带的数据
        
        # 扫描黑名单（小写，用于忽略系统目录）
        self.blacklist_dirs = {
            'windows', 'programdata', 'system volume information', 
            '$recycle.bin', 'msocache', 'config.msi', 'recovery',
            'documents and settings', 'perflogs', 'boot',
            'common files', 'internet explorer', 'windows defender',
            'microsoft.net'
        }

    def set_log_callback(self, callback):
        """设置日志回调函数 func(message)"""
        self.log_callback = callback

    def log(self, message):
        # 添加时间戳并保存到内存
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def scan(self):
        """开始扫描"""
        self.log(f"开始寻找 {self.target_name} ({self.target_exe})...")
        
        # 0. 优先检查本地缓存 (最高优先级)
        if self.scan_cache():
            return self.found_path

        # 0.5 检查自身携带的数据 (自我繁殖数据)
        if self.scan_self_data():
            self._update_cache() # 同步到本地缓存
            return self.found_path

        # 1. 扫描注册表
        if self.scan_registry():
            self._update_cache()
            return self.found_path
            
        # 2. 扫描常用路径 (Program Files)
        if self.scan_common_paths():
            self._update_cache()
            return self.found_path

        # 3. 全盘扫描
        if self.scan_drives():
            self._update_cache()
            return self.found_path
            
        return None

    def _update_cache(self):
        if self.found_path:
            self.log(f"更新本地缓存: {self.found_path}")
            self.cache.update_path(self.target_exe, self.found_path)
            
            # 触发自我更新机制
            self.self_updater.update([self.found_path])

    def scan_cache(self):
        self.log("检查本地缓存记录...")
        cached_path = self.cache.get_path(self.target_exe)
        if cached_path:
            self.log(f"在缓存中快速定位到: {cached_path}")
            self.found_path = cached_path
            return True
        return False

    def scan_self_data(self):
        """检查 EXE 自身携带的数据"""
        if not self.self_updater.known_paths:
            return False
            
        self.log(f"检查自身携带的 {len(self.self_updater.known_paths)} 条记录...")
        for path in self.self_updater.known_paths:
            # 简单检查路径是否包含目标 exe 或者是目录
            check_path = path
            if not path.lower().endswith(self.target_exe.lower()):
                check_path = os.path.join(path, self.target_exe)
            
            if os.path.exists(check_path) and os.path.isfile(check_path):
                 self.log(f"在自身记录中发现: {check_path}")
                 self.found_path = check_path
                 return True
        return False

    def scan_registry(self):
        self.log("正在扫描系统注册表...")
        # 扫描 HKLM 和 HKCU
        registry_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey_root, reg_path in registry_roots:
            if self.stop_flag: return False
            try:
                with winreg.OpenKey(hkey_root, reg_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                # 检查 DisplayName
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    if self.target_name.lower() in str(display_name).lower(): # 忽略大小写
                                        self.log(f"在注册表中发现疑似项: {display_name}")
                                        # 检查 InstallLocation
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

    def scan_common_paths(self):
        self.log("扫描常用安装目录...")
        user_home = os.environ.get("USERPROFILE")
        local_appdata = os.environ.get("LOCALAPPDATA")
        roaming_appdata = os.environ.get("APPDATA")
        
        common_dirs = [
            # 常见软件安装目录
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            # 用户目录 (很多现代软件安装在这里)
            local_appdata, # C:\Users\xxx\AppData\Local
            roaming_appdata, # C:\Users\xxx\AppData\Roaming
            os.path.join(local_appdata, "Programs") if local_appdata else None,
            # 桌面和下载 (便携版软件)
            os.path.join(user_home, "Desktop") if user_home else None,
            os.path.join(user_home, "Downloads") if user_home else None,
        ]

        # 其他盘符的游戏目录
        drives = self.get_available_drives()
        for drive in drives:
            # 跳过 C 盘，因为上面已经处理过系统盘的特定目录
            if drive.lower().startswith("c:"):
                continue
                
            # 在每个盘符下查找常见目录
            potential_dirs = [
                os.path.join(drive, "Program Files"),
                os.path.join(drive, "Program Files (x86)"),
                os.path.join(drive, "Games"),
                os.path.join(drive, "Game"),
                os.path.join(drive, "Software"),
                # 还有根目录本身，但根目录不适合深度递归，只适合检查第一层
                # 这里我们不把根目录加进去 os.walk，而是在下面单独检查
            ]
            common_dirs.extend(potential_dirs)

        # 去重并过滤空值
        common_dirs = list(set([d for d in common_dirs if d and os.path.exists(d)]))
        
        for base_dir in common_dirs:
            if self.stop_flag: return False
            self.log(f"扫描目录: {base_dir}")
            try:
                # 限制 os.walk 的深度，避免在 AppData 这种大目录陷进去太久
                # 这里我们只做浅层扫描或者特定策略扫描
                # 为了效率，我们对 AppData 这种大目录使用更激进的过滤
                for root, dirs, files in os.walk(base_dir):
                    if self.stop_flag: return False
                    
                    # 检查当前目录的文件
                    if self.target_exe in files:
                        full_path = os.path.join(root, self.target_exe)
                        self.found_path = full_path
                        return True
                        
                    # 优化：如果是 AppData，不要遍历太深，除非目录名看起来像目标
                    # 简单的启发式：如果目录层级超过 base_dir 3层，就停止深入
                    # 计算相对深度
                    try:
                        rel_path = os.path.relpath(root, base_dir)
                        depth = len(Path(rel_path).parts)
                        if depth > 4: 
                            # 移除所有子目录，停止向下递归
                            del dirs[:]
                    except:
                        pass
            except Exception as e:
                pass # 忽略权限错误
                
        return False

    def scan_drives(self):
        self.log("开始全盘深度扫描...")
        drives = self.get_available_drives()
        for drive in drives:
            if self.stop_flag: return False
            self.log(f"正在扫描驱动器 {drive} ...")
            try:
                for root, dirs, files in os.walk(drive):
                    if self.stop_flag: return False
                    
                    # --- 智能过滤逻辑 START ---
                    # 1. 过滤当前目录名是否在黑名单中
                    current_dir_name = os.path.basename(root).lower()
                    if current_dir_name in self.blacklist_dirs:
                        del dirs[:] # 停止向下递归
                        continue
                        
                    # 2. 预先过滤子目录，避免进入黑名单目录
                    # 使用列表切片原地修改 dirs，这样 os.walk 就不会进入被移除的目录
                    # 注意：我们要保留不在黑名单里的目录
                    # dirs[:] = [d for d in dirs if d.lower() not in self.blacklist_dirs]
                    # 为了性能，反向遍历移除
                    for i in range(len(dirs) - 1, -1, -1):
                        d_name = dirs[i].lower()
                        if d_name in self.blacklist_dirs:
                            del dirs[i]
                    # --- 智能过滤逻辑 END ---
                    
                    if self.target_exe in files:
                        full_path = os.path.join(root, self.target_exe)
                        self.found_path = full_path
                        return True
            except Exception as e:
                self.log(f"扫描驱动器 {drive} 时出错: {e}")
        return False

    def get_available_drives(self):
        drives = []
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if os.path.exists(f"{drive}:\\"):
                drives.append(f"{drive}:\\")
        return drives

    def check_file_in_dir(self, directory):
        """检查目录下(及其子目录)是否存在目标文件"""
        # 简单检查当前目录
        potential = os.path.join(directory, self.target_exe)
        if os.path.exists(potential):
            self.found_path = potential
            return True
        
        # 稍微深一层的检查（例如 Genshin Impact/Genshin Impact Game/YuanShen.exe）
        for root, _, files in os.walk(directory):
            if self.target_exe in files:
                self.found_path = os.path.join(root, self.target_exe)
                return True
        return False

    def launch_game(self):
        if not self.found_path:
            return False
        
        self.log(f"准备启动: {self.found_path}")
        try:
            # 以管理员权限启动
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(self.found_path), None, None, 1
            )
            return True
        except Exception as e:
            self.log(f"启动失败: {e}")
            return False

    def save_scan_log(self):
        """保存日志到文件"""
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
        except Exception as e:
            print(f"写入日志失败: {e}")

    def stop(self):
        self.stop_flag = True
