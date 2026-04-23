# -*- coding: utf-8 -*-
"""
注册表扫描器 — 从 Windows 注册表的 Uninstall 键中查找目标程序的安装路径。
"""
import winreg
from typing import Optional

from .base_scanner import BaseScanner


class RegistryScanner(BaseScanner):

    def scan(self) -> Optional[str]:
        self.log("正在扫描系统注册表...")
        registry_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hkey_root, reg_path in registry_roots:
            if self.stop_flag or self._found_event.is_set():
                return None
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
                                            if install_loc and self.check_file_in_dir(install_loc):
                                                return self.found_path
                                        except OSError:
                                            pass
                                except OSError:
                                    pass
                        except OSError:
                            continue
            except OSError:
                continue
        return None
