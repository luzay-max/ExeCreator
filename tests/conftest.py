# -*- coding: utf-8 -*-
"""
conftest.py — pytest 全局 fixture 配置
"""
import os
import sys

import pytest

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def tmp_file(tmp_path):
    """创建一个临时小文件用于测试。"""
    f = tmp_path / "test_target.exe"
    f.write_bytes(b"\x00" * 1024)  # 1KB
    return str(f)


@pytest.fixture
def tmp_dir(tmp_path):
    """创建一个包含目标文件的临时目录结构。"""
    game_dir = tmp_path / "Games" / "TestGame"
    game_dir.mkdir(parents=True)
    target = game_dir / "TestGame.exe"
    target.write_bytes(b"\x00" * 512)
    return str(tmp_path), str(target)
