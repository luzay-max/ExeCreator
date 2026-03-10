import tkinter as tk
from tkinter import ttk
import random

class FakeLoaderUI:
    def __init__(self, title="Loading...", width=600, height=400):
        self.root = tk.Tk()
        self.root.title(title)
        
        # 设置窗口大小并居中
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # 禁止调整大小
        self.root.resizable(False, False)
        
        # 移除窗口边框（可选，增加沉浸感）
        self.root.overrideredirect(True)
        
        # 样式设置
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 布局
        self.main_frame = tk.Frame(self.root, bg='#2b2b2b')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        self.title_label = tk.Label(
            self.main_frame, 
            text=title, 
            font=("Microsoft YaHei", 16, "bold"),
            bg='#2b2b2b',
            fg='white'
        )
        self.title_label.pack(pady=(50, 20))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            length=400, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=20)
        
        # 状态文本
        self.status_label = tk.Label(
            self.main_frame,
            text="Initializing...",
            font=("Consolas", 10),
            bg='#2b2b2b',
            fg='#aaaaaa'
        )
        self.status_label.pack(pady=10)
        
        self.running = True
        self.auto_progress()

    def update_status(self, text):
        if self.running:
            self.status_label.config(text=text)
            self.root.update()

    def update_progress(self, value):
        if self.running:
            self.progress_var.set(value)
            self.root.update()

    def auto_progress(self):
        """模拟一个缓慢的进度增长，防止进度条不动"""
        if not self.running:
            return
        
        current = self.progress_var.get()
        if current < 90:
            increment = random.uniform(0.1, 0.5)
            self.progress_var.set(current + increment)
        
        self.root.after(100, self.auto_progress)

    def close(self):
        self.running = False
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()

if __name__ == "__main__":
    # 测试预览
    ui = FakeLoaderUI("植物大战僵尸3 - 资源加载中")
    ui.root.after(3000, ui.close)
    ui.mainloop()
