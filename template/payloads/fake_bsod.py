# -*- coding: utf-8 -*-
"""
高保真蓝屏 (BSOD) 伪装载荷 — v4.0 新增

全屏显示一个高度逼真的 Windows 蓝屏死机画面，使用 tkinter 实现。
支持自定义停止代码和倒计时百分比，数秒后自动关闭。

使用方式:
    bsod = FakeBSOD(stop_code="CRITICAL_PROCESS_DIED", duration=8)
    bsod.show()  # 阻塞显示，duration 秒后自动关闭
"""
import random
import tkinter as tk
from typing import Optional


class FakeBSOD:
    """高仿 Windows 10/11 蓝屏画面。"""

    # 经典蓝屏停止代码列表
    STOP_CODES = [
        "CRITICAL_PROCESS_DIED",
        "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
        "IRQL_NOT_LESS_OR_EQUAL",
        "VIDEO_TDR_TIMEOUT_DETECTED",
        "PAGE_FAULT_IN_NONPAGED_AREA",
        "SYSTEM_SERVICE_EXCEPTION",
        "KMODE_EXCEPTION_NOT_HANDLED",
        "UNEXPECTED_KERNEL_MODE_TRAP",
        "BAD_POOL_HEADER",
        "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
    ]

    def __init__(
        self,
        stop_code: Optional[str] = None,
        duration: int = 8,
    ) -> None:
        """
        :param stop_code: 蓝屏停止代码。None 则随机选择。
        :param duration:  显示持续时间（秒），之后自动关闭。
        """
        self.stop_code = stop_code or random.choice(self.STOP_CODES)
        self.duration = max(3, duration)
        self.root: Optional[tk.Tk] = None
        self._progress = 0

    def show(self) -> None:
        """显示蓝屏画面（阻塞），duration 秒后自动关闭。"""
        try:
            self.root = tk.Tk()
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost", True)
            self.root.configure(bg="#0078D7", cursor="none")
            self.root.overrideredirect(True)

            # 阻止 Alt+F4
            self.root.protocol("WM_DELETE_WINDOW", lambda: None)

            # 快捷键 ESC 可关闭（给使用者留个后门）
            self.root.bind("<Escape>", lambda e: self._close())

            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()

            canvas = tk.Canvas(
                self.root,
                width=screen_w,
                height=screen_h,
                bg="#0078D7",
                highlightthickness=0,
            )
            canvas.pack()

            # 大号哭脸 :(
            sad_y = int(screen_h * 0.25)
            canvas.create_text(
                int(screen_w * 0.12), sad_y,
                text=":(",
                font=("Segoe UI Light", 140),
                fill="white",
                anchor="w",
            )

            # 主提示文本
            msg_x = int(screen_w * 0.12)
            msg_y = sad_y + 160

            main_msg = (
                "Your PC ran into a problem and needs to restart. "
                "We're just collecting some error info, and then we'll "
                "restart for you."
            )
            canvas.create_text(
                msg_x, msg_y,
                text=main_msg,
                font=("Segoe UI", 22),
                fill="white",
                anchor="nw",
                width=int(screen_w * 0.7),
            )

            # 进度百分比
            self._progress_text_id = canvas.create_text(
                msg_x, msg_y + 100,
                text="0% complete",
                font=("Segoe UI", 22),
                fill="white",
                anchor="nw",
            )

            # 底部信息区
            bottom_y = int(screen_h * 0.72)
            canvas.create_text(
                msg_x, bottom_y,
                text=(
                    "For more information about this problem and possible fixes, "
                    "visit https://www.windows.com/stopcode"
                ),
                font=("Segoe UI", 14),
                fill="white",
                anchor="nw",
                width=int(screen_w * 0.6),
            )

            # 停止代码
            canvas.create_text(
                msg_x, bottom_y + 60,
                text="If you call a support person, give them this info:",
                font=("Segoe UI", 14),
                fill="white",
                anchor="nw",
            )
            canvas.create_text(
                msg_x, bottom_y + 90,
                text=f"Stop code: {self.stop_code}",
                font=("Segoe UI", 14),
                fill="white",
                anchor="nw",
            )

            self._canvas = canvas

            # 启动进度动画
            self._animate_progress()

            # 定时自动关闭
            self.root.after(self.duration * 1000, self._close)

            self.root.mainloop()
        except Exception:
            # 静默失败
            pass

    def _animate_progress(self) -> None:
        """模拟进度增长。"""
        if self.root is None:
            return

        try:
            if self._progress < 100:
                self._progress += random.randint(1, 5)
                self._progress = min(self._progress, 100)
                self._canvas.itemconfig(
                    self._progress_text_id,
                    text=f"{self._progress}% complete",
                )
                # 随机间隔
                interval = random.randint(200, 600)
                self.root.after(interval, self._animate_progress)
        except Exception:
            pass

    def _close(self) -> None:
        """关闭蓝屏窗口。"""
        try:
            if self.root:
                self.root.destroy()
                self.root = None
        except Exception:
            pass


if __name__ == "__main__":
    bsod = FakeBSOD(duration=5)
    bsod.show()
