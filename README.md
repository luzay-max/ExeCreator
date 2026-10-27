# ExeCreator · PrankLauncherBuilder

**基于 Python 的 Windows 启动器演示与构建项目**

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)

ExeCreator 仓库中的 **PrankLauncherBuilder** 是一个带图形界面的 Windows 启动器生成器。它提供可配置的加载界面、程序查找、启动流程演示以及 PyInstaller 打包能力，适合在**自己的设备或经过明确授权的测试环境**中学习桌面 UI、Windows 程序打包和模块化 Python 项目结构。

> [!IMPORTANT]
> **使用前请阅读安全与隐私说明。** 项目包含可能误导他人、干扰正常操作或向外部地址传输设备信息的可选功能。请勿将生成的程序冒充真实游戏、官方安装器或系统组件，也不要在未经同意的设备上运行或传播。

## 目录

- [项目概览](#项目概览)
- [功能与限制](#功能与限制)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [构建生成器](#构建生成器)
- [项目结构](#项目结构)
- [测试与开发](#测试与开发)
- [安全与隐私](#安全与隐私)
- [常见问题](#常见问题)
- [后续改进方向](#后续改进方向)
- [参与贡献与许可证](#参与贡献与许可证)

## 项目概览

仓库主要由两个部分构成：

| 部分 | 所在位置 | 作用 |
| --- | --- | --- |
| **Builder（生成器）** | \`builder/\` | 提供图形配置界面，整理模板并调用 PyInstaller |
| **Launcher（运行模板）** | \`template/\` | 展示加载界面，执行目标程序查找、启动或回退流程 |
| **测试** | \`tests/\` | 覆盖构建、扫描、工具模块和部分 v4.0 功能 |

**请区分两个不同的可执行文件：**

- **生成器 EXE**：由根目录的 \`build.bat\` 或 \`PrankLauncherBuilder.spec\` 构建，默认位于 \`dist/PrankLauncherBuilder.exe\`。
- **Launcher EXE**：通过生成器 GUI 的“生成”操作创建，默认写入仓库根目录的 \`output/\`。其文件名由 GUI 配置决定。

这两个过程并不相同；打包生成器并不代表已经生成了 Launcher。

## 功能与限制

| 模块 | 代码现状 | 说明 |
| --- | --- | --- |
| 图形界面 | 已有实现 | 基于 \`customtkinter\`，包含深浅主题、配置项及预览入口 |
| 配置模板 | 已有实现 | 可填写目标程序、窗口标题、图标与应用元数据 |
| 扫描和启动 | 已有实现 | 查找目标程序；找到后尝试启动，未找到时可执行回退流程 |
| EXE 构建 | 已有实现 | 使用 PyInstaller 生成 Windows 可执行文件 |
| 可选签名 | 已有实现 | 需自行准备合法证书与 Windows SignTool |
| 其他演示效果 | 可选实现 | 包含模拟蓝屏、声音与鼠标效果；可能干扰正常操作 |
| 环境检测 | 可选实现 | 代码存在调试器、虚拟机或沙箱检测逻辑；不应作为规避安全审查的手段 |
| Webhook 通知 | 可选实现 | 涉及向配置的外部地址发送事件及部分设备信息；需提前获得知情同意 |
| 第三方文件上传 | 可选实现 | 构建后经用户确认才会尝试上传，服务可用性未经持续验证 |

“已有实现”仅表示对应源代码存在，**不等于已在所有 Windows 版本完成端到端验证**。实际行为还取决于系统配置、第三方服务和运行权限。

## 环境要求

- **操作系统**：建议 Windows 10 / 11（主要运行路径使用 Windows 专用 API，不保证 macOS / Linux 可用）。
- **Python**：建议 3.11 或更高版本；项目的 Ruff / Mypy 配置面向 Python 3.11，依赖锁文件由另一 Python 版本生成，组合兼容性需实测。
- **构建工具**：PyInstaller（由依赖文件声明）。
- **GUI 组件**：\`customtkinter\`（目前在 GUI 源代码中直接引用，但**尚未列入** \`requirements.txt\` 与 \`requirements.lock\`）。

> [!NOTE]
> \`requirements.lock\` 内指定了第三方 PyPI 镜像地址。如需使用默认 PyPI 或企业内部镜像，请先审阅该文件；不要直接假设它可在所有网络环境中使用。

## 快速开始

以下步骤用于**本地查看和开发生成器**。建议先在隔离的测试环境中操作，不要直接运行来源不明的构建产物。

### 1. 克隆代码并创建虚拟环境

在 Windows PowerShell 中执行：

~~~powershell
git clone https://github.com/luzay-max/ExeCreator.git
cd ExeCreator
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
~~~

如果本机没有 \`py -3.11\`，可在确认版本后改用 \`python -m venv .venv\`。PowerShell 的脚本执行策略可能影响虚拟环境激活；也可以直接调用 \`.venv\Scripts\python.exe\`。

### 2. 安装依赖

~~~powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install customtkinter
~~~

目前需要单独安装 \`customtkinter\`，这是仓库依赖声明尚未补齐的问题。若希望按已锁定的 PyInstaller 依赖版本安装，可自行检查并改用 \`requirements.lock\`。

### 3. 打开生成器

~~~powershell
python builder/builder_gui.py
~~~

也可尝试仓库提供的 \`run_builder.bat\`；但它仅检测 Python 或已有打包 EXE，**不会自动补齐全部 GUI 依赖**。

首次体验时，建议仅在授权的测试机器上查看 GUI、切换主题、预览加载效果。不要使用真实公司的名称、商标、图标或签名信息冒充官方软件。

### 4. 理解生成流程

生成器界面提供基础配置、模板预览、构建操作及日志显示。其核心构建逻辑位于 \`builder/builder_core.py\`，默认将生成文件放在 \`output/\`，构建过程中的临时目录为 \`temp_build_env/\`。

某些选项涉及系统交互、数据回传或第三方网络上传。对这些功能进行测试前，请先阅读下方的[安全与隐私](#安全与隐私)章节。

## 构建生成器

如果需要研究生成器本身的 Windows 打包过程，可查看以下仓库文件：

- \`PrankLauncherBuilder.spec\`：PyInstaller 构建配置。
- \`build.bat\`：构建脚本，会清理既有的 \`build_builder/\`、\`dist/\`、\`logs/\` 等目录。
- \`build_portable.bat\`：尝试准备嵌入式 Python 环境的实验性便携打包脚本，**尚不能视为经过验证的一键打包方案**。

**注意：** 当前 \`PrankLauncherBuilder.spec\` 声明了管理员权限请求（\`uac_admin=True\`）；执行或修改构建流程前应检查这项设置是否符合实际需求。请勿通过关闭防病毒软件、绕过系统保护或隐藏真实用途来解决安全告警。

## 项目结构

~~~text
ExeCreator/
├── builder/
│   ├── builder_gui.py             # GUI 入口
│   ├── builder_core.py            # 构建编排与 PyInstaller 调用
│   ├── history_manager.py         # 本地配置历史
│   ├── locale/                    # 国际化资源
│   ├── widgets/                   # 配置面板、日志视图
│   └── utils/                     # 版本、日志、上传等辅助模块
├── template/
│   ├── boot.py                    # Launcher 模板入口
│   ├── fake_ui.py                 # 加载界面
│   ├── launcher_core.py           # 扫描与启动流程
│   ├── scanner/                   # 缓存、注册表、磁盘扫描模块
│   ├── payloads/                  # 可选的交互效果
│   ├── webhook.py                 # 可选事件通知
│   └── anti_analysis.py           # 可选环境检测
├── tests/                         # 自动化测试
├── requirements.txt               # 主要打包依赖
├── requirements.lock              # 锁定版本（含自定义镜像）
├── PrankLauncherBuilder.spec      # 生成器打包配置
├── run_builder.bat                 # Windows 运行脚本
├── build.bat                       # Windows 构建脚本
├── build_portable.bat              # 实验性便携构建脚本
├── pyproject.toml                  # Ruff / Mypy 配置
└── README.md
~~~

## 测试与开发

项目包含 \`tests/\`，但**仓库未给出经过验证的总体测试覆盖率**，因此不应宣称“覆盖率超过 90%”。

安装开发测试工具后，可尝试运行：

~~~powershell
python -m pip install pytest ruff
python -m pytest -q
python -m ruff check builder template tests
~~~

测试命令仅是开发入口说明，本 README 修改**未声称测试已全部通过**。涉及 Windows API、GUI 或外部网络的功能，请在合适的 Windows 测试环境里单独验证；测试外部服务时优先使用模拟对象而非真实上传或回传。

欢迎优先贡献依赖整理、可重复测试、GUI 可访问性、错误提示、日志脱敏和文档改进。

## 安全与隐私

本仓库并非经过安全审计的通用安装器框架。请明确以下事实：

1. **取得同意**：仅在本人设备或得到明确授权的环境中运行。不要伪装成可信厂商、游戏客户端、更新程序或系统警告欺骗他人。
2. **避免干扰操作**：模拟蓝屏、声音和鼠标效果可能造成误解或影响正常使用；不应在真实工作环境或他人设备上试验。
3. **谨慎处理网络回传**：启用 Webhook 后，程序可能发送执行事件、目标程序信息，以及主机名、操作系统、架构、用户名等设备信息。应事先取得同意并确认数据去向；不要收集或发送不必要的个人信息。
4. **留意第三方上传**：代码包含上传到公共文件服务的功能。将构建产物上传到第三方可能使文件脱离你的控制；不要上传包含凭据、个人资料或内部信息的文件。
5. **保护本地配置**：\`builder/history_manager.py\` 会将部分配置保存到 \`builder/history.json\`。虽然代码会排除签名密码和启动图像数据，但历史配置仍可能含有路径、URL 等敏感内容，提交代码前请自行检查。
6. **遵守软件授权**：第三方商标、软件素材、证书和名称必须有合法使用权限。编译产物受到安全产品告警时，应核对原因，不要以规避检测为目标。

如发现数据泄露或其他安全问题，请不要在公开 Issue 中直接粘贴密钥、Webhook 地址、凭据或个人信息。

## 常见问题

<details>
<summary>运行 GUI 提示 No module named 'customtkinter'？</summary>

GUI 源文件依赖 \`customtkinter\`，当前依赖清单尚未声明它。检查正在使用的 Python 虚拟环境，并在同一环境内安装该依赖：

~~~powershell
python -m pip install customtkinter
~~~

</details>

<details>
<summary>为什么根目录的 build.bat 与 GUI 的“生成”输出不一致？</summary>

\`build.bat\` 打包的是**生成器**，使用 \`PrankLauncherBuilder.spec\`，默认输出在 \`dist/\`。GUI 的“生成”功能由 \`BuilderCore\` 实现，默认输出在 \`output/\`。

</details>

<details>
<summary>为什么 Linux 或 macOS 下可能无法运行？</summary>

项目使用 \`winreg\`、\`winsound\`、Windows 特定 API 与 Windows EXE 打包逻辑，目前按 Windows 项目维护。其他平台尚无完整支持承诺。

</details>

<details>
<summary>为什么打包脚本报错或提示缺失资源？</summary>

先核对 Python / PyInstaller 版本、当前工作目录及 \`template/\` 是否齐全。注意部分脚本仍带有旧版本的输出提示，\`build_portable.bat\` 的完整性也需要进一步验证。保留错误日志提交可复现的 Issue，切勿盲目关闭安全防护。

</details>

<details>
<summary>当前可以直接按 MIT 许可证使用吗？</summary>

**不能据此作出判断。** 旧 README 曾标注 MIT，但当前仓库根目录没有 \`LICENSE\` 文件。请等待仓库维护者添加并明确许可证文本；在此之前不要假设已获得 MIT 授权。

</details>

## 后续改进方向

以下是建议，而非已交付功能：

- [ ] 将 GUI、测试和 Windows 打包所需依赖统一声明，并更新锁文件。
- [ ] 增加经过验证的 Windows CI、端到端构建测试及实际运行截图。
- [ ] 修复或重写实验性便携构建流程，避免缺失资源与版本提示混乱。
- [ ] 补充隐私说明、显式授权提示、日志脱敏与默认安全配置。
- [ ] 完善错误处理、配置校验、GUI 无障碍体验与开发文档。
- [ ] 由维护者正式确定开源许可证并添加 \`LICENSE\` 文件。

已有的计划文档可参考 [v4.0 开发计划](v4.0_开发计划.md) 与 [PLAN.md](PLAN.md)，但其中部分想法可能已过时或并未完成，应以当前代码和测试为准。

## 参与贡献与许可证

欢迎通过 [Issues](https://github.com/luzay-max/ExeCreator/issues) 提交 Bug、文档错误或改进建议，并通过 [Pull Requests](https://github.com/luzay-max/ExeCreator/pulls) 贡献可审阅的变更。

提交 PR 时，建议写清楚修改背景、影响范围与验证方法；涉及 GUI 请附真实截图，涉及系统或网络行为请说明授权范围和风险控制措施。

**许可证状态：尚待明确。** 截至本次文档修订，仓库根目录未发现 \`LICENSE\` 文件，因此不再沿用旧 README 中未经文件支持的 MIT 声明。许可证由维护者确定后，请同步更新本节与仓库元信息。

---

如果项目的文档或代码对你的学习有帮助，欢迎通过 Issue 提出建议。优先保证**准确、透明、可复现、安全**，比功能宣传更重要。
