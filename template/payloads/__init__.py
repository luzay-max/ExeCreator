# -*- coding: utf-8 -*-
"""
恶搞载荷 (Payloads) 包 — v4.0 新增

提供多种可配置的恶搞效果：
- fake_bsod:    高保真蓝屏画面
- audio_prank:  后台播放搞怪音频
- mouse_drift:  鼠标短时间漂移整蛊
"""

try:
    from .audio_prank import AudioPrank
    from .fake_bsod import FakeBSOD
    from .mouse_drift import MouseDrift
except ImportError:
    # 合并打包后这些类已经在同一文件中，无需导入
    pass

__all__ = ["FakeBSOD", "AudioPrank", "MouseDrift"]
