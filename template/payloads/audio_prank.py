# -*- coding: utf-8 -*-
"""
后台搞怪音频播放载荷 — v4.0 新增

使用 Windows 内置的 winsound 模块或 PlaySound API 在后台播放音频。
支持两种模式：
1. 内嵌音频数据（Base64 编码的 WAV）
2. 系统蜂鸣音序列（无需任何外部文件）

使用方式:
    prank = AudioPrank()
    prank.play_beep_sequence()       # 蜂鸣序列
    prank.play_embedded(wav_b64)     # 播放嵌入的 WAV
"""
import base64
import os
import random
import tempfile
import threading
import time
from typing import List, Optional, Tuple


class AudioPrank:
    """后台搞怪音频播放器。"""

    # 预置蜂鸣旋律（频率Hz, 时长ms）
    MELODIES = {
        "alarm": [
            (800, 200), (600, 200), (800, 200), (600, 200),
            (800, 200), (600, 200), (800, 200), (600, 200),
        ],
        "error_beep": [
            (440, 500), (0, 200), (440, 500), (0, 200), (440, 500),
        ],
        "ascending": [
            (262, 150), (294, 150), (330, 150), (349, 150),
            (392, 150), (440, 150), (494, 150), (523, 300),
        ],
        "descending": [
            (523, 150), (494, 150), (440, 150), (392, 150),
            (349, 150), (330, 150), (294, 150), (262, 300),
        ],
        "random_chaos": [],  # 运行时随机生成
        "windows_error": [
            (523, 100), (0, 50), (392, 300),
        ],
        "doorbell": [
            (659, 400), (523, 600),
        ],
    }

    def __init__(self, repeat: int = 1, delay_between: float = 0.5) -> None:
        """
        :param repeat: 播放重复次数
        :param delay_between: 每次重复之间的间隔（秒）
        """
        self.repeat = max(1, repeat)
        self.delay_between = delay_between

    def play_beep_sequence(
        self,
        melody_name: Optional[str] = None,
        background: bool = True,
    ) -> None:
        """
        播放蜂鸣旋律。

        :param melody_name: 旋律名称，None 则随机选择
        :param background:  是否在后台线程中播放
        """
        if melody_name and melody_name in self.MELODIES:
            notes = self.MELODIES[melody_name]
        elif melody_name == "random_chaos" or melody_name is None:
            # 随机生成混沌旋律
            notes = [
                (random.randint(200, 2000), random.randint(50, 300))
                for _ in range(random.randint(8, 20))
            ]
        else:
            notes = list(self.MELODIES.values())[
                random.randint(0, len(self.MELODIES) - 1)
            ]

        if background:
            t = threading.Thread(
                target=self._play_notes,
                args=(notes,),
                daemon=True,
            )
            t.start()
        else:
            self._play_notes(notes)

    def play_embedded(
        self,
        wav_base64: str,
        background: bool = True,
    ) -> None:
        """
        播放 Base64 编码的 WAV 音频数据。

        :param wav_base64: Base64 编码的 WAV 数据
        :param background: 是否在后台线程中播放
        """
        if not wav_base64:
            return

        if background:
            t = threading.Thread(
                target=self._play_wav_data,
                args=(wav_base64,),
                daemon=True,
            )
            t.start()
        else:
            self._play_wav_data(wav_base64)

    def play_system_sound(self, sound_type: str = "exclamation") -> None:
        """
        播放 Windows 系统音效。

        :param sound_type: asterisk, exclamation, hand, question, default
        """
        try:
            import winsound

            sound_map = {
                "asterisk": winsound.MB_ICONASTERISK,
                "exclamation": winsound.MB_ICONEXCLAMATION,
                "hand": winsound.MB_ICONHAND,
                "question": winsound.MB_ICONQUESTION,
                "default": winsound.MB_OK,
            }
            flag = sound_map.get(sound_type, winsound.MB_ICONEXCLAMATION)
            winsound.MessageBeep(flag)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  内部实现
    # ------------------------------------------------------------------ #

    def _play_notes(self, notes: List[Tuple[int, int]]) -> None:
        """播放蜂鸣音序列（同步）。"""
        try:
            import winsound

            for _ in range(self.repeat):
                for freq, duration in notes:
                    if freq <= 0:
                        # 静音间隔
                        time.sleep(duration / 1000.0)
                    else:
                        winsound.Beep(max(37, freq), duration)
                if self.repeat > 1:
                    time.sleep(self.delay_between)
        except Exception:
            pass

    def _play_wav_data(self, wav_base64: str) -> None:
        """解码并播放 WAV 数据（同步）。"""
        tmp_path = None
        try:
            import winsound

            wav_data = base64.b64decode(wav_base64)

            # 写入临时文件
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(wav_data)

            for _ in range(self.repeat):
                winsound.PlaySound(
                    tmp_path,
                    winsound.SND_FILENAME | winsound.SND_NODEFAULT,
                )
                if self.repeat > 1:
                    time.sleep(self.delay_between)
        except Exception:
            pass
        finally:
            # 清理临时文件
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass


if __name__ == "__main__":
    prank = AudioPrank(repeat=2)
    prank.play_beep_sequence("windows_error", background=False)
