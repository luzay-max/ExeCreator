# -*- coding: utf-8 -*-
"""
constants.py — 全局常量定义

将硬编码的字符串、日志格式、版本号等集中管理。
"""

# ============ 版本信息 ============
VERSION = "3.1.0"
APP_NAME = "PrankLauncherBuilder"
APP_TITLE = f"恶搞启动器生成工具 v{VERSION}"

# ============ 日志格式 ============
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============ 默认配置 ============
DEFAULT_CONFIG = {
    "target_exe": "YuanShen.exe",
    "target_name": "原神",
    "fallback_url": "https://ys.mihoyo.com",
    "error_message": "无法定位程序输入点于动态链接库 Kernel32.dll。",
    "window_title": "正在加载游戏资源...",
    "output_name": "植物大战僵尸3.exe",
    "target_size_mb": 10,
    "meta_company": "Microsoft Corporation",
    "meta_desc": "Game Client",
    "meta_copyright": "© Microsoft Corporation. All rights reserved.",
    "meta_version": "1.0.0.1",
}

# ============ 构建流程消息 ============
MSG_BUILD_START = "开始构建恶搞启动器..."
MSG_BUILD_DONE = "🎉 全部完成！"
MSG_MERGE_START = "正在合并代码模块..."
MSG_MERGE_DONE = "代码合并完成"
MSG_PACK_START = "正在打包 (这可能需要几分钟)..."
MSG_INFLATE_START = "正在执行文件膨胀..."
MSG_CLEAN = "清理临时文件..."
MSG_VERSION_DONE = "版本信息已生成"
MSG_VERSION_FAIL = "警告: 生成版本信息失败，将跳过元数据伪装"
MSG_NO_PYINSTALLER = "未检测到 PyInstaller，请安装。"

# ============ 扫描器消息 ============
MSG_SCAN_START = "开始寻找 {name} ({exe})..."
MSG_SCAN_CACHE = "检查本地缓存记录..."
MSG_SCAN_REGISTRY = "正在扫描系统注册表..."
MSG_SCAN_COMMON = "扫描常用安装目录..."
MSG_SCAN_FULL = "开始全盘深度扫描..."
MSG_SCAN_FOUND = "发现目标: {path}"
MSG_SCAN_NOT_FOUND = "未找到目标程序"

# ============ 伪装 UI 默认任务文本 ============
FAKE_LOADING_TASKS = [
    "正在校验本地资源完整性...",
    "连接服务器安全通道...",
    "下载更新清单文件...",
    "初始化游戏引擎环境...",
    "加载材质与纹理资源...",
    "检查反作弊系统状态...",
    "同步玩家云端配置...",
    "等待图形驱动响应...",
]

# ============ 文件路径 ============
CACHE_DIR_NAME = "FakeLauncherCache"
CACHE_FILE_NAME = "known_paths.json"
HISTORY_FILE_NAME = "history.json"
