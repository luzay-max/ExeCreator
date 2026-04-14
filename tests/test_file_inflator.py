# -*- coding: utf-8 -*-
"""
test_file_inflator.py — FileInflator 单元测试
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from builder.utils.file_inflator import FileInflator


class TestParseSize:
    def setup_method(self):
        self.inflator = FileInflator()

    def test_plain_number_defaults_to_mb(self):
        assert self.inflator.parse_size("10") == 10 * 1024 * 1024

    def test_mb_suffix(self):
        assert self.inflator.parse_size("5MB") == 5 * 1024 * 1024

    def test_kb_suffix(self):
        assert self.inflator.parse_size("512KB") == 512 * 1024

    def test_gb_suffix(self):
        assert self.inflator.parse_size("1GB") == 1024 * 1024 * 1024

    def test_bytes_suffix(self):
        assert self.inflator.parse_size("4096B") == 4096

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            self.inflator.parse_size("not_a_size")


class TestInflateFile:
    def setup_method(self):
        self.inflator = FileInflator()

    def test_inflate_increases_size(self, tmp_file):
        original_size = os.path.getsize(tmp_file)
        target_mb = 0.01  # 10KB target
        result = self.inflator.inflate_file(tmp_file, target_mb)
        assert result["success"] is True
        new_size = os.path.getsize(tmp_file)
        assert new_size >= int(target_mb * 1024 * 1024)

    def test_inflate_skip_when_already_large(self, tmp_file):
        # target = 0.0001MB ≈ 104 bytes, file is 1024 bytes
        result = self.inflator.inflate_file(tmp_file, 0.0001)
        assert result["success"] is True
        assert result["inflated_bytes"] == 0

    def test_inflate_nonexistent_file_raises(self):
        with pytest.raises(Exception):
            self.inflator.inflate_file("/nonexistent/file.exe", 10)

    def test_inflate_result_dict_fields(self, tmp_file):
        result = self.inflator.inflate_file(tmp_file, 0.01)
        assert "success" in result
        assert "original_size" in result
        assert "final_size" in result
        assert "inflated_bytes" in result
        assert "message" in result
