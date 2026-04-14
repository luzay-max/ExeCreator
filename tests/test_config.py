# -*- coding: utf-8 -*-
"""
test_config_panel.py — ConfigPanel 配置读取测试
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from builder.history_manager import HistoryManager


class TestHistoryManager:
    def test_save_and_load_roundtrip(self, tmp_path):
        hf = str(tmp_path / "test_history.json")
        mgr = HistoryManager(history_file="test_history.json")
        mgr.history_file = hf  # override path

        config = {"target_exe": "test.exe", "target_name": "Test", "target_size_mb": 10}
        mgr.save_history(config)

        loaded = mgr.load_history()
        # Override path for load too
        mgr2 = HistoryManager()
        mgr2.history_file = hf
        loaded = mgr2.load_history()

        assert loaded["target_exe"] == "test.exe"
        assert loaded["target_size_mb"] == 10

    def test_load_missing_file_returns_empty(self, tmp_path):
        mgr = HistoryManager()
        mgr.history_file = str(tmp_path / "nonexistent.json")
        result = mgr.load_history()
        assert result == {}

    def test_load_corrupted_file_returns_empty(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("NOT VALID JSON {{{{", encoding="utf-8")
        mgr = HistoryManager()
        mgr.history_file = str(bad_file)
        result = mgr.load_history()
        assert result == {}
