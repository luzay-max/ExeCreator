# -*- coding: utf-8 -*-
"""
历史记录管理器
用于自动保存和加载生成器的主界面配置，提升用户体验
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, history_file='history.json'):
        self.history_dir = os.path.dirname(os.path.abspath(__file__))
        self.history_file = os.path.join(self.history_dir, history_file)
        
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
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"无法保存历史配置: {e}")
