import tkinter as tk
from tkinter import ttk
import random
import base64

class FakeLoaderUI:
    def __init__(self, title="Loading...", width=600, height=400, splash_data="", parent=None):
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()
        self.root.title(title)
        
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Load splash image
        self.splash_img = None
        if splash_data:
            try:
                img = tk.PhotoImage(data=base64.b64decode(splash_data))
                
                max_width = 800
                max_height = 550
                w = img.width()
                h = img.height()
                
                if w > max_width or h > max_height:
                    w_factor = (w + max_width - 1) // max_width
                    h_factor = (h + max_height - 1) // max_height
                    factor = max(w_factor, h_factor)
                    if factor > 1:
                        img = img.subsample(factor, factor)
                        w = img.width()
                        h = img.height()
                        
                self.splash_img = img
                width = w
                height = h
            except Exception as e:
                pass

        self.canvas = tk.Canvas(self.root, width=width, height=height, bg='#2b2b2b', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        if self.splash_img:
            self.canvas.create_image(0, 0, image=self.splash_img, anchor="nw")

        # 设置窗口大小并居中
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        center_x = width // 2
        
        self.title_text_id = self.canvas.create_text(
            center_x, height // 2 - 40,
            text=title,
            font=("Microsoft YaHei", 16, "bold"),
            fill="white",
            justify="center"
        )
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.root, 
            orient=tk.HORIZONTAL, 
            length=int(width * 0.7), 
            mode='determinate',
            variable=self.progress_var
        )
        self.canvas.create_window(center_x, height // 2 + 10, window=self.progress_bar)
        
        self.status_text_id = self.canvas.create_text(
            center_x, height // 2 + 50,
            text="Initializing...",
            font=("Consolas", 10),
            fill="#dddddd",
            justify="center"
        )
        
        self.running = True
        
        # 内置假任务列表用于更逼真的状态展示
        self.fake_tasks = [
            "正在校验本地资源完整性...",
            "连接服务器安全通道...",
            "下载更新清单文件...",
            "初始化游戏引擎环境...",
            "加载材质与纹理资源...",
            "检查反作弊系统状态...",
            "同步玩家云端配置...",
            "等待图形驱动响应..."
        ]
        
        # 绑定快捷键以便退出（特别是对无边框窗口）
        self.root.bind('<Escape>', lambda e: self.close())
        self.canvas.bind('<Double-Button-1>', lambda e: self.close())
        
        self.auto_progress()

    def update_status(self, text):
        if self.running:
            self.canvas.itemconfig(self.status_text_id, text=text)
            self.root.update()

    def update_progress(self, value):
        if self.running:
            self.progress_var.set(value)
            self.root.update()

    def auto_progress(self):
        if not self.running:
            return
            
        current = self.progress_var.get()
        if current < 90:
            increment = random.uniform(0.1, 0.6)
            self.progress_var.set(current + increment)
            
            # 随机更新状态文本
            if random.random() < 0.15:  # 15% 概率切换状态
                self.update_status(random.choice(self.fake_tasks))
                
        self.root.after(100, self.auto_progress)

    def close(self):
        self.running = False
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()

if __name__ == "__main__":
    ui = FakeLoaderUI("植物大战僵尸3 - 资源加载中")
    ui.root.after(3000, ui.close)
    ui.mainloop()
