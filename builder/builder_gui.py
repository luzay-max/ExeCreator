# -*- coding: utf-8 -*-
"""
PrankLauncherBuilder - 恶搞启动器生成工具
主界面模块 - v4.0 customtkinter 现代化重构
"""
import logging
import os
import subprocess
import sys
import threading

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("请安装 customtkinter: pip install customtkinter")

from tkinter import messagebox

# 确保项目根目录在 sys.path 中（无论从哪里启动都能找到模块）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from builder_core import BuilderCore  # noqa: E402
from history_manager import HistoryManager  # noqa: E402
from widgets.config_panel import ConfigPanel  # noqa: E402
from widgets.log_viewer import LogViewer  # noqa: E402

try:
    from builder.locale.i18n import get_current_lang, set_lang, t  # noqa: E402
except ImportError:
    from locale.i18n import get_current_lang, set_lang, t  # type: ignore # noqa: E402

try:
    from builder.utils.constants import APP_NAME, APP_TITLE, LOG_FORMAT, VERSION
except ImportError:
    try:
        from utils.constants import APP_NAME, APP_TITLE, LOG_FORMAT, VERSION  # type: ignore
    except ImportError:
        # Fallback values if constants module is completely missing
        APP_NAME = "PrankLauncherBuilder"
        APP_TITLE = "Prank Launcher Builder v4.0"
        LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        VERSION = "4.0.0"

logger = logging.getLogger(__name__)

# ============ 色彩主题 ============
ACCENT_COLOR = "#6C5CE7"       # 主色调 — 优雅紫
ACCENT_HOVER = "#5A4BD1"       # 悬停色
SUCCESS_COLOR = "#00B894"      # 成功绿
WARNING_COLOR = "#FDCB6E"      # 警告黄
DANGER_COLOR = "#FF7675"       # 危险红


class BuilderGUI:
    def __init__(self):
        # 设置 customtkinter 外观
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry("750x960")
        self.root.minsize(700, 900)

        self.history_mgr = HistoryManager()

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
        # ============ 顶部标题栏 ============
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill='x', padx=20, pady=(15, 0))

        # 标题
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="🎭 恶搞启动器生成工具",
            font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold"),
        ).pack(anchor='w')

        ctk.CTkLabel(
            title_frame,
            text=f"v{VERSION}  •  Prank Launcher Builder",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor='w')

        # 右侧按钮组
        btn_group = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_group.pack(side='right')

        self.lang_btn = ctk.CTkButton(
            btn_group,
            text=t("menu_language"),
            width=120,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color=("gray85", "gray25"),
            command=self._toggle_lang,
        )
        self.lang_btn.pack(side='left', padx=5)

        self.theme_btn = ctk.CTkButton(
            btn_group,
            text="🌙 " + t("theme_light"),
            width=120,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color=("gray85", "gray25"),
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side='left', padx=5)

        # ============ 分隔线 ============
        ctk.CTkFrame(self.root, height=2, fg_color=("gray80", "gray30")).pack(
            fill='x', padx=20, pady=10
        )

        # ============ 主内容区 (可滚动) ============
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.root,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray40"),
        )
        self.scrollable_frame.pack(fill='both', expand=True, padx=15, pady=(0, 5))

        # 核心配置面板
        self.config_panel = ConfigPanel(self.scrollable_frame)

        # ============ 底部操作栏 ============
        bottom_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_frame.pack(fill='x', padx=20, pady=(5, 10))

        self.preview_btn = ctk.CTkButton(
            bottom_frame,
            text="👁  " + t("btn_preview"),
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self._preview_ui,
        )
        self.preview_btn.pack(side='left', padx=(0, 10), expand=True, fill='x')

        self.build_btn = ctk.CTkButton(
            bottom_frame,
            text="🚀  " + t("btn_generate"),
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            command=self._start_build_thread,
        )
        self.build_btn.pack(side='left', expand=True, fill='x')

        # ============ 日志区 ============
        self.log_viewer = LogViewer(self.root)

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="🌑 " + t("theme_dark"))
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="🌙 " + t("theme_light"))

    def _toggle_lang(self):
        current = get_current_lang()
        new_lang = "en_US" if current == "zh_CN" else "zh_CN"
        set_lang(new_lang)
        messagebox.showinfo(
            "Language / 语言",
            "Language changed. Please restart the application for changes to take full effect.\n"
            "语言已切换，请重启程序以完全生效。"
        )
        self.lang_btn.configure(text=t("menu_language"))
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            self.theme_btn.configure(text="🌙 " + t("theme_light"))
        else:
            self.theme_btn.configure(text="🌑 " + t("theme_dark"))
        self.preview_btn.configure(text="👁  " + t("btn_preview"))
        self.build_btn.configure(text="🚀  " + t("btn_generate"))

    def _preview_ui(self):
        """生成界面预览"""
        config = self.config_panel.get_config()
        title = config.get("window_title", "加载中...")

        from template.fake_ui import FakeLoaderUI

        def _mock_close(ui):
            ui.running = False
            ui.root.destroy()

        # 使用 Toplevel 作为父窗口
        ui = FakeLoaderUI(title, splash_data=config.get("splash_image_data", ""), parent=self.root)
        ui.close = lambda: _mock_close(ui)

    def _start_build_thread(self):
        self.build_btn.configure(state='disabled')
        self.preview_btn.configure(state='disabled')
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
                self._last_build_path = msg
                messagebox.showinfo("Success", t("msg_generate_success").format(path=msg))
                try:
                    subprocess.run(f'explorer /select,"{msg}"', shell=True)
                except Exception:
                    pass
                # v4.0: 云端分发提示
                self._prompt_cloud_upload(msg)
            else:
                messagebox.showerror("Error", t("msg_generate_error").format(error=msg))
        finally:
            self.build_btn.configure(state='normal')
            self.preview_btn.configure(state='normal')

    def _prompt_cloud_upload(self, file_path: str):
        """构建成功后询问是否上传到云端。"""
        answer = messagebox.askyesno(
            t("cloud_upload_title", "云端分发"),
            t("cloud_upload_prompt", "构建成功！是否上传到云端生成分享链接？"),
        )
        if not answer:
            return

        self.log_viewer.log("正在上传到云端...")
        try:
            from utils.cloud_uploader import CloudUploader
        except ImportError:
            from builder.utils.cloud_uploader import CloudUploader

        def _upload():
            uploader = CloudUploader(service="file.io")
            ok, result = uploader.upload(file_path)
            if ok:
                qr_info = CloudUploader.generate_qr_text(result)
                self.log_viewer.log(f"✅ 上传成功！\n{qr_info}")
                messagebox.showinfo(
                    t("cloud_upload_title", "云端分发"),
                    t("cloud_upload_success", "上传成功！\n链接: {url}").format(url=result),
                )
            else:
                self.log_viewer.log(f"❌ 上传失败: {result}")
                messagebox.showerror(
                    t("cloud_upload_title", "云端分发"),
                    t("cloud_upload_fail", "上传失败: {error}").format(error=result),
                )

        threading.Thread(target=_upload, daemon=True).start()

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
    if install_global_handler is not None:
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
    app.mainloop()

if __name__ == "__main__":
    main()
