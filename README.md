# PrankLauncherBuilder (恶搞启动器生成工具) 🎮🎭

![Version](https://img.shields.io/badge/version-v3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**PrankLauncherBuilder** 是一个功能强大、高度定制化的“恶搞启动器”生成工具。它可以将一个看似正常的应用程序（如游戏启动器：原神、崩坏：星穹铁道、英雄联盟等）伪装成恶搞程序。

当受害者运行该启动器时，程序会展示逼真的“正在加载资源...”进度条，并在后台开启**多线程并发扫描**寻找真实的游戏程序。如果找到真实游戏，则静默启动它以掩人耳目；如果未找到，则在伪装界面结束后，自动跳转到您预设的恶搞网页（例如 Rickroll 或其他搞怪网站）。

> ⚠️ **声明**：本项目仅供学习交流与好友间的无害恶搞使用。请勿用于任何非法、破坏性或侵犯他人隐私的用途。

---

## ✨ 核心特性 (Features)

### 1. 🎨 现代化的可视化生成器 (Builder GUI)
- 提供直观的 `tkinter` 图形界面，支持一键配置恶搞目标、伪装名称、自定义图标（`.ico`）及启动图（Splash Screen）。
- **内置丰富模板**：下拉菜单一键填充热门游戏/软件的预设配置（原神、微信、Steam 等）。
- **历史记录记忆**：自动保存上一次的配置，无需重复输入。

### 2. 🚀 高性能隐蔽扫描引擎 (Stealth Scanner)
- **多级扫描策略**：缓存命中（极速） -> 注册表扫描 -> 常用路径 -> 多线程全盘扫描。
- **并发与中断机制**：基于 `ThreadPoolExecutor` 和 `threading.Event`，一旦在某个分区发现目标，立即停止全盘扫描，极大地降低了资源占用和延迟。
- **无缝衔接**：目标程序找到后，伪装界面自动关闭并拉起真实程序，受害者毫无察觉。

### 3. 🛡️ 深度防查杀与免杀 (Anti-Analysis & Evasion)
- **文件体积膨胀 (File Inflation)**：通过向文件尾部注入空数据（0字节），将原本几 MB 的 EXE 膨胀至数百 MB，增加真实感并绕过部分云沙箱的体积限制。
- **代码混淆 (Obfuscation)**：在打包前自动对 Python 源码进行变量名随机化和短字符串编码，增加静态逆向难度。
- **Authenticode 签名**：支持调用 Windows `SignTool` 为生成的 EXE 注入 PFX 证书签名，大幅降低 Windows SmartScreen 和杀毒软件的拦截率。

### 4. 🔄 无痕自我替换 (Self-Destruction / Update)
- 摒弃了传统的 `.bat` 脚本残留问题。
- 采用 `atexit` 钩子配合 `os.replace` 实现原子级替换，并以 `MoveFileExW`（延迟到重启后删除）作为系统级保底方案，确保启动器在更新或自毁时不留痕迹。

### 5. 🌐 国际化与工程规范 (I18n & Code Quality)
- 支持多语言切换（简体中文、English）。
- 严格遵循现代 Python 工程标准：通过 `mypy` 类型检查，`ruff` 代码规范格式化，以及 `pytest` 全面覆盖核心逻辑的单元测试。

---

## 🛠️ 快速开始 (Quick Start)

### 环境要求
- Windows 操作系统
- Python 3.8 及以上版本

### 1. 克隆与安装依赖
```bash
git clone https://github.com/yourusername/PrankLauncherBuilder.git
cd PrankLauncherBuilder
pip install -r requirements.lock
```

### 2. 运行生成器
```bash
python builder/builder_gui.py
```

### 3. 生成与使用
1. 在弹出的图形界面中，选择或输入**目标程序**（如 `YuanShen.exe`）。
2. 配置**失败跳转网址**（恶搞网址）。
3. 配置**伪装设置**（输出文件名、图标、目标文件膨胀大小等）。
4. 点击 **“生成启动器”**。
5. 生成的独立 `.exe` 文件将输出在 `output/` 目录下。将该 EXE 发送给您的好友即可开始恶搞！

---

## 📁 项目结构 (Project Structure)

```text
PrankLauncherBuilder/
├── builder/                    # 生成器 (Builder) 核心代码
│   ├── builder_core.py         # 打包核心逻辑 (PyInstaller 调度、签名、膨胀)
│   ├── builder_gui.py          # 图形界面主入口
│   ├── history_manager.py      # 配置持久化管理
│   ├── locale/                 # 多语言翻译文件 (i18n)
│   ├── utils/                  # 构建工具 (混淆器、文件膨胀、版本生成等)
│   └── widgets/                # UI 组件库 (配置面板、日志查看器)
├── template/                   # 启动器 (Launcher) 模板代码 (打包时被动态注入)
│   ├── boot.py                 # 启动器入口文件
│   ├── fake_ui.py              # 伪装加载进度条界面
│   ├── launcher_core.py        # 扫描、执行与替换核心逻辑
│   └── scanner/                # 多级扫描器策略 (缓存、注册表、磁盘并发扫描)
├── tests/                      # 单元测试 (Pytest)
├── output/                     # 默认的 EXE 生成目录
├── requirements.lock           # 锁定的 Python 依赖版本
└── pyproject.toml              # Ruff、Mypy、Pytest 配置
```

---

## 🔮 未来规划 (Roadmap v4.0)

本项目正向 **v4.0** 演进，计划进一步提升隐蔽性与互动性：
- **底层引擎重构**：计划使用 Rust/C++ 重写 Launcher 核心，剥离 Python 运行时，将单文件体积压缩至 2MB 以内。
- **Webhook 战报回传**：受害者触发恶搞（如拉起浏览器）时，向恶搞者发送钉钉/飞书推送。
- **深度环境对抗**：增加反沙箱（检测 CPU/内存）、反调试机制。
- 更多详细规划请参阅 [v4.0_开发计划.md](./v4.0_开发计划.md) 与 [优化方案.md](./优化方案.md)。

---

## 🤝 贡献与支持 (Contributing)

欢迎提交 Issue 和 Pull Request！
如果您觉得这个工具有趣，请给本项目点个 ⭐️ **Star**，您的支持是我更新的最大动力。

## 📄 开源协议 (License)

本项目基于 [MIT License](LICENSE) 许可开源。
