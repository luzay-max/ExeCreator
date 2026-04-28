# -*- coding: utf-8 -*-
"""
日志查看器 — v4.0 customtkinter 重构
"""
try:
    import customtkinter as ctk
except ImportError:
    raise ImportError("请安装 customtkinter: pip install customtkinter")



class LogViewer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10, height=180)
        self.pack(fill='x', padx=15, pady=(5, 10))
        self.pack_propagate(False)

        # 标题
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill='x', padx=10, pady=(8, 2))
        ctk.CTkLabel(
            header, text="📋 构建日志",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#6C5CE7",
        ).pack(side='left')

        ctk.CTkButton(
            header, text="清空", width=50, height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            hover_color=("gray85", "gray25"),
            command=self.clear,
        ).pack(side='right')

        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6,
            wrap='word',
            state='disabled',
            activate_scrollbars=True,
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(2, 8))

    def log(self, message: str):
        """追加一条日志消息。"""
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def clear(self):
        """清空日志。"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')
