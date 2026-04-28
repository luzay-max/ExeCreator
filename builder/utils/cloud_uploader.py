# -*- coding: utf-8 -*-
"""
云端分发模块 — v4.0
构建完成后自动上传 EXE 到公共文件分享服务并返回下载链接。
仅使用 urllib 标准库，零第三方依赖。
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Tuple


class CloudUploader:
    """
    文件云端上传器，支持多种公共分享服务。

    用法::

        uploader = CloudUploader()
        ok, url = uploader.upload("output/test.exe")
        if ok:
            print(f"分享链接: {url}")
    """

    # 文件大小上限 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __init__(self, service: str = "file.io",
                 timeout: int = 60):
        """
        Args:
            service: 上传服务名称 (file.io / 0x0.st / tmpfiles)
            timeout: HTTP 超时秒数
        """
        self.service = service.lower().strip()
        self.timeout = max(10, timeout)

    def upload(self, file_path: str) -> Tuple[bool, str]:
        """
        上传文件并返回分享链接。

        Returns:
            (success, url_or_error)
        """
        if not os.path.exists(file_path):
            return (False, f"文件不存在: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            return (False, f"文件过大: {file_size / 1024 / 1024:.1f}MB > 100MB")
        if file_size == 0:
            return (False, "文件为空")

        try:
            if self.service == "file.io":
                return self._upload_fileio(file_path)
            elif self.service == "0x0.st":
                return self._upload_0x0(file_path)
            elif self.service == "tmpfiles":
                return self._upload_tmpfiles(file_path)
            else:
                return (False, f"不支持的服务: {self.service}")
        except urllib.error.URLError as e:
            return (False, f"网络错误: {e}")
        except Exception as e:
            return (False, f"上传失败: {e}")

    def _build_multipart(self, file_path: str,
                         field_name: str = "file") -> Tuple[bytes, str]:
        """构建 multipart/form-data 请求体。"""
        boundary = "----PrankLauncherBoundary9876543210"
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"\r\n'.encode()
        )
        body.extend(
            b"Content-Type: application/octet-stream\r\n\r\n"
        )
        body.extend(file_data)
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        content_type = f"multipart/form-data; boundary={boundary}"
        return bytes(body), content_type

    def _upload_fileio(self, file_path: str) -> Tuple[bool, str]:
        """上传到 file.io (临时文件托管, 单次下载后删除)。"""
        body, ct = self._build_multipart(file_path, "file")
        req = urllib.request.Request(
            "https://file.io",
            data=body,
            headers={"Content-Type": ct},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("success"):
            return (True, data.get("link", ""))
        return (False, data.get("message", "未知错误"))

    def _upload_0x0(self, file_path: str) -> Tuple[bool, str]:
        """上传到 0x0.st (匿名文件托管)。"""
        body, ct = self._build_multipart(file_path, "file")
        req = urllib.request.Request(
            "https://0x0.st",
            data=body,
            headers={"Content-Type": ct},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            url = resp.read().decode("utf-8").strip()
        if url.startswith("http"):
            return (True, url)
        return (False, url)

    def _upload_tmpfiles(self, file_path: str) -> Tuple[bool, str]:
        """上传到 tmpfiles.org (临时文件托管)。"""
        body, ct = self._build_multipart(file_path, "file")
        req = urllib.request.Request(
            "https://tmpfiles.org/api/v1/upload",
            data=body,
            headers={"Content-Type": ct},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        status = data.get("status")
        if status == "success":
            url = data.get("data", {}).get("url", "")
            # tmpfiles 返回预览页面链接，需要转为直链
            url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            return (True, url)
        return (False, str(data))

    @staticmethod
    def generate_qr_text(url: str) -> str:
        """
        生成可用于终端/日志的 QR 提示文本。
        实际二维码图片生成需要 qrcode 库，这里提供 API 链接替代。
        """
        qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(url)}"
        return (
            f"分享链接: {url}\n"
            f"二维码图片: {qr_api}\n"
        )

    @staticmethod
    def get_available_services() -> list:
        """返回支持的服务列表。"""
        return ["file.io", "0x0.st", "tmpfiles"]
