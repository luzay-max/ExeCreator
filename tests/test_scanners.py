# -*- coding: utf-8 -*-
"""
test_scanners.py — 扫描器模块单元测试
"""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from template.scanner.base_scanner import BaseScanner  # noqa: E402
from template.scanner.cache_scanner import CacheScanner  # noqa: E402
from template.scanner.drive_scanner import DriveScanner  # noqa: E402


class TestBaseScanner:
    def test_log_appends_entry(self):
        s = BaseScanner("test.exe", "Test")
        s.log("hello")
        assert len(s.logs) == 1
        assert "hello" in s.logs[0]

    def test_stop_sets_flags(self):
        s = BaseScanner("test.exe", "Test")
        assert s.stop_flag is False
        s.stop()
        assert s.stop_flag is True
        assert s._found_event.is_set()

    def test_get_available_drives_returns_list(self):
        s = BaseScanner("test.exe", "Test")
        drives = s.get_available_drives()
        assert isinstance(drives, list)
        # C:\ should exist on Windows
        assert any("C" in d for d in drives)

    def test_check_file_in_dir_finds_file(self, tmp_dir):
        base_dir, target_path = tmp_dir
        s = BaseScanner("TestGame.exe", "TestGame")
        found = s.check_file_in_dir(os.path.join(base_dir, "Games", "TestGame"))
        assert found is True
        assert s.found_path == target_path

    def test_check_file_in_dir_returns_false_for_missing(self, tmp_path):
        s = BaseScanner("nonexistent.exe", "Nope")
        found = s.check_file_in_dir(str(tmp_path))
        assert found is False

    def test_scan_raises_not_implemented(self):
        s = BaseScanner("test.exe", "Test")
        with pytest.raises(NotImplementedError):
            s.scan()


class TestCacheScanner:
    def test_scan_self_data_finds_existing_path(self, tmp_dir):
        base_dir, target_path = tmp_dir
        scanner = CacheScanner("TestGame.exe", "TestGame",
                               known_paths=[target_path])
        result = scanner.scan()
        assert result == target_path

    def test_scan_self_data_skips_missing_paths(self):
        scanner = CacheScanner("TestGame.exe", "TestGame",
                               known_paths=[r"C:\FAKE\PATH\nope.exe"])
        result = scanner.scan()
        assert result is None

    def test_scan_empty_known_paths(self):
        scanner = CacheScanner("TestGame.exe", "TestGame", known_paths=[])
        result = scanner.scan()
        # Will check local cache (probably miss), then self_data (empty) → None
        # This is expected on a dev machine with no cache
        assert result is None


class TestDriveScanner:
    def test_scan_directory_finds_file(self, tmp_dir):
        base_dir, target_path = tmp_dir
        scanner = DriveScanner("TestGame.exe", "TestGame")
        result = scanner._scan_directory(base_dir, max_depth=5)
        assert result == target_path

    def test_scan_directory_respects_depth_limit(self, tmp_path):
        # Create a deeply nested file
        deep = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        (deep / "Deep.exe").write_bytes(b"\x00")

        scanner = DriveScanner("Deep.exe", "Deep")
        result = scanner._scan_directory(str(tmp_path), max_depth=2)
        assert result is None  # depth 5 > max_depth 2

    def test_scan_directory_returns_none_for_empty(self, tmp_path):
        scanner = DriveScanner("NonExistent.exe", "Nope")
        result = scanner._scan_directory(str(tmp_path), max_depth=3)
        assert result is None

    def test_stop_flag_halts_scan(self, tmp_dir):
        base_dir, _ = tmp_dir
        scanner = DriveScanner("TestGame.exe", "TestGame")
        scanner.stop()  # pre-stop
        result = scanner._scan_directory(base_dir, max_depth=5)
        assert result is None
