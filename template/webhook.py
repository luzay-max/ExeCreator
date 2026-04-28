# -*- coding: utf-8 -*-
"""
Webhook 战报回传模块 — v4.0 新增

支持的推送服务：
- Server酱 (https://sct.ftqq.com)
- 钉钉群机器人 (DingTalk Bot)
- 飞书群机器人 (Feishu/Lark Bot)
- 通用 JSON Webhook (自定义 URL)

设计原则：
- 仅使用标准库 (urllib)，不引入 requests 等第三方依赖。
- 所有网络操作为非阻塞（启动独立线程），不影响主程序流程。
- 静默失败，绝不因为推送异常导致 Launcher 崩溃或行为异常。
"""
import datetime
import json
import os
import platform
import threading
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class WebhookReporter:
    """异步 Webhook 回传器。"""

    # 支持的服务类型
    SERVICE_SERVERCHAN = "serverchan"
    SERVICE_DINGTALK = "dingtalk"
    SERVICE_FEISHU = "feishu"
    SERVICE_CUSTOM = "custom"

    def __init__(
        self,
        webhook_url: str = "",
        service_type: str = "custom",
        timeout: int = 10,
    ) -> None:
        self.webhook_url: str = webhook_url.strip()
        self.service_type: str = service_type.lower().strip()
        self.timeout: int = timeout
        self.enabled: bool = bool(self.webhook_url)

    # ------------------------------------------------------------------ #
    #  公共 API
    # ------------------------------------------------------------------ #

    def report_scan_result(
        self,
        target_name: str,
        target_exe: str,
        found: bool,
        found_path: Optional[str] = None,
        action: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        报告扫描结果。在独立线程中发送，不阻塞调用方。

        :param target_name: 目标显示名称（如"原神"）
        :param target_exe:  目标进程名（如"YuanShen.exe"）
        :param found:       是否找到目标
        :param found_path:  找到的路径（仅 found=True 时有效）
        :param action:      后续执行的动作描述
        :param extra:       额外信息字典
        """
        if not self.enabled:
            return

        # 收集环境信息
        env_info = self._collect_env_info()

        # 构建统一的报告数据
        report: Dict[str, Any] = {
            "event": "scan_result",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_name": target_name,
            "target_exe": target_exe,
            "found": found,
            "found_path": found_path or "",
            "action": action,
            "environment": env_info,
        }
        if extra:
            report["extra"] = extra

        # 异步发送
        self._send_async(report)

    def report_event(self, event_name: str, message: str, **kwargs: Any) -> None:
        """
        报告自定义事件。

        :param event_name: 事件名称
        :param message:    事件消息
        :param kwargs:     额外键值对
        """
        if not self.enabled:
            return

        report: Dict[str, Any] = {
            "event": event_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message,
        }
        report.update(kwargs)

        self._send_async(report)

    # ------------------------------------------------------------------ #
    #  内部实现
    # ------------------------------------------------------------------ #

    @staticmethod
    def _collect_env_info() -> Dict[str, str]:
        """收集当前运行环境信息（脱敏）。"""
        try:
            return {
                "hostname": platform.node(),
                "os": f"{platform.system()} {platform.release()}",
                "arch": platform.machine(),
                "user": os.getenv("USERNAME", os.getenv("USER", "unknown")),
            }
        except Exception:
            return {"hostname": "unknown", "os": "unknown"}

    def _send_async(self, report: Dict[str, Any]) -> None:
        """在后台线程发送，静默处理所有异常。"""
        t = threading.Thread(
            target=self._do_send,
            args=(report,),
            daemon=True,
        )
        t.start()

    def _do_send(self, report: Dict[str, Any]) -> None:
        """根据 service_type 分发到对应的格式化方法，并执行 HTTP POST。"""
        try:
            if self.service_type == self.SERVICE_SERVERCHAN:
                self._send_serverchan(report)
            elif self.service_type == self.SERVICE_DINGTALK:
                self._send_dingtalk(report)
            elif self.service_type == self.SERVICE_FEISHU:
                self._send_feishu(report)
            else:
                self._send_custom(report)
        except Exception:
            # 静默忽略所有异常，绝不影响主程序
            pass

    # ---------- Server酱 ---------- #

    def _send_serverchan(self, report: Dict[str, Any]) -> None:
        """
        Server酱格式：GET/POST 到 https://sctapi.ftqq.com/{SENDKEY}.send
        参数: title, desp
        """
        found = report.get("found", False)
        target = report.get("target_name", "未知")
        status_emoji = "✅" if found else "❌"

        title = f"{status_emoji} {target} 扫描报告"
        lines = [
            "## 扫描结果",
            f"- **目标**: {target} (`{report.get('target_exe', '')}`)",
            f"- **状态**: {'已找到' if found else '未找到'}",
        ]
        if found:
            lines.append(f"- **路径**: `{report.get('found_path', '')}`")
        if report.get("action"):
            lines.append(f"- **执行动作**: {report['action']}")

        env = report.get("environment", {})
        if env:
            lines.append("\n## 环境信息")
            lines.append(f"- **主机**: {env.get('hostname', '?')}")
            lines.append(f"- **系统**: {env.get('os', '?')}")
            lines.append(f"- **用户**: {env.get('user', '?')}")

        lines.append(f"\n---\n*{report.get('timestamp', '')}*")
        desp = "\n".join(lines)

        # Server酱 API: POST form-urlencoded
        data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
        req = urllib.request.Request(self.webhook_url, data=data)
        urllib.request.urlopen(req, timeout=self.timeout)

    # ---------- 钉钉机器人 ---------- #

    def _send_dingtalk(self, report: Dict[str, Any]) -> None:
        """
        钉钉机器人格式：POST JSON
        {"msgtype": "markdown", "markdown": {"title": "...", "text": "..."}}
        """
        found = report.get("found", False)
        target = report.get("target_name", "未知")
        status_emoji = "✅" if found else "❌"

        title = f"{status_emoji} {target} 扫描报告"
        text_lines = [
            f"### {title}",
            f"- **目标**: {target} (`{report.get('target_exe', '')}`)",
            f"- **状态**: {'已找到' if found else '未找到'}",
        ]
        if found:
            text_lines.append(f"- **路径**: `{report.get('found_path', '')}`")
        if report.get("action"):
            text_lines.append(f"- **动作**: {report['action']}")

        env = report.get("environment", {})
        if env:
            text_lines.append(f"- **主机**: {env.get('hostname', '?')} ({env.get('os', '?')})")

        text_lines.append(f"\n> {report.get('timestamp', '')}")

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": "\n\n".join(text_lines),
            },
        }
        self._post_json(payload)

    # ---------- 飞书机器人 ---------- #

    def _send_feishu(self, report: Dict[str, Any]) -> None:
        """
        飞书机器人格式：POST JSON
        {"msg_type": "interactive", "card": {...}}
        """
        found = report.get("found", False)
        target = report.get("target_name", "未知")
        status = "✅ 已找到" if found else "❌ 未找到"

        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**目标**: {target} (`{report.get('target_exe', '')}`)\n"
                        f"**状态**: {status}\n"
                    ),
                },
            },
        ]

        if found and report.get("found_path"):
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**路径**: `{report['found_path']}`",
                },
            })

        if report.get("action"):
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**执行动作**: {report['action']}",
                },
            })

        env = report.get("environment", {})
        if env:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**主机**: {env.get('hostname', '?')}\n"
                        f"**系统**: {env.get('os', '?')}\n"
                        f"**用户**: {env.get('user', '?')}"
                    ),
                },
            })

        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": report.get("timestamp", ""),
                }
            ],
        })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{'✅' if found else '❌'} {target} 扫描报告",
                    },
                    "template": "green" if found else "red",
                },
                "elements": elements,
            },
        }
        self._post_json(payload)

    # ---------- 通用 JSON ---------- #

    def _send_custom(self, report: Dict[str, Any]) -> None:
        """通用 JSON Webhook：直接 POST 完整报告数据。"""
        self._post_json(report)

    # ---------- HTTP 工具 ---------- #

    def _post_json(self, payload: Dict[str, Any]) -> None:
        """通用 JSON POST 请求。"""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        urllib.request.urlopen(req, timeout=self.timeout)
