# -*- coding: utf-8 -*-
"""
v4.0 新增模块的单元测试 — Webhook / Payloads
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from template.anti_analysis import AntiAnalysis  # noqa: E402
from template.payloads.audio_prank import AudioPrank  # noqa: E402
from template.payloads.fake_bsod import FakeBSOD  # noqa: E402
from template.payloads.mouse_drift import MouseDrift  # noqa: E402
from template.webhook import WebhookReporter  # noqa: E402


class TestWebhookReporter(unittest.TestCase):
    """WebhookReporter 单元测试。"""

    def test_disabled_when_no_url(self):
        """无 URL 时 enabled 应为 False。"""
        reporter = WebhookReporter(webhook_url="", service_type="custom")
        self.assertFalse(reporter.enabled)

    def test_enabled_when_url_set(self):
        """有 URL 时 enabled 应为 True。"""
        reporter = WebhookReporter(
            webhook_url="https://example.com/webhook",
            service_type="custom",
        )
        self.assertTrue(reporter.enabled)

    def test_report_scan_result_noop_when_disabled(self):
        """禁用状态下 report 不应触发任何网络请求。"""
        reporter = WebhookReporter(webhook_url="")
        # 不应抛出异常
        reporter.report_scan_result(
            target_name="原神",
            target_exe="YuanShen.exe",
            found=True,
            found_path="C:\\Games\\YuanShen.exe",
        )

    def test_collect_env_info(self):
        """环境信息收集不应崩溃。"""
        info = WebhookReporter._collect_env_info()
        self.assertIn("hostname", info)
        self.assertIn("os", info)

    def test_service_types(self):
        """各服务类型常量应正确定义。"""
        self.assertEqual(WebhookReporter.SERVICE_SERVERCHAN, "serverchan")
        self.assertEqual(WebhookReporter.SERVICE_DINGTALK, "dingtalk")
        self.assertEqual(WebhookReporter.SERVICE_FEISHU, "feishu")
        self.assertEqual(WebhookReporter.SERVICE_CUSTOM, "custom")

    @patch("template.webhook.urllib.request.urlopen")
    def test_send_custom_json(self, mock_urlopen):
        """通用 JSON Webhook 应发送正确的 POST 请求。"""
        mock_urlopen.return_value = MagicMock()

        reporter = WebhookReporter(
            webhook_url="https://example.com/hook",
            service_type="custom",
        )
        # 同步发送以便测试
        report = {
            "event": "scan_result",
            "target_name": "测试",
            "found": False,
        }
        reporter._do_send(report)

        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertEqual(req.full_url, "https://example.com/hook")
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["event"], "scan_result")
        self.assertFalse(body["found"])

    @patch("template.webhook.urllib.request.urlopen")
    def test_send_dingtalk_format(self, mock_urlopen):
        """钉钉格式应包含 msgtype=markdown。"""
        mock_urlopen.return_value = MagicMock()

        reporter = WebhookReporter(
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test",
            service_type="dingtalk",
        )
        report = {
            "event": "scan_result",
            "target_name": "原神",
            "target_exe": "YuanShen.exe",
            "found": True,
            "found_path": "C:\\Games\\YuanShen.exe",
            "action": "launched",
            "environment": {"hostname": "test", "os": "Windows 10", "user": "test"},
            "timestamp": "2026-01-01 00:00:00",
        }
        reporter._do_send(report)

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["msgtype"], "markdown")
        self.assertIn("title", body["markdown"])

    @patch("template.webhook.urllib.request.urlopen")
    def test_send_feishu_format(self, mock_urlopen):
        """飞书格式应包含 msg_type=interactive。"""
        mock_urlopen.return_value = MagicMock()

        reporter = WebhookReporter(
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test",
            service_type="feishu",
        )
        report = {
            "event": "scan_result",
            "target_name": "微信",
            "target_exe": "WeChat.exe",
            "found": False,
            "action": "opened_url",
            "environment": {"hostname": "pc", "os": "Windows 11", "user": "user"},
            "timestamp": "2026-01-01 12:00:00",
        }
        reporter._do_send(report)

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["msg_type"], "interactive")
        self.assertIn("card", body)

    def test_network_error_silent(self):
        """网络错误应被静默忽略。"""
        reporter = WebhookReporter(
            webhook_url="https://invalid.local/hook",
            service_type="custom",
        )
        # 同步调用 — 不应抛出异常
        report = {"event": "test", "found": False}
        reporter._do_send(report)  # Should not raise


class TestFakeBSOD(unittest.TestCase):
    """FakeBSOD 单元测试。"""

    def test_default_stop_code(self):
        """默认停止代码应从预设列表中随机选择。"""
        bsod = FakeBSOD()
        self.assertIn(bsod.stop_code, FakeBSOD.STOP_CODES)

    def test_custom_stop_code(self):
        """自定义停止代码应被保留。"""
        bsod = FakeBSOD(stop_code="CUSTOM_ERROR")
        self.assertEqual(bsod.stop_code, "CUSTOM_ERROR")

    def test_minimum_duration(self):
        """持续时间最小值应为 3 秒。"""
        bsod = FakeBSOD(duration=1)
        self.assertEqual(bsod.duration, 3)

    def test_normal_duration(self):
        """正常持续时间应被保留。"""
        bsod = FakeBSOD(duration=10)
        self.assertEqual(bsod.duration, 10)


class TestAudioPrank(unittest.TestCase):
    """AudioPrank 单元测试。"""

    def test_melodies_defined(self):
        """预置旋律应存在。"""
        expected = ["alarm", "error_beep", "ascending", "descending",
                    "random_chaos", "windows_error", "doorbell"]
        for name in expected:
            self.assertIn(name, AudioPrank.MELODIES)

    def test_repeat_minimum(self):
        """重复次数最小值应为 1。"""
        prank = AudioPrank(repeat=0)
        self.assertEqual(prank.repeat, 1)

    def test_default_values(self):
        """默认值应正确。"""
        prank = AudioPrank()
        self.assertEqual(prank.repeat, 1)
        self.assertEqual(prank.delay_between, 0.5)


class TestMouseDrift(unittest.TestCase):
    """MouseDrift 单元测试。"""

    def test_intensity_clamped(self):
        """强度应被限制在 1-10。"""
        drift_low = MouseDrift(intensity=0)
        self.assertEqual(drift_low.intensity, 1)
        drift_high = MouseDrift(intensity=100)
        self.assertEqual(drift_high.intensity, 10)
        drift_normal = MouseDrift(intensity=5)
        self.assertEqual(drift_normal.intensity, 5)

    def test_duration_non_negative(self):
        """持续时间应非负。"""
        drift = MouseDrift(duration=-5)
        self.assertEqual(drift.duration, 0.0)

    def test_interval_minimum(self):
        """间隔最小值应为 0.02。"""
        drift = MouseDrift(interval=0.001)
        self.assertEqual(drift.interval, 0.02)

    def test_not_running_initially(self):
        """初始状态不应为运行中。"""
        drift = MouseDrift()
        self.assertFalse(drift.is_running)

    def test_stop_when_not_started(self):
        """未启动时调用 stop 不应崩溃。"""
        drift = MouseDrift()
        drift.stop()  # Should not raise


class TestAntiAnalysis(unittest.TestCase):
    """AntiAnalysis 单元测试。"""

    def test_default_params(self):
        aa = AntiAnalysis()
        self.assertEqual(aa.min_cpu, 2)
        self.assertEqual(aa.min_ram_gb, 2.0)

    def test_min_cpu_clamped(self):
        aa = AntiAnalysis(min_cpu=0)
        self.assertEqual(aa.min_cpu, 1)

    def test_check_debugger_returns_tuple(self):
        result = AntiAnalysis().check_debugger()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_check_cpu_cores(self):
        aa = AntiAnalysis(min_cpu=1)
        is_sus, detail = aa.check_cpu_cores()
        self.assertFalse(is_sus)  # Real machine has >= 1 core

    def test_check_ram_size(self):
        aa = AntiAnalysis(min_ram_gb=0.5)
        is_sus, detail = aa.check_ram_size()
        self.assertFalse(is_sus)  # Real machine has >= 0.5GB

    def test_check_sandbox_username(self):
        aa = AntiAnalysis()
        is_sus, detail = aa.check_sandbox_username()
        self.assertIsInstance(is_sus, bool)

    def test_check_sandbox_files(self):
        aa = AntiAnalysis()
        is_sus, detail = aa.check_sandbox_files()
        self.assertIsInstance(is_sus, bool)

    def test_get_results_empty_before_run(self):
        aa = AntiAnalysis()
        self.assertEqual(aa.get_results(), {})


if __name__ == "__main__":
    unittest.main()
