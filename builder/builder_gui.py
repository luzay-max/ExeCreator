# -*- coding: utf-8 -*-
"""
PrankLauncherBuilder - 恶搞启动器生成工具
主界面模块 - 提供可视化配置界面

优化版本 v2.0:
- 支持延迟加载，减少启动时间
- 统一的错误处理
- 模块化的代码结构
- 更好的用户体验
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import shutil
import subprocess
import threading
import re
import logging

# 设置日志
logger = logging.getLogger(__name__)

# ============ 版本信息 ============
VERSION = "2.0.0"
APP_NAME = "PrankLauncherBuilder"


class BuildProgressDialog:
    """打包进度对话框"""
    
    def __init__(self, parent, total_steps=8):
        self.parent = parent
        self.total_steps = total_steps
        self.current_step = 0
        self.log_messages = []
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("打包进度")
        self.dialog.geometry("600x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 450) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            orient=tk.HORIZONTAL,
            length=550,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=20, padx=25)
        
        # 状态标签
        self.status_label = ttk.Label(
            self.dialog,
            text="准备中...",
            font=("Microsoft YaHei", 10)
        )
        self.status_label.pack(pady=5)
        
        # 步骤列表
        self.steps_frame = ttk.Frame(self.dialog)
        self.steps_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)
        
        self.step_labels = []
        for i, step_name in enumerate([
            "初始化环境",
            "收集依赖",
            "生成配置",
            "合并代码",
            "执行打包",
            "文件膨胀",
            "清理临时文件",
            "完成"
        ][:total_steps]):
            label = ttk.Label(
                self.steps_frame,
                text=f"○ {step_name}",
                font=("Microsoft YaHei", 9),
                foreground='gray'
            )
            label.pack(anchor="w", pady=2)
            self.step_labels.append(label)
        
        # 日志区域
        self.log_text = tk.Text(
            self.dialog,
            height=8,
            width=70,
            font=("Consolas", 8),
            state='disabled',
            background='#f0f0f0'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 10))
        
        # 取消按钮
        self.cancel_btn = ttk.Button(
            self.dialog,
            text="取消",
            command=self.cancel
        )
        self.cancel_btn.pack(pady=10, padx=25, anchor="e")
        
        self.cancelled = False
        self.completed = False
    
    def update_step(self, step_num, status_text, logs=None):
        """更新步骤"""
        self.current_step = step_num
        
        # 更新进度条
        progress = (step_num / self.total_steps) * 100
        self.progress_var.set(progress)
        
        # 更新状态标签
        if step_num < self.total_steps:
            self.status_label.config(text=f"步骤 {step_num}/{self.total_steps}: {status_text}")
        
        # 更新步骤列表显示
        for i, label in enumerate(self.step_labels):
            if i < step_num:
                label.config(text=f"✓ {label.cget('text')[2:]}", foreground='green')
            elif i == step_num:
                label.config(text=f"● {label.cget('text')[2:]}", foreground='blue')
        
        # 更新日志
        if logs:
            self.log_text.config(state='normal')
            for log in logs:
                self.log_text.insert('end', log + "\n")
            self.log_text.see('end')
            self.log_text.config(state='disabled')
        
        self.dialog.update()
    
    def add_log(self, message):
        """添加日志"""
        self.log_messages.append(message)
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.dialog.update()
    
    def cancel(self):
        """取消打包"""
        self.cancelled = True
        self.dialog.destroy()
    
    def success(self, output_path):
        """打包成功"""
        self.completed = True
        self.progress_var.set(100)
        self.status_label.config(text="打包完成！", foreground='green')
        
        # 更新所有步骤为完成状态
        for label in self.step_labels:
            label.config(text="✓ " + label.cget('text')[2:], foreground='green')
        
        self.cancel_btn.config(text="关闭")
        
        # 延迟关闭并显示成功消息
        self.dialog.after(1500, lambda: self._show_success_message(output_path))
    
    def _show_success_message(self, output_path):
        self.dialog.destroy()
        messagebox.showinfo(
            "成功",
            f"打包成功！\n\n"
            f"输出文件: {output_path}\n\n"
            f"点击确定打开输出目录",
            parent=self.parent
        )
        # 打开输出目录
        try:
            subprocess.run(f'explorer /select,"{output_path}"', shell=True)
        except:
            pass
    
    def error(self, error_message):
        """打包失败"""
        self.progress_var.set(0)
        self.status_label.config(text="打包失败！", foreground='red')
        self.cancel_btn.config(text="关闭")
        messagebox.showerror("打包失败", error_message, parent=self.dialog)


class BuilderGUI:
    """
    恶搞启动器生成工具主界面
    
    提供可视化配置界面，用于配置并一键生成恶搞 exe
    """
    
    def __init__(self):
        # 延迟导入重型模块（可选优化）
        self._imports_loaded = False
        
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title(f"恶搞启动器生成工具 v{VERSION}")
        self.root.geometry("650x850")
        self.root.minsize(650, 850)
        self.root.resizable(True, True)
        
        # 设置窗口图标
        self._setup_icon()
        
        # 初始化界面
        self._setup_ui()
        
        # 初始化日志
        self._setup_logger()
        
        logger.info(f"{APP_NAME} v{VERSION} 已启动")
    
    def _setup_icon(self):
        """设置窗口图标"""
        try:
            # 尝试从 assets 目录加载图标
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets', 'app_icon.ico'
            )
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # 静默失败，使用默认图标
    
    def _setup_logger(self):
        """初始化日志"""
        # 创建日志文件
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'builder_{int(__import__("time").time())}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _setup_ui(self):
        """设置UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="恶搞启动器生成工具",
            font=("Microsoft YaHei", 18, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # 副标题
        subtitle_label = ttk.Label(
            main_frame,
            text=f"版本 {VERSION} | Prank Launcher Builder",
            font=("Microsoft YaHei", 9),
            foreground='gray'
        )
        subtitle_label.pack(pady=(0, 15))
        
        # 分隔线
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # ============ 目标程序设置 ============
        self._create_section(main_frame, "目标程序设置", 0)
        
        self.target_exe = self._create_entry(main_frame, "目标进程名 (如 YuanShen.exe):", "YuanShen.exe")
        self.target_name = self._create_entry(main_frame, "程序描述 (如 原神):", "原神")
        self.fallback_url = self._create_entry(main_frame, "失败跳转网址:", "https://ys.mihoyo.com")
        self.error_message = self._create_entry(main_frame, "伪造报错内容 (空则不弹窗):", 
                                               "无法定位程序输入点于动态链接库 Kernel32.dll。")
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # ============ 伪装设置 ============
        self._create_section(main_frame, "伪装设置", 1)
        
        self.output_name = self._create_entry(main_frame, "生成文件名 (如 game.exe):", "植物大战僵尸3.exe")
        self.window_title = self._create_entry(main_frame, "伪装窗口标题:", "正在加载游戏资源...")
        
        # 图标选择
        icon_frame = ttk.Frame(main_frame)
        icon_frame.pack(fill='x', pady=5)
        ttk.Label(icon_frame, text="图标文件 (.ico):", width=20).pack(side='left')
        self.icon_path_var = tk.StringVar()
        ttk.Entry(icon_frame, textvariable=self.icon_path_var).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(icon_frame, text="浏览...", command=self._browse_icon).pack(side='left')
        
        # 文件膨胀
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(fill='x', pady=5)
        ttk.Label(size_frame, text="目标文件大小 (MB):", width=20).pack(side='left')
        self.target_size_var = tk.StringVar(value="10")
        ttk.Entry(size_frame, textvariable=self.target_size_var, width=10).pack(side='left', padx=5)
        ttk.Label(size_frame, text="(0 表示不膨胀)").pack(side='left')
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # ============ 元数据伪装 (高级) ============
        self._create_section(main_frame, "元数据伪装 (高级)", 2)
        
        self.meta_company = self._create_entry(main_frame, "公司名称:", "Microsoft Corporation")
        self.meta_desc = self._create_entry(main_frame, "文件描述:", "Game Client")
        self.meta_copyright = self._create_entry(
            main_frame, "版权信息:", "© Microsoft Corporation. All rights reserved.")
        self.meta_version = self._create_entry(main_frame, "版本号 (X.X.X.X):", "1.0.0.1")
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        # ============ 操作区 ============
        self.log_text = tk.Text(main_frame, height=10, state='disabled', 
                                 font=("Consolas", 9), background='#f5f5f5')
        self.log_text.pack(fill='x', pady=(0, 10))
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=10)
        
        self.build_btn = ttk.Button(
            btn_frame, 
            text="🚀 开始生成", 
            command=self._start_build_thread
        )
        self.build_btn.pack(fill='x', ipady=8)
        
        # 说明标签
        info_label = ttk.Label(
            main_frame,
            text="提示: 打包过程可能需要 1-5 分钟，请耐心等待",
            font=("Microsoft YaHei", 8),
            foreground='gray'
        )
        info_label.pack(pady=5)
    
    def _create_section(self, parent, title, section_id):
        """创建区域标题"""
        frame = ttk.LabelFrame(parent, text=title, padding="10")
        frame.pack(fill='x', pady=5)
        return frame
    
    def _create_entry(self, parent, label_text, default_value, **kwargs):
        """创建标签-输入框组合"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=3)
        ttk.Label(frame, text=label_text, width=22).pack(side='left')
        entry = ttk.Entry(frame, **kwargs)
        entry.insert(0, default_value)
        entry.pack(side='left', fill='x', expand=True)
        return entry
    
    def _browse_icon(self):
        """浏览图标文件"""
        path = filedialog.askopenfilename(
            filetypes=[("Icon Files", "*.ico"), ("All Files", "*.*")]
        )
        if path:
            self.icon_path_var.set(path)
            self._log(f"已选择图标: {path}")
    
    def _log(self, message):
        """记录日志"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update()
        logger.info(message)
    
    def _start_build_thread(self):
        """启动打包线程"""
        self.build_btn.config(state='disabled')
        t = threading.Thread(target=self._build_process, daemon=True)
        t.start()
    
    def _validate_inputs(self) -> bool:
        """验证输入"""
        # 验证版本号格式
        version = self.meta_version.get().strip()
        if not re.match(r'^\d+\.\d+\.\d+\.\d+$', version):
            messagebox.showerror("输入错误", "版本号格式无效！\n应为 X.X.X.X 格式（如 1.0.0.1）")
            return False
        
        # 验证输出文件名
        output_name = self.output_name.get().strip()
        if not output_name:
            messagebox.showerror("输入错误", "输出文件名不能为空！")
            return False
        
        if not output_name.endswith('.exe'):
            output_name += '.exe'
            self.output_name.delete(0, tk.END)
            self.output_name.insert(0, output_name)
        
        return True
    
    def _get_project_paths(self):
        """获取项目路径"""
        if getattr(sys, 'frozen', False):
            # 打包环境
            base_path = sys._MEIPASS
            
            # 检查 _MEIPASS 目录是否存在
            if not os.path.exists(base_path):
                # 尝试使用 exe 所在目录
                base_path = os.path.dirname(sys.executable)
            
            template_dir = os.path.join(base_path, "template")
            
            # 如果模板目录不在 _MEIPASS 中，尝试在 exe 同级目录查找
            if not os.path.exists(template_dir):
                exe_dir = os.path.dirname(sys.executable)
                template_dir = os.path.join(exe_dir, "template")
                base_path = exe_dir
            
            return base_path, template_dir
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_path, "template")
            return base_path, template_dir
    
    def _read_template_file(self, filename: str, template_dir: str) -> str:
        """读取模板文件"""
        filepath = os.path.join(template_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"模板文件不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _build_process(self):
        """打包主流程"""
        try:
            # 验证输入
            if not self._validate_inputs():
                self.build_btn.config(state='normal')
                return
            
            self._log("=" * 50)
            self._log("开始构建恶搞启动器...")
            self._log("=" * 50)
            
            # 收集参数
            config = {
                "target_exe": self.target_exe.get().strip(),
                "target_name": self.target_name.get().strip(),
                "fallback_url": self.fallback_url.get().strip(),
                "window_title": self.window_title.get().strip(),
                "error_message": self.error_message.get().strip(),
                "show_log": True
            }
            
            output_name = self.output_name.get().strip()
            if not output_name.endswith(".exe"):
                output_name += ".exe"
            
            icon_path = self.icon_path_var.get().strip()
            target_size_mb = float(self.target_size_var.get())
            
            self._log(f"目标程序: {config['target_exe']} ({config['target_name']})")
            self._log(f"输出文件: {output_name}")
            
            # 获取路径
            base_path, template_dir = self._get_project_paths()
            
            # 检查模板目录
            if not os.path.exists(template_dir):
                raise FileNotFoundError(f"找不到模板目录: {template_dir}")
            
            # 创建构建目录
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
            
            # 读取模板文件
            fake_ui_code = self._read_template_file("fake_ui.py", template_dir)
            launcher_core_code = self._read_template_file("launcher_core.py", template_dir)
            boot_code = self._read_template_file("boot.py", template_dir)
            
            # 移除测试代码
            if 'if __name__ == "__main__":' in fake_ui_code:
                fake_ui_code = fake_ui_code.split('if __name__ == "__main__":')[0]
            
            # 注入配置
            config_str = "CONFIG = " + repr(config)
            boot_code = re.sub(
                r"# --- CONFIG START ---.*# --- CONFIG END ---",
                f"# --- CONFIG START ---\n{config_str}\n# --- CONFIG END ---",
                boot_code,
                flags=re.DOTALL
            )
            
            # 移除本地导入
            boot_code = re.sub(
                r"# --- IMPORTS START ---.*# --- IMPORTS END ---", 
                "", 
                boot_code, 
                flags=re.DOTALL
            )
            
            # 合并代码
            final_code = f"""
# === MERGED BUILD ===
import os
import sys
import threading
import time
import webbrowser
import winreg
import ctypes
import tkinter as tk
from tkinter import ttk
import random
from pathlib import Path

# --- Module: launcher_core ---
{launcher_core_code}

# --- Module: fake_ui ---
{fake_ui_code}

# --- Module: boot ---
{boot_code}
"""
            
            # 写入合并后的 boot.py
            boot_file = os.path.join(build_dir, "boot.py")
            with open(boot_file, "w", encoding="utf-8") as f:
                f.write(final_code)
            
            self._log("代码合并完成")
            
            # ============ 生成版本信息 ============
            version_file_path = None
            try:
                version_str = self.meta_version.get().strip()
                if not re.match(r'^\d+\.\d+\.\d+\.\d+$', version_str):
                    version_str = "1.0.0.0"
                
                version_tuple = tuple(map(int, version_str.split('.')))
                
                # 读取版本模板
                ver_template = self._read_template_file("version_info_template.txt", template_dir)
                
                ver_content = ver_template.format(
                    file_version_tuple=version_tuple,
                    product_version_tuple=version_tuple,
                    company_name=self.meta_company.get().strip(),
                    file_description=self.meta_desc.get().strip(),
                    file_version=version_str,
                    internal_name=output_name,
                    copyright=self.meta_copyright.get().strip(),
                    original_filename=output_name,
                    product_name=self.meta_desc.get().strip(),
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
            
            # 检查 PyInstaller
            try:
                subprocess.run(
                    ["pyinstaller", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                pyinstaller_cmd = ["pyinstaller"]
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 尝试本地 Python
                local_py = os.path.join(current_work_dir, "python_embedded", "python.exe")
                local_pyinstaller = os.path.join(
                    current_work_dir, "python_embedded", "Scripts", "pyinstaller.exe"
                )
                
                if os.path.exists(local_py) and os.path.exists(local_pyinstaller):
                    self._log("使用本地嵌入式 Python 环境...")
                    pyinstaller_cmd = [local_py, "-m", "PyInstaller"]
                else:
                    raise RuntimeError(
                        "未检测到 PyInstaller！\n"
                        "请安装 Python 和 PyInstaller，或者将本程序放在包含 python_embedded 的便携包中运行。"
                    )
            
            # 构建命令
            cmd = pyinstaller_cmd + [
                "--onefile",
                "--clean",
                "--noconsole",
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
            
            # 执行打包
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                cmd,
                cwd=build_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )
            
            # 实时输出
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
                self._inflate_file(exe_path, target_size_mb)
            
            # ============ 清理 ============
            self._log("清理临时文件...")
            try:
                shutil.rmtree(build_dir)
            except:
                pass
            
            self._log("=" * 50)
            self._log("🎉 全部完成！")
            self._log("=" * 50)
            
            messagebox.showinfo("成功", f"生成成功！\n\n文件路径: {exe_path}")
            
            # 打开输出目录
            try:
                subprocess.run(f'explorer /select,"{exe_path}"', shell=True)
            except:
                pass
            
        except Exception as e:
            error_msg = str(e)
            self._log(f"错误: {error_msg}")
            logger.exception("打包过程发生错误")
            messagebox.showerror("错误", f"打包失败！\n\n{error_msg}")
        
        finally:
            self.build_btn.config(state='normal')
    
    def _inflate_file(self, file_path: str, target_mb: float):
        """文件膨胀"""
        try:
            current_size = os.path.getsize(file_path)
            target_bytes = int(target_mb * 1024 * 1024)
            
            if current_size >= target_bytes:
                self._log("当前文件已超过目标大小，跳过膨胀")
                return
            
            needed_bytes = target_bytes - current_size
            self._log(f"需要填充: {needed_bytes / 1024 / 1024:.2f} MB")
            
            with open(file_path, "ab") as f:
                chunk_size = 1024 * 1024  # 1MB
                written = 0
                
                while needed_bytes > 0:
                    write_size = min(chunk_size, needed_bytes)
                    f.write(b'\0' * write_size)
                    needed_bytes -= write_size
                    written += write_size
            
            self._log("文件膨胀完成")
            
        except Exception as e:
            self._log(f"文件膨胀失败: {e}")
    
    def mainloop(self):
        """运行主界面"""
        self.root.mainloop()


# ============ 启动入口 ============
def main():
    """主入口函数"""
    # 尝试显示启动闪屏
    try:
        import sys
        import os
        
        if getattr(sys, 'frozen', False):
            splash_path = os.path.join(sys._MEIPASS, 'splash_screen.py')
            if os.path.exists(splash_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("splash_screen", splash_path)
                splash_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(splash_module)
                splash_module.run_splash_thread(1200)
    except Exception:
        pass
    
    # 启动主程序
    app = BuilderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
