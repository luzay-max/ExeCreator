# -*- coding: utf-8 -*-
"""
PrankLauncherBuilder - 恶搞启动器生成工具
主界面模块 - v3.0 优化重构版
"""
import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# 确保项目根目录在 sys.path 中（无论从哪里启动都能找到模块）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from builder_core import BuilderCore
from history_manager import HistoryManager
from widgets.config_panel import ConfigPanel
from widgets.log_viewer import LogViewer
try:
    from builder.locale.i18n import t, set_lang, get_current_lang
except ImportError:
    from locale.i18n import t, set_lang, get_current_lang  # type: ignore

try:
    from builder.utils.constants import VERSION, APP_NAME, APP_TITLE, LOG_FORMAT
except ImportError:
    from utils.constants import VERSION, APP_NAME, APP_TITLE, LOG_FORMAT  # type: ignore, VERSION

logger = logging.getLogger(__name__)

class BuilderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("680x900")
        self.root.minsize(650, 850)

        self.history_mgr = HistoryManager()
        self.is_dark_theme = False

        self._setup_icon()
        self._setup_ui()
        self._setup_logger()

        # 加载历史
        cfg = self.history_mgr.load_history()
        self.config_panel.set_config(cfg)

        logger.info(f"{APP_NAME} v{VERSION} 已启动")

    def _setup_icon(self):
        try:
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'assets', 'app_icon.ico'
            )
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def _setup_logger(self):
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'builder_{int(__import__("time").time())}.log')
        logging.basicConfig(level=logging.INFO,
                            format=LOG_FORMAT,
                            handlers=[logging.FileHandler(log_file, encoding='utf-8'),
                                      logging.StreamHandler()])

    def _setup_ui(self):
        # 顶层按钮栏
        top_frame = ttk.Frame(self.root, padding=(20, 10, 20, 0))
        top_frame.pack(fill='x')

        self.lang_btn = ttk.Button(top_frame, text=t("menu_language"), command=self._toggle_lang)
        self.lang_btn.pack(side='right', padx=5)

        self.theme_btn = ttk.Button(top_frame, text=t("theme_dark"), command=self._toggle_theme)
        self.theme_btn.pack(side='right')

        # 主框架装载区
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="恶搞启动器生成工具", font=("Microsoft YaHei", 18, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame, text=f"版本 {VERSION} | Prank Launcher Builder", foreground='gray').pack(pady=(0, 5))

        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=5)

        # 核心组件库 ConfigPanel
        self.config_panel = ConfigPanel(main_frame)

        # 操作区 (先 pack 到底部，确保不会被遮挡)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side='bottom', fill='x', pady=10)

        self.preview_btn = ttk.Button(btn_frame, text="👁 " + t("btn_preview"), command=self._preview_ui)
        self.preview_btn.pack(side='left', padx=5, expand=True, fill='x', ipady=5)

        self.build_btn = ttk.Button(btn_frame, text="🚀 " + t("btn_generate"), command=self._start_build_thread)
        self.build_btn.pack(side='left', padx=5, expand=True, fill='x', ipady=5)

        # 日志查看区 (最后 pack，占用剩余空间)
        self.log_viewer = LogViewer(main_frame)

    def _toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        style = ttk.Style()
        if self.is_dark_theme:
            self.root.configure(bg='#2b2b2b')
            style.theme_use('default')
            style.configure('.', background='#2b2b2b', foreground='white')
            style.configure('TLabel', background='#2b2b2b', foreground='white')
            style.configure('TFrame', background='#2b2b2b')
            style.configure('TLabelframe', background='#2b2b2b', foreground='white')
            style.configure('TLabelframe.Label', background='#2b2b2b')
            self.log_viewer.log_text.config(bg='#1e1e1e', fg='#00ff00')
        else:
            self.root.configure(bg='SystemButtonFace')
            style.theme_use('clam')
            style.configure('.', background='SystemButtonFace', foreground='black')
            style.configure('TLabel', background='SystemButtonFace', foreground='black')
            style.configure('TFrame', background='SystemButtonFace')
            style.configure('TLabelframe', background='SystemButtonFace', foreground='black')
            style.configure('TLabelframe.Label', background='SystemButtonFace')
            self.log_viewer.log_text.config(bg='#f5f5f5', fg='black')
        
        self.theme_btn.config(text=t("theme_light") if self.is_dark_theme else t("theme_dark"))

    def _toggle_lang(self):
        current = get_current_lang()
        new_lang = "en_US" if current == "zh_CN" else "zh_CN"
        set_lang(new_lang)
        # Suggest restart for UI to update fully
        messagebox.showinfo("Language / 语言", "Language changed. Please restart the application for changes to take full effect.\n语言已切换，请重启程序以完全生效。")
        self.lang_btn.config(text=t("menu_language"))
        self.theme_btn.config(text=t("theme_light") if self.is_dark_theme else t("theme_dark"))
        self.preview_btn.config(text="👁 " + t("btn_preview"))
        self.build_btn.config(text="🚀 " + t("btn_generate"))

    def _preview_ui(self):
        """生成界面预览"""
        config = self.config_panel.get_config()
        title = config.get("window_title", "加载中...")
        from template.fake_ui import FakeLoaderUI

        def _mock_close(ui):
            ui.running = False
            ui.root.destroy()

        ui = FakeLoaderUI(title, splash_data=config.get("splash_image_data", ""), parent=self.root)
        ui.close = lambda: _mock_close(ui)
        # 不需要起新线程，Toplevel 属于当前的 Tkinter mainloop
        # 直接让它在现有循环中运行即可

    def _start_build_thread(self):
        self.build_btn.config(state='disabled')
        self.preview_btn.config(state='disabled')
        cfg = self.config_panel.get_config()
        self.history_mgr.save_history(cfg)
        self.log_viewer.clear()

        t = threading.Thread(target=self._build_worker, args=(cfg,), daemon=True)
        t.start()

    def _build_worker(self, config):
        core = BuilderCore(log_callback=self.log_viewer.log)
        try:
            success, msg = core.build(config)
            if success:
                messagebox.showinfo("Success", t("msg_generate_success").format(path=msg))
                try:
                    subprocess.run(f'explorer /select,"{msg}"', shell=True)
                except:
                    pass
            else:
                messagebox.showerror("Error", t("msg_generate_error").format(error=msg))
        finally:
            self.build_btn.config(state='normal')
            self.preview_btn.config(state='normal')

    def mainloop(self):
        self.root.mainloop()

def main():
    # 安装全局未捕获异常处理器
    try:
        from builder.utils.errors import install_global_handler
    except ImportError:
        try:
            from utils.errors import install_global_handler
        except ImportError:
            install_global_handler = None
    if install_global_handler:
        install_global_handler()

    try:
        import sys
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

    app = BuilderGUI()
    # 默认触发一次主题切换以统一样式
    app.root.after(100, app._toggle_theme)
    app.root.after(150, app._toggle_theme) # 然后切回亮色，保证样式被初始化
    app.mainloop()

if __name__ == "__main__":
    main()
