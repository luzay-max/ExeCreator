"""
启动闪屏模块
在主程序启动时显示品牌闪屏
"""
import tkinter as tk
import threading
import time
import sys

def show_splash(duration=1500):
    """
    显示启动闪屏
    
    Args:
        duration: 闪屏显示时长（毫秒）
    """
    root = tk.Tk()
    
    # 设置无边框、全屏、置顶
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    
    # 深色背景色
    bg_color = '#1a1a2e'
    root.configure(bg=bg_color)
    
    # 居中显示
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 400, 250
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # 标题 - 使用大字体
    title_label = tk.Label(
        root,
        text="恶搞启动器生成工具",
        font=("Microsoft YaHei", 18, "bold"),
        bg=bg_color,
        fg='#ffffff'
    )
    title_label.pack(pady=(50, 15))
    
    # 副标题
    subtitle_label = tk.Label(
        root,
        text="Prank Launcher Builder",
        font=("Arial", 10),
        bg=bg_color,
        fg='#888888'
    )
    subtitle_label.pack()
    
    # 分隔线
    separator = tk.Frame(root, height=2, bg='#3a3a5e')
    separator.pack(fill='x', padx=40, pady=20)
    
    # 版本号
    version_label = tk.Label(
        root,
        text="v1.0.0",
        font=("Microsoft YaHei", 9),
        bg=bg_color,
        fg='#666666'
    )
    version_label.pack(side=tk.BOTTOM, pady=(0, 15))
    
    # 加载点动画
    dots_label = tk.Label(
        root,
        text="正在初始化",
        font=("Microsoft YaHei", 9),
        bg=bg_color,
        fg='#4a9eff'
    )
    dots_label.pack(side=tk.BOTTOM, pady=(0, 5))
    
    def animate_dots():
        """加载点动画"""
        current = dots_label.cget('text')
        if '...' in current:
            dots_label.config(text='正在初始化')
        else:
            dots_label.config(text=current + '.')
        dots_label.after(500, animate_dots)
    
    animate_dots()
    
    # 更新窗口
    root.update()
    
    # 延时后关闭
    def close_splash():
        root.destroy()
    
    root.after(duration, close_splash)
    root.mainloop()

def run_splash_thread(duration=1500):
    """
    在新线程中运行闪屏
    确保主程序不会被阻塞
    """
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        splash_thread = threading.Thread(target=show_splash, args=(duration,), daemon=True)
        splash_thread.start()
    else:
        # 开发环境 - 缩短闪屏时间或不显示
        pass  # 开发环境不显示闪屏

if __name__ == "__main__":
    # 测试闪屏
    show_splash(2000)
