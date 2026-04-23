# -*- coding: utf-8 -*-
"""
版本信息生成器模块
用于生成Windows可执行文件的版本信息
"""
import logging
import os
import re
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class VersionGenerator:
    """
    Windows PE版本信息生成器
    
    生成符合Windows标准的版本信息文件
    """

    # 版本信息模板
    VERSION_TEMPLATE = '''# UTF-8
#
# Version Information
#
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={file_version_tuple},
    prodvers={product_version_tuple},
    # Contains a bitmask that specifies the valid bits 'flags'
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of this file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'{company_name}'),
        StringStruct(u'FileDescription', u'{file_description}'),
        StringStruct(u'FileVersion', u'{file_version}'),
        StringStruct(u'InternalName', u'{internal_name}'),
        StringStruct(u'LegalCopyright', u'{legal_copyright}'),
        StringStruct(u'OriginalFilename', u'{original_filename}'),
        StringStruct(u'ProductName', u'{product_name}'),
        StringStruct(u'ProductVersion', u'{product_version}'),
        StringStruct(u'Comments', u'{comments}'),
        StringStruct(u'LegalTrademarks', u'{legal_trademarks}'),
        StringStruct(u'PrivateBuild', u'{private_build}'),
        StringStruct(u'SpecialBuild', u'{special_build}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
'''

    def __init__(self):
        pass

    def parse_version(self, version_str: str) -> Tuple[int, int, int, int]:
        """
        解析版本字符串
        
        Args:
            version_str: 版本字符串（如 "1.0.0.0"）
        
        Returns:
            Tuple[int, int, int, int]: 版本号元组
        """
        # 验证版本格式
        if not re.match(r'^\d+\.\d+\.\d+\.\d+$', version_str):
            raise ValueError(f"无效的版本格式: {version_str}，应为 X.X.X.X 格式")

        parts = version_str.split('.')
        if len(parts) != 4:
            raise ValueError(f"版本号必须包含4个部分: {version_str}")

        try:
            return tuple(int(p) for p in parts)
        except ValueError:
            raise ValueError(f"版本号必须为数字: {version_str}")

    def generate_version_info(
        self,
        file_version: str = "1.0.0.0",
        product_version: str = "1.0.0.0",
        company_name: str = "",
        file_description: str = "",
        legal_copyright: str = "",
        original_filename: str = "",
        product_name: str = "",
        comments: str = "",
        legal_trademarks: str = "",
        private_build: str = "",
        special_build: str = "",
        internal_name: str = ""
    ) -> str:
        """
        生成版本信息文件内容
        
        Args:
            file_version: 文件版本号
            product_version: 产品版本号
            company_name: 公司名称
            file_description: 文件描述
            legal_copyright: 版权信息
            original_filename: 原始文件名
            product_name: 产品名称
            comments: 备注
            legal_trademarks: 商标
            private_build: 私有构建说明
            special_build: 特殊构建说明
            internal_name: 内部名称
        
        Returns:
            str: 版本信息文件内容
        """
        # 解析版本号
        file_version_tuple = self.parse_version(file_version)
        product_version_tuple = self.parse_version(product_version)

        # 使用内部名称或产品名称
        internal_name = internal_name or product_name

        # 格式化版本字符串（去掉最后一个数字）
        file_ver_str = '.'.join(str(v) for v in file_version_tuple[:-1])
        product_ver_str = '.'.join(str(v) for v in product_version_tuple[:-1])

        # 填充模板
        content = self.VERSION_TEMPLATE.format(
            file_version_tuple=file_version_tuple,
            product_version_tuple=product_version_tuple,
            company_name=company_name or '',
            file_description=file_description or '',
            file_version=file_ver_str,
            internal_name=internal_name,
            legal_copyright=legal_copyright or '',
            original_filename=original_filename or '',
            product_name=product_name or '',
            product_version=product_ver_str,
            comments=comments or '',
            legal_trademarks=legal_trademarks or '',
            private_build=private_build or '',
            special_build=special_build or ''
        )

        logger.info(f"生成版本信息文件: file_version={file_version}, product_version={product_version}")

        return content

    def save_version_info(
        self,
        file_path: str,
        **kwargs
    ) -> bool:
        """
        生成并保存版本信息文件
        
        Args:
            file_path: 输出文件路径
            **kwargs: 版本信息参数
        
        Returns:
            bool: 是否成功
        """
        try:
            content = self.generate_version_info(**kwargs)

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"版本信息已保存到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"保存版本信息失败: {e}")
            return False

    @staticmethod
    def create_default_config(
        output_name: str,
        version: str = "1.0.0.0"
    ) -> Dict[str, Any]:
        """
        创建默认配置
        
        Args:
            output_name: 输出文件名
            version: 版本号
        
        Returns:
            Dict: 配置字典
        """
        name_without_ext = os.path.splitext(output_name)[0]

        return {
            'file_version': version,
            'product_version': version,
            'company_name': 'Microsoft Corporation',
            'file_description': 'Game Client',
            'legal_copyright': f'© {name_without_ext}. All rights reserved.',
            'original_filename': output_name,
            'product_name': name_without_ext,
            'internal_name': name_without_ext,
        }

    @staticmethod
    def format_size_for_display(size_bytes: int) -> str:
        """
        格式化文件大小显示
        
        Args:
            size_bytes: 字节数
        
        Returns:
            str: 格式化后的大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.2f} MB"


def generate_version_info(**kwargs) -> str:
    """
    便捷函数：生成版本信息
    
    Returns:
        str: 版本信息文件内容
    """
    generator = VersionGenerator()
    return generator.generate_version_info(**kwargs)


def save_version_info(file_path: str, **kwargs) -> bool:
    """
    便捷函数：保存版本信息
    
    Args:
        file_path: 输出文件路径
        **kwargs: 版本信息参数
    
    Returns:
        bool: 是否成功
    """
    generator = VersionGenerator()
    return generator.save_version_info(file_path, **kwargs)






