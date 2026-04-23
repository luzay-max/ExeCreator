# -*- coding: utf-8 -*-
"""
扫描器基类 — 提供统一的接口和公用工具方法。

所有具体扫描器（注册表、驱动器、缓存等）均继承此类。
"""
import datetime
import os
import threading
from typing import Callable, List, Optional, Set


class BaseScanner:
    """扫描器抽象基类。"""

    def __init__(self, target_exe: str, target_name: str) -> None:
        self.target_exe: str = target_exe
        self.target_name: str = target_name
        self.found_path: Optional[str] = None
        self.stop_flag: bool = False
        self.log_callback: Optional[Callable[[str], None]] = None
        self.logs: List[str] = []

        # 并发扫描用的全局"已找到"事件 & 写入锁
        self._found_event: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()

        # 扫描黑名单（小写，用于忽略系统目录）
        self.blacklist_dirs: Set[str] = {
            'windows', 'programdata', 'system volume information',
            '$recycle.bin', 'msocache', 'config.msi', 'recovery',
            'documents and settings', 'perflogs', 'boot',
            'common files', 'internet explorer', 'windows defender',
            'microsoft.net'
        }

    # ------------------------------------------------------------------ #
    #  公用工具
    # ------------------------------------------------------------------ #

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self.log_callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def stop(self) -> None:
        self.stop_flag = True
        self._found_event.set()

    def get_available_drives(self) -> List[str]:
        drives: List[str] = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives

    def check_file_in_dir(self, directory: str) -> bool:
        potential = os.path.join(directory, self.target_exe)
        if os.path.exists(potential):
            self.found_path = potential
            return True
        try:
            for root, _, files in os.walk(directory):
                if self.target_exe in files:
                    self.found_path = os.path.join(root, self.target_exe)
                    return True
        except (PermissionError, OSError):
            pass
        return False

    # ------------------------------------------------------------------ #
    #  子类需实现的接口
    # ------------------------------------------------------------------ #

    def scan(self) -> Optional[str]:
        """执行扫描，返回找到的路径或 None。子类必须覆写。"""
        raise NotImplementedError
