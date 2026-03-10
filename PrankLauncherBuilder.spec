# -*- mode: python ; coding: utf-8 -*-
"""
PrankLauncherBuilder - PyInstaller 配置文件
打包配置：生成独立的 Windows 可执行文件

使用方法：
    pyinstaller PrankLauncherBuilder.spec
    或
    python -m PyInstaller PrankLauncherBuilder.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all

# ============ 基础配置 ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'template')
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')
OUTPUT_NAME = 'PrankLauncherBuilder'

# ============ 收集数据文件 ============
def get_data_files():
    """收集需要打包的数据文件"""
    datas = [
        (TEMPLATE_DIR, 'template'),  # 打包template目录到exe同目录
    ]
    
    # 添加 assets 目录（如果存在）
    if os.path.exists(ASSETS_DIR):
        datas.append((ASSETS_DIR, 'assets'))
    
    return datas

# ============ 收集 Tkinter 依赖 ============
tmp_ret = collect_all('tkinter')
datas = tmp_ret[0] + get_data_files()
binaries = tmp_ret[1]
hiddenimports = tmp_ret[2]

# ============ 扩展隐藏导入 ============
additional_hiddenimports = [
    # tkinter 核心模块
    'tkinter',
    'tkinter.ttk',
    'tkinter.tix',
    'tkinter.scrolledtext',
    'tkinter.constants',
    
    # tkinter 对话框和组件
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.colorchooser',
    'tkinter.font',
    'tkinter.dialog',
    
    # Windows API
    'winreg',
    'ctypes',
    'ctypes.wintypes',
    'ctypes.util',
    
    # 系统操作
    'subprocess',
    'threading',
    'shutil',
    'os',
    'sys',
    'io',
    'errno',
    
    # 数据处理
    'json',
    're',
    'struct',
    'copy',
    'tempfile',
    'warnings',
    
    # 文件和路径操作
    'pathlib',
    'glob',
    'fnmatch',
    'linecache',
    'marshal',
    'pickle',
    
    # 时间和日期
    'time',
    'datetime',
    'calendar',
    
    # 随机数
    'random',
    'math',
    
    # 编码
    'codecs',
    'encodings',
    'encodings.*',
    
    # 网络
    'webbrowser',
    'urllib',
    'urllib.parse',
    'urllib.request',
    'urllib.error',
    'http',
    
    # 日志
    'logging',
    'logging.handlers',
    
    # 字符串处理
    'string',
    'collections',
    'itertools',
    'functools',
    'operator',
    
    # 类型提示
    'typing',
    'types',
    
    # Windows 特定模块
    'msvcrt',
    '_thread',
    
    # 其他可能需要的模块
    'platform',
    'abc',
    'contextlib',
]

hiddenimports.extend(additional_hiddenimports)

# ============ 排除不需要的模块 ============
excludes = [
    'pytest',
    'unittest',
    'test',
    'test_*',
    'pydoc',
    'doctest',
    'pdb',
    'pdb_plus',
    'py_compile',
    'venv',
    'pip',
    'pip._vendor',
    'setuptools',
    'setuptools.*',
    'wheel',
    'wheel.*',
    'easy_install',
    'pkg_resources',
    'pywin32',
    'pywin32_*',
    'distutils',
    'distutils.*',
    'lib2to3',
    'lib2to3.*',
]

# ============ 分析阶段 ============
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'builder', 'builder_gui.py')],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# ============ 打包阶段 ============
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=OUTPUT_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    uac_info='管理员权限需要此程序来执行系统级操作',
)
