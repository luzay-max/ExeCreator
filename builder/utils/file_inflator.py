# -*- coding: utf-8 -*-
"""
文件膨胀模块
提供文件大小膨胀功能，用于增加exe文件的真实感
"""
import logging
import os
from typing import Optional

from builder.utils.errors import FileOperationError

logger = logging.getLogger(__name__)


class FileInflator:
    """
    文件膨胀器
    
    通过向文件末尾追加数据来增加文件大小
    """

    # 常用大小单位
    SIZE_UNITS = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
    }

    def __init__(self):
        self.current_size = 0
        self.target_size = 0
        self.inflate_ratio: float = 0.0

    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
        
        Returns:
            int: 文件大小（字节）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        return os.path.getsize(file_path)

    def parse_size(self, size_str: str) -> int:
        """
        解析大小字符串
        
        Args:
            size_str: 大小字符串（如 "10MB", "5KB", "1024"）
        
        Returns:
            int: 大小（字节）
        """
        size_str = size_str.strip()

        # 如果没有单位，默认是 MB
        if not any(size_str.endswith(unit) for unit in self.SIZE_UNITS):
            try:
                return int(float(size_str) * self.SIZE_UNITS['MB'])
            except ValueError:
                raise ValueError(f"无法解析大小字符串: {size_str}")

        # 解析带单位的大小（按单位长度降序匹配，避免 B 先匹配 MB/KB/GB）
        for unit, multiplier in sorted(self.SIZE_UNITS.items(), key=lambda x: len(x[0]), reverse=True):
            if size_str.upper().endswith(unit.upper()):
                try:
                    value = float(size_str[:-len(unit)])
                    return int(value * multiplier)
                except ValueError:
                    raise ValueError(f"无法解析大小字符串: {size_str}")

        raise ValueError(f"无法解析大小字符串: {size_str}")

    def inflate_file(
        self,
        file_path: str,
        target_size_mb: float,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        膨胀文件到指定大小
        
        Args:
            file_path: 文件路径
            target_size_mb: 目标大小（MB）
            progress_callback: 进度回调函数 (current_bytes, total_bytes)
        
        Returns:
            dict: 膨胀结果信息
        """
        if not os.path.exists(file_path):
            raise FileOperationError("读取", file_path, "文件不存在")

        current_size = self.get_file_size(file_path)
        target_bytes = int(target_size_mb * 1024 * 1024)

        # 如果当前文件已经大于等于目标大小
        if current_size >= target_bytes:
            logger.info(f"当前文件大小 ({current_size} 字节) 已超过目标大小，跳过膨胀")
            return {
                'success': True,
                'original_size': current_size,
                'final_size': current_size,
                'inflated_bytes': 0,
                'message': '文件已足够大，无需膨胀'
            }

        # 计算需要填充的字节数
        needed_bytes = target_bytes - current_size

        logger.info(f"开始文件膨胀: {file_path}")
        logger.info(f"当前大小: {current_size / 1024 / 1024:.2f} MB")
        logger.info(f"目标大小: {target_size_mb:.2f} MB")
        logger.info(f"需要填充: {needed_bytes / 1024 / 1024:.2f} MB")

        try:
            # 打开文件以追加模式
            with open(file_path, 'ab') as f:
                # 分块写入，避免内存占用过大
                chunk_size = 1024 * 1024  # 1MB
                written_bytes = 0

                while needed_bytes > 0:
                    write_size = min(chunk_size, needed_bytes)

                    # 写入零字节（比随机字节更节省空间）
                    f.write(b'\0' * write_size)
                    written_bytes += write_size
                    needed_bytes -= write_size

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(written_bytes, target_bytes - current_size)

                self.current_size = current_size + written_bytes
                self.target_size = target_bytes
                self.inflate_ratio = self.current_size / current_size if current_size > 0 else 1.0

            logger.info(f"文件膨胀完成! 最终大小: {self.current_size / 1024 / 1024:.2f} MB")

            return {
                'success': True,
                'original_size': current_size,
                'final_size': self.current_size,
                'inflated_bytes': written_bytes,
                'message': '文件膨胀成功'
            }

        except Exception as e:
            logger.error(f"文件膨胀失败: {e}")
            raise FileOperationError("写入", file_path, str(e))

    def deflate_file(self, file_path: str) -> int:
        """
        移除文件末尾的膨胀数据（如果知道原始大小）
        注意：此功能需要记录原始大小
        
        Args:
            file_path: 文件路径
        
        Returns:
            int: 移除的字节数
        """
        # TODO: 实现原始大小追溯功能
        logger.warning("deflate_file 功能尚未实现，需要配合原始大小记录")
        return 0

    def get_inflate_info(self) -> dict:
        """
        获取最近一次膨胀操作的信息
        
        Returns:
            dict: 膨胀信息
        """
        return {
            'current_size': self.current_size,
            'target_size': self.target_size,
            'inflate_ratio': self.inflate_ratio
        }

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        格式化文件大小为人类可读格式
        
        Args:
            size_bytes: 大小（字节）
        
        Returns:
            str: 格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024

        return f"{size_bytes:.2f} TB"


def inflate_file(
    file_path: str,
    target_size_mb: float,
    progress_callback: Optional[callable] = None
) -> dict:
    """
    便捷函数：膨胀文件到指定大小
    
    Args:
        file_path: 文件路径
        target_size_mb: 目标大小（MB）
        progress_callback: 进度回调函数
    
    Returns:
        dict: 膨胀结果
    """
    inflator = FileInflator()
    return inflator.inflate_file(file_path, target_size_mb, progress_callback)






