import os
import sys
import threading
import time
import webbrowser

# --- IMPORTS START ---
# 导入同目录下的模块
# PyInstaller 打包时会将这些模块打包进去
try:
    from fake_ui import FakeLoaderUI
    from launcher_core import GameScanner
except ImportError:
    # 开发环境下的导入路径处理
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from fake_ui import FakeLoaderUI
    from launcher_core import GameScanner
# --- IMPORTS END ---

# --- CONFIG START ---
# 这些值将在生成时被替换
CONFIG = {
    "target_exe": "YuanShen.exe",
    "target_name": "原神",
    "fallback_url": "https://ys.mihoyo.com",
    "window_title": "正在加载游戏资源...",
    "show_log": True,
    "error_message": "" # 默认为空，不弹窗
}
# --- CONFIG END ---

def show_fake_error():
    """弹出伪造的系统错误框"""
    msg = CONFIG.get("error_message")
    if not msg:
        return

    try:
        import ctypes
        # MessageBoxW(hwnd, text, caption, type)
        # type 0x10 = MB_ICONHAND (Error Icon)
        ctypes.windll.user32.MessageBoxW(0, msg, "System Error", 0x10)
    except:
        pass

def main():
    # 1. 初始化 UI
    ui = FakeLoaderUI(title=CONFIG["window_title"], splash_data=CONFIG.get("splash_image_data", ""))

    # 2. 初始化扫描器
    scanner = GameScanner(CONFIG["target_exe"], CONFIG["target_name"])

    # 定义日志回调
    def log_callback(msg):
        if CONFIG["show_log"]:
            ui.update_status(msg)

    scanner.set_log_callback(log_callback)

    # 3. 扫描线程
    def scan_thread_func():
        # 稍微延迟一下，让用户看到加载界面
        time.sleep(1.5)

        found_path = scanner.scan()

        # 扫描结束，进度条拉满
        ui.update_progress(100)
        ui.update_status("加载完成")
        time.sleep(0.5)

        # 执行后续操作 (在关闭 UI 之前执行，防止主程序提前退出)
        try:
            if found_path:
                print(f"Found: {found_path}")
                scanner.launch_game()
            else:
                print("Not found, opening URL")
                # 弹窗欺骗 (阻塞式)
                show_fake_error()
                webbrowser.open(CONFIG["fallback_url"])
        except Exception as e:
            print(f"Execution error: {e}")

        # 保存日志
        try:
            scanner.save_scan_log()
        except:
            pass

        # 给一点时间让外部程序启动
        time.sleep(1.0)

        # 关闭 UI (这将导致主线程退出)
        ui.close()

    # 启动后台线程
    t = threading.Thread(target=scan_thread_func, daemon=True)
    t.start()

    # 进入 UI 主循环（阻塞直到 ui.close() 被调用）
    ui.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 确保出错时也能打开网页作为保底
        print(f"Error: {e}")
        webbrowser.open(CONFIG["fallback_url"])
