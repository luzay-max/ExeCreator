# -*- coding: utf-8 -*-
"""
日志工具模块
提供格式化日志输出功能
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# 默认日志格式
DEFAULT_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class Logger:
    """日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Logger._initialized:
            self.logger = None
            self.log_file = None
            self.console_enabled = True
            self.file_enabled = False
            Logger._initialized = True
    
    def setup(self, name='PrankBuilder', level=logging.INFO, 
              console=True, file_path=None, log_format=None):
        """
        初始化日志系统
        
        Args:
            name: 日志名称
            level: 日志级别
            console: 是否输出到控制台
            file_path: 日志文件路径（可选）
            log_format: 日志格式
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置格式
        formatter = logging.Formatter(
            log_format or DEFAULT_FORMAT,
            datefmt=DATE_FORMAT
        )
        
        # 控制台处理器
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if file_path:
            self.log_file = file_path
            # 确保目录存在
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            self.logger.addHandler(file_handler)
            self.file_enabled = True
        
        self.console_enabled = console
    
    def debug(self, message):
        """调试日志"""
        if self.logger:
            self.logger.debug(message)
    
    def info(self, message):
        """信息日志"""
        if self.logger:
            self.logger.info(message)
    
    def warning(self, message):
        """警告日志"""
        if self.logger:
            self.logger.warning(message)
    
    def error(self, message):
        """错误日志"""
        if self.logger:
            self.logger.error(message)
    
    def critical(self, message):
        """严重错误日志"""
        if self.logger:
            self.logger.critical(message)
    
    def exception(self, message, exc_info=True):
        """异常日志"""
        if self.logger:
            self.logger.exception(message)
    
    def log_build_step(self, step_num, total_steps, message):
        """记录构建步骤"""
        self.info(f"[{step_num}/{total_steps}] {message}")
    
    def get_log_content(self):
        """获取日志文件内容"""
        if self.log_file and os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
        return None
    
    def clear_log(self):
        """清除日志文件"""
        if self.log_file and os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write('')
            except Exception:
                pass


# 全局日志实例
_log_instance = None


def get_logger() -> Logger:
    """获取全局日志实例"""
    global _log_instance
    if _log_instance is None:
        _log_instance = Logger()
    return _log_instance


def setup_logger(name='PrankBuilder', level=logging.INFO, 
                 console=True, file_path=None):
    """快速设置日志"""
    logger = get_logger()
    logger.setup(name, level, console, file_path)
    return logger






