# -*- coding: utf-8 -*-
"""
错误处理模块
提供统一的错误处理和用户友好的错误提示
"""
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


def handle_errors(func):
    """
    错误处理装饰器
    
    Usage:
        @handle_errors
        def my_function(self):
            ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"发生错误: {str(e)}\n\n详细信息:\n{traceback.format_exc()}"
            logger.error(error_msg)
            show_error_dialog(error_msg, "错误")
            return False
    return wrapper


def show_error_dialog(message, title="错误"):
    """
    显示错误对话框
    
    Args:
        message: 错误信息
        title: 对话框标题
    """
    try:
        # 隐藏主窗口
        root = tk.Tk()
        root.withdraw()
        
        # 显示错误消息
        messagebox.showerror(title, message)
        
        # 清理
        root.destroy()
    except Exception as e:
        # 如果Tkinter有问题，直接打印到控制台
        print(f"无法显示错误对话框: {message}")
        print(f"对话框错误: {e}")


def show_warning_dialog(message, title="警告"):
    """
    显示警告对话框
    
    Args:
        message: 警告信息
        title: 对话框标题
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(title, message)
        root.destroy()
    except Exception:
        print(f"警告: {message}")


def show_info_dialog(message, title="信息"):
    """
    显示信息对话框
    
    Args:
        message: 信息内容
        title: 对话框标题
    """
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(f"信息: {message}")


def ask_yes_no(message, title="确认"):
    """
    显示是/否对话框
    
    Args:
        message: 询问信息
        title: 对话框标题
    
    Returns:
        bool: True 表示"是"，False 表示"否"
    """
    try:
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(title, message)
        root.destroy()
        return result
    except Exception:
        print(f"询问: {message}")
        return False


# ============ 自定义异常类 ============


class BuildError(Exception):
    """打包错误基类"""
    
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details
        logger.error(f"BuildError: {message}")
        if details:
            logger.error(f"详细信息: {details}")
    
    def __str__(self):
        if self.details:
            return f"{self.message}\n\n详细信息: {self.details}"
        return self.message


class MissingDependencyError(BuildError):
    """缺少依赖错误"""
    
    def __init__(self, dependency_name, suggestion=None):
        message = f"缺少必要的依赖: {dependency_name}"
        details = suggestion or f"请安装 {dependency_name} 后再试"
        super().__init__(message, details)


class InvalidConfigError(BuildError):
    """配置错误"""
    
    def __init__(self, config_name, reason=None):
        message = f"配置无效: {config_name}"
        details = reason or f"{config_name} 的配置不正确，请检查"
        super().__init__(message, details)


class TemplateNotFoundError(BuildError):
    """模板文件未找到"""
    
    def __init__(self, template_path):
        message = f"模板文件未找到: {template_path}"
        super().__init__(message, "请确保 template 目录存在于程序目录下")


class BuildCancelledError(BuildError):
    """打包被用户取消"""
    
    def __init__(self):
        super().__init__("打包已取消", "用户取消了打包操作")


class PyInstallerError(BuildError):
    """PyInstaller 打包错误"""
    
    def __init__(self, return_code, output=None):
        message = f"PyInstaller 打包失败 (返回码: {return_code})"
        details = output or "请检查控制台输出获取详细信息"
        super().__init__(message, details)


class FileOperationError(BuildError):
    """文件操作错误"""
    
    def __init__(self, operation, file_path, reason=None):
        message = f"文件操作失败: {operation} - {file_path}"
        details = reason or f"无法完成文件操作: {operation}"
        super().__init__(message, details)

