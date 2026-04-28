# -*- coding: utf-8 -*-
"""CloudUploader 单元测试。"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from builder.utils.cloud_uploader import CloudUploader  # noqa: E402


class TestCloudUploader(unittest.TestCase):

    def test_available_services(self):
        services = CloudUploader.get_available_services()
        self.assertIn("file.io", services)
        self.assertIn("0x0.st", services)
        self.assertIn("tmpfiles", services)

    def test_upload_missing_file(self):
        up = CloudUploader()
        ok, msg = up.upload("/nonexistent/file.exe")
        self.assertFalse(ok)
        self.assertIn("不存在", msg)

    def test_upload_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            path = f.name
        try:
            ok, msg = CloudUploader().upload(path)
            self.assertFalse(ok)
            self.assertIn("为空", msg)
        finally:
            os.unlink(path)

    def test_unsupported_service(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            f.write(b"test data")
            path = f.name
        try:
            up = CloudUploader(service="unknown_service")
            ok, msg = up.upload(path)
            self.assertFalse(ok)
            self.assertIn("不支持", msg)
        finally:
            os.unlink(path)

    def test_multipart_builder(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            f.write(b"hello world")
            path = f.name
        try:
            up = CloudUploader()
            body, ct = up._build_multipart(path)
            self.assertIn(b"hello world", body)
            self.assertIn("multipart/form-data", ct)
            self.assertIn("boundary=", ct)
        finally:
            os.unlink(path)

    def test_qr_text_generation(self):
        text = CloudUploader.generate_qr_text("https://example.com/file")
        self.assertIn("https://example.com/file", text)
        self.assertIn("qrserver.com", text)

    def test_timeout_clamped(self):
        up = CloudUploader(timeout=1)
        self.assertEqual(up.timeout, 10)

    @patch("builder.utils.cloud_uploader.urllib.request.urlopen")
    def test_fileio_success(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b'{"success":true,"link":"https://file.io/abc"}'
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as f:
            f.write(b"test")
            path = f.name
        try:
            up = CloudUploader(service="file.io")
            ok, url = up.upload(path)
            self.assertTrue(ok)
            self.assertEqual(url, "https://file.io/abc")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
