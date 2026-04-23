# -*- coding: utf-8 -*-
"""
历史记录管理器
用于自动保存和加载生成器的主界面配置，提升用户体验
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, history_file='history.json'):
        self.history_dir = os.path.dirname(os.path.abspath(__file__))
        self.history_file = os.path.join(self.history_dir, history_file)

    def _sanitize_config(self, config: dict) -> dict:
        """移除不应持久化的临时数据与敏感信息。"""
        sanitized = dict(config)
        sanitized.pop("signing_password", None)
        sanitized.pop("splash_image_data", None)
        return sanitized

    def load_history(self) -> dict:
        """加载历史配置"""
        if not os.path.exists(self.history_file):
            return {}

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"无法加载历史配置: {e}")
            return {}

    def save_history(self, config: dict):
        """保存历史配置"""
        try:
            safe_config = self._sanitize_config(config)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"无法保存历史配置: {e}")
