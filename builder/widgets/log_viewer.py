# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk

class LogViewer(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self._setup_ui()
        
    def _setup_ui(self):
        self.log_text = tk.Text(self, height=10, state='disabled', 
                               font=("Consolas", 9), background='#f5f5f5')
        self.log_text.pack(fill='both', expand=True, pady=(0, 10))

    def log(self, message: str):
        """添加一条日志"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        if hasattr(self, 'update'):
            self.update()

    def clear(self):
        """清空日志"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
