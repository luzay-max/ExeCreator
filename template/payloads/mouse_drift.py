# -*- coding: utf-8 -*-
"""
鼠标漂移整蛊载荷 — v4.0 新增

在后台线程中以微小的随机偏移移动鼠标光标，
制造"鼠标不听使唤"的整蛊效果。支持配置强度和持续时间。

使用 Windows API (ctypes) 直接操作鼠标位置，无需第三方库。

使用方式:
    drift = MouseDrift(intensity=3, duration=15)
    drift.start()   # 后台启动漂移
    drift.stop()    # 提前停止
"""
import ctypes
import ctypes.wintypes
import random
import threading
import time
from typing import Optional


class MouseDrift:
    """鼠标漂移整蛊器。"""

    def __init__(
        self,
        intensity: int = 3,
        duration: float = 15.0,
        interval: float = 0.05,
    ) -> None:
        """
        :param intensity: 漂移强度（1-10），数值越大鼠标偏移越明显
        :param duration:  持续时间（秒），0 表示无限直到 stop() 被调用
        :param interval:  每次移动的间隔（秒）
        """
        self.intensity = max(1, min(10, intensity))
        self.duration = max(0.0, duration)
        self.interval = max(0.02, interval)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """在后台线程中启动鼠标漂移。"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._drift_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """停止鼠标漂移。"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------ #
    #  内部实现
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_cursor_pos() -> tuple:
        """获取当前鼠标位置。"""
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)

    @staticmethod
    def _set_cursor_pos(x: int, y: int) -> None:
        """设置鼠标位置。"""
        ctypes.windll.user32.SetCursorPos(x, y)

    def _drift_loop(self) -> None:
        """漂移主循环。"""
        start_time = time.time()

        try:
            while self._running:
                # 检查持续时间
                if self.duration > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= self.duration:
                        break

                # 获取当前位置
                x, y = self._get_cursor_pos()

                # 计算随机偏移
                # 强度映射：intensity 1 → ±1px, intensity 10 → ±15px
                max_offset = self.intensity * 1.5
                dx = random.uniform(-max_offset, max_offset)
                dy = random.uniform(-max_offset, max_offset)

                # 偶尔来一次大跳跃（5% 概率）
                if random.random() < 0.05:
                    dx *= 3
                    dy *= 3

                new_x = int(x + dx)
                new_y = int(y + dy)

                # 确保不超出屏幕边界
                screen_w = ctypes.windll.user32.GetSystemMetrics(0)
                screen_h = ctypes.windll.user32.GetSystemMetrics(1)
                new_x = max(0, min(screen_w - 1, new_x))
                new_y = max(0, min(screen_h - 1, new_y))

                self._set_cursor_pos(new_x, new_y)

                time.sleep(self.interval)

        except Exception:
            pass
        finally:
            self._running = False


if __name__ == "__main__":
    drift = MouseDrift(intensity=5, duration=10)
    print("Mouse drift starting for 10 seconds... (press Ctrl+C to abort)")
    drift.start()
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        drift.stop()
    print("Done.")
