# -*- coding: utf-8 -*-
"""
驱动器扫描器 — 包含常用路径扫描和全盘深度扫描两种策略。

v3.0: 使用 ThreadPoolExecutor 并发扫描，threading.Event 实现 "一处发现，全盘停止"。
"""
import os
import concurrent.futures
from pathlib import Path
from typing import Optional, List
from .base_scanner import BaseScanner


class DriveScanner(BaseScanner):

    # ------------------------------------------------------------------ #
    #  策略 A：常用路径快速扫描
    # ------------------------------------------------------------------ #

    def scan(self) -> Optional[str]:
        """依次执行常用路径扫描和全盘扫描。"""
        result = self.scan_common_paths()
        if result:
            return result
        return self.scan_drives()

    def scan_common_paths(self) -> Optional[str]:
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

        common_dirs = list({d for d in common_dirs if d and os.path.exists(d)})
        if not common_dirs:
            return None

        self._found_event.clear()
        max_workers = min(len(common_dirs), 8)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_directory, d, max_depth=4): d
                for d in common_dirs
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        self.log(f"在常用路径中发现: {result}")
                        with self._lock:
                            if not self.found_path:
                                self.found_path = result
                        for f in futures:
                            f.cancel()
                        return result
                except (PermissionError, OSError):
                    pass
        return None

    # ------------------------------------------------------------------ #
    #  策略 B：全盘深度扫描
    # ------------------------------------------------------------------ #

    def scan_drives(self) -> Optional[str]:
        """并发扫描所有驱动器（每个驱动器一个线程）。"""
        self.log("开始全盘深度扫描...")
        drives = self.get_available_drives()
        if not drives:
            return None

        self._found_event.clear()
        max_workers = len(drives)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_single_drive, drive): drive
                for drive in drives
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        self.log(f"全盘扫描发现: {result}")
                        with self._lock:
                            if not self.found_path:
                                self.found_path = result
                        for f in futures:
                            f.cancel()
                        return result
                except (PermissionError, OSError):
                    pass
        return None

    # ------------------------------------------------------------------ #
    #  内部 Worker 方法
    # ------------------------------------------------------------------ #

    def _scan_single_drive(self, drive: str) -> Optional[str]:
        self.log(f"正在扫描驱动器 {drive} ...")
        try:
            for root, dirs, files in os.walk(drive):
                if self.stop_flag or self._found_event.is_set():
                    return None

                current_dir_name = os.path.basename(root).lower()
                if current_dir_name in self.blacklist_dirs:
                    dirs.clear()
                    continue

                for i in range(len(dirs) - 1, -1, -1):
                    if dirs[i].lower() in self.blacklist_dirs:
                        del dirs[i]

                if self.target_exe in files:
                    full_path = os.path.join(root, self.target_exe)
                    self._found_event.set()
                    return full_path
        except PermissionError:
            pass
        except OSError as e:
            self.log(f"扫描驱动器 {drive} 时出错: {e}")
        return None

    def _scan_directory(self, base_dir: str, max_depth: int = 4) -> Optional[str]:
        try:
            for root, dirs, files in os.walk(base_dir):
                if self.stop_flag or self._found_event.is_set():
                    return None

                if self.target_exe in files:
                    full_path = os.path.join(root, self.target_exe)
                    self._found_event.set()
                    return full_path

                try:
                    rel_path = os.path.relpath(root, base_dir)
                    depth = len(Path(rel_path).parts)
                    if depth > max_depth:
                        dirs.clear()
                except ValueError:
                    dirs.clear()
        except PermissionError:
            pass
        except OSError:
            pass
        return None
