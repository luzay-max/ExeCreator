# PrankLauncherBuilder 完全独立化改造计划

**版本**: 1.0  
**创建日期**: 2026-02-24  
**项目状态**: 规划阶段  
**预计完成时间**: 10个工作日  

---

## 📋 项目概述

### 背景
当前 PrankLauncherBuilder 恶搞启动器生成工具虽然功能完善，但在部署和使用上存在一定门槛：
- 生成器需要系统安装 Python 和 PyInstaller
- 非技术用户配置环境困难
- 无法在纯净 Windows 环境下直接运行
- 分发和部署过程复杂

### 目标
将恶搞生成器改造为**完全独立的 EXE 文件**，实现：
1. **生成器完全独立**：单 EXE 文件，无外部依赖，双击即用
2. **跨环境运行**：支持 Windows 10/11 所有版本，32/64位系统
3. **生成的恶搞 EXE 独立**：输出文件同样无需 Python 环境
4. **部署简便**：用户只需下载单个文件或压缩包

### 成功标准
- 生成器文件体积 ≤ 50MB
- 启动时间 ≤ 5秒（首次），≤ 2秒（后续）
- 支持 Windows 10/11 全版本
- 零外部依赖，无需安装运行环境
- 恶搞 EXE 生成成功率 ≥ 99%

---

## 🏗️ 技术架构设计

### 整体架构
```
用户层
  ↓
双击 PrankLauncherBuilder_Standalone.exe
  ↓
应用层：自解压运行时 + 嵌入式 Python 3.11 + 所有依赖
  ↓
核心层：Tkinter GUI + 配置逻辑 + PyInstaller 调用引擎
  ↓
生成层：动态模板生成 → PyInstaller 打包 → 文件膨胀优化
  ↓
输出层：完全独立的恶搞 EXE（单文件，无依赖）
```

### 关键技术方案

#### 1. 生成器独立化
- **嵌入式 Python**: Python 3.11.9 embeddable package (8MB)
- **依赖捆绑**: pefile、pywin32、PyInstaller 打包进 EXE
- **运行时自解压**: EXE 启动时释放运行时到临时目录
- **延迟加载**: 减少启动时间，按需加载模块

#### 2. 恶搞 EXE 生成优化
- **模板预编译**: 将模板文件预编译为字节码
- **依赖精简**: 只打包必需的 Python 标准库模块
- **UPX 压缩**: 使用 UPX 压缩 EXE，减少文件体积
- **元数据伪装**: 集成版本信息、图标、公司名称伪装

#### 3. 兼容性保障
- **Windows API 最小化**: 仅使用 Windows 7+ 兼容的 API
- **无 .NET 依赖**: 避免需要安装 .NET Framework
- **无 VC++ 运行时**: 使用纯 Python 实现
- **Unicode 支持**: 完整支持中文路径和特殊字符

---

## 📅 实施计划

### 阶段一：环境准备与基础改造 (2天)
- [ ] **步骤 1.1**: 下载并配置 Python 3.11.9 embeddable package
- [ ] **步骤 1.2**: 创建独立的 `standalone_entry.py` 入口点
- [ ] **步骤 1.3**: 修改依赖导入逻辑，支持嵌入式环境检测
- [ ] **步骤 1.4**: 优化资源加载路径 (`sys._MEIPASS` 兼容)
- [ ] **步骤 1.5**: 创建独立的 spec 文件 `standalone.spec`

### 阶段二：完全独立打包实现 (3天)
- [ ] **步骤 2.1**: 设计 PyInstaller spec 配置，包含所有依赖
- [ ] **步骤 2.2**: 实现运行时自解压和初始化逻辑
- [ ] **步骤 2.3**: 集成 pefile、pywin32 到打包配置
- [ ] **步骤 2.4**: 测试独立 EXE 在纯净 Windows 环境运行
- [ ] **步骤 2.5**: 优化启动速度，实现延迟加载机制

### 阶段三：恶搞 EXE 生成优化 (2天)
- [ ] **步骤 3.1**: 分析并精简生成的恶搞 EXE 依赖项
- [ ] **步骤 3.2**: 实现模板预编译和缓存机制
- [ ] **步骤 3.3**: 优化 PyInstaller 打包参数，减少体积
- [ ] **步骤 3.4**: 集成 UPX 压缩到打包流程
- [ ] **步骤 3.5**: 测试生成的恶搞 EXE 在目标环境运行

### 阶段四：兼容性测试与优化 (2天)
- [ ] **步骤 4.1**: 在多版本 Windows 环境测试 (Win10/11)
- [ ] **步骤 4.2**: 测试 32 位和 64 位系统兼容性
- [ ] **步骤 4.3**: 验证杀毒软件兼容性，优化特征
- [ ] **步骤 4.4**: 测试企业环境限制 (AppLocker, 软件限制策略)
- [ ] **步骤 4.5**: 优化错误处理和用户提示

### 阶段五：部署与文档 (1天)
- [ ] **步骤 5.1**: 创建一键打包脚本 `build_standalone.bat`
- [ ] **步骤 5.2**: 编写详细使用文档和故障排除指南
- [ ] **步骤 5.3**: 创建版本发布检查清单
- [ ] **步骤 5.4**: 测试完整工作流程并录制演示视频

---

## 🔧 详细技术实现

### 1. 独立入口点代码
```python
# standalone_entry.py
import sys
import os

def setup_embedded_environment():
    """设置嵌入式 Python 环境"""
    if getattr(sys, 'frozen', False):
        meipass = sys._MEIPASS
        site_packages = os.path.join(meipass, 'python_embedded', 'Lib', 'site-packages')
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
    
    embedded_pyinstaller = find_embedded_pyinstaller()
    if embedded_pyinstaller:
        os.environ['PYINSTALLER_PATH'] = embedded_pyinstaller

def main():
    setup_embedded_environment()
    from builder.builder_gui import BuilderGUI
    app = BuilderGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
```

### 2. 独立化 spec 配置
```python
# standalone.spec 关键配置
datas += [
    ('python_embedded', 'python_embedded'),
    ('template', 'template'),
    ('assets', 'assets'),
]

hiddenimports += [
    'pefile',
    'pefile.pefile',
    'win32api',
    'win32process',
    'win32con',
    'winerror',
    'pywintypes',
]

# PyInstaller 配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PrankLauncherBuilder_Standalone',
    debug=False,
    strip=False,
    upx=True,           # 启用 UPX 压缩
    console=False,      # 无控制台窗口
    uac_admin=True,     # 支持管理员权限
    runtime_tmpdir='.', # 运行时临时目录
)
```

### 3. 优化的恶搞 EXE 生成参数
```python
OPTIMIZED_PYINSTALLER_ARGS = [
    '--onefile',
    '--noconsole',
    '--clean',
    '--upx',                           # UPX 压缩
    '--upx-exclude=vcruntime140.dll',  # 排除特定文件
    '--exclude-module=tkinter.dnd',    # 排除不必要模块
    '--exclude-module=tkinter.test',
    '--runtime-tmpdir=.',              # 运行时临时目录
    '--disable-windowed-traceback',    # 禁用错误窗口
    '--collect-all', 'tkinter',        # 强制收集所有 Tkinter 资源
]
```

### 4. 文件结构规划
```
PrankLauncherBuilder_Standalone/
├── PrankLauncherBuilder_Standalone.exe  # 完全独立的主程序
├── README_Standalone.txt                # 使用说明
├── (可选) assets/                       # 图标资源目录
└── (可选) template/                     # 模板文件目录
```

---

## 🧪 测试验证方案

### 测试环境矩阵
| 测试项目 | Win10 64位 | Win11 64位 | Win10 32位 | 企业版 |
|----------|------------|------------|------------|--------|
| 生成器运行 | ✅ | ✅ | ✅ | ✅ |
| 恶搞 EXE 生成 | ✅ | ✅ | ✅ | ✅ |
| 恶搞 EXE 执行 | ✅ | ✅ | ✅ | ✅ |
| 管理员权限 | ✅ | ✅ | ✅ | ✅ |
| 网络隔离 | ✅ | ✅ | ✅ | ✅ |

### 具体测试用例
1. **纯净系统测试**: 在全新安装的 Windows 虚拟机中测试
2. **依赖缺失测试**: 移除 Python、.NET 等环境组件
3. **安全软件测试**: 在开启 Windows Defender、第三方杀毒软件环境下测试
4. **权限测试**: 标准用户权限、管理员权限、受限用户权限
5. **路径测试**: 中文路径、长路径、特殊字符路径
6. **批量测试**: 连续生成多个恶搞 EXE，测试稳定性
7. **长期运行测试**: 连续运行 24 小时，测试内存泄漏和稳定性

### 性能测试指标
- **启动时间**: 冷启动 ≤ 5秒，热启动 ≤ 2秒
- **内存占用**: 峰值 ≤ 200MB，空闲 ≤ 50MB
- **CPU 使用率**: 峰值 ≤ 30%，平均 ≤ 5%
- **打包速度**: 生成恶搞 EXE ≤ 2分钟
- **文件体积**: 生成器 ≤ 50MB，恶搞 EXE ≤ 30MB

---

## ⚠️ 风险分析与应对

### 技术风险
| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| 杀毒软件误报 | 高 | 中 | 1. 添加数字签名(如有)<br>2. 提供白名单添加指南<br>3. 优化代码减少可疑特征 |
| Windows 版本兼容 | 中 | 高 | 1. 使用兼容性模式<br>2. 提供 Win7 兼容包选项<br>3. 明确系统要求 |
| 文件体积过大 | 中 | 低 | 1. 使用 UPX 压缩<br>2. 精简依赖模块<br>3. 提供精简版选项 |
| 自我繁殖特征误报 | 高 | 高 | 1. 提供关闭选项<br>2. 明确说明功能<br>3. 企业版禁用此功能 |
| 运行时权限不足 | 低 | 中 | 1. 提供管理员权限提示<br>2. 降级运行模式<br>3. 错误友好提示 |

### 部署风险
- **用户教育不足**: 提供清晰的 README 和错误处理指南
- **版本管理混乱**: 建立版本号系统和更新机制
- **反馈渠道缺失**: 建立问题反馈渠道，持续优化

### 法律与合规风险
- **使用范围限制**: 明确说明仅用于合法娱乐目的
- **隐私保护**: 确保不收集用户数据，不侵犯隐私
- **版权合规**: 不侵犯第三方知识产权

---

## 📦 交付成果

### 核心交付物
1. **`PrankLauncherBuilder_Standalone.exe`**: 完全独立的生成器程序
2. **`build_standalone.bat`**: 一键打包脚本
3. **`standalone.spec`**: 独立打包配置文件
4. **`standalone_entry.py`**: 独立入口点代码
5. **`README_Standalone.md`**: 详细使用文档
6. **测试报告文档**: 兼容性测试结果
7. **故障排除指南**: 常见问题解决方案

### 文档交付物
1. **用户手册**: 完整的使用说明和示例
2. **技术手册**: 架构说明和开发指南
3. **部署指南**: 分发和部署说明
4. **FAQ 文档**: 常见问题解答
5. **版本说明**: 版本更新内容和变更记录

### 质量检查清单
- [ ] 生成器在纯净 Windows 10/11 环境正常运行
- [ ] 生成的恶搞 EXE 在目标环境正常运行
- [ ] 文件体积符合要求 (≤ 50MB)
- [ ] 启动时间符合要求 (≤ 5秒)
- [ ] 内存占用符合要求 (≤ 200MB)
- [ ] 无关键错误或崩溃
- [ ] 文档完整且准确
- [ ] 测试用例全部通过

---

## 🚀 后续优化路线图

### 短期优化 (1-2个月)
- [ ] 添加多语言支持 (英文、日文等)
- [ ] 实现云端配置同步功能
- [ ] 添加恶搞模板市场和分享功能
- [ ] 优化 UI 界面，提升用户体验
- [ ] 添加批量生成功能

### 中期规划 (3-6个月)
- [ ] 开发跨平台版本 (macOS, Linux)
- [ ] 集成 AI 智能伪装生成
- [ ] 建立用户社区和反馈系统
- [ ] 添加插件系统和扩展 API
- [ ] 实现自动更新机制

### 长期愿景 (6-12个月)
- [ ] 开发 Web 版本，支持在线生成
- [ ] 集成到游戏平台和软件商店
- [ ] 建立恶搞模板生态系统
- [ ] 开发企业级定制版本
- [ ] 开源核心代码，建立社区贡献

---

## 📊 资源需求

### 人力资源
- **项目负责人**: 1人 (总体规划和协调)
- **开发工程师**: 1-2人 (代码实现和测试)
- **测试工程师**: 1人 (兼容性测试和验证)
- **文档工程师**: 1人 (文档编写和维护)

### 硬件资源
- **开发环境**: Windows 10/11 开发机
- **测试环境**: Windows 10/11 虚拟机 (多种版本)
- **构建服务器**: 用于自动化打包和测试
- **存储空间**: 用于版本管理和备份

### 软件资源
- **开发工具**: Python 3.11, PyInstaller, Git
- **测试工具**: 虚拟机软件, 性能监控工具
- **文档工具**: Markdown 编辑器, 截图工具
- **项目管理**: 任务跟踪和版本控制工具

### 时间资源
- **总工期**: 10个工作日
- **开发时间**: 7天
- **测试时间**: 2天
- **文档时间**: 1天
- **缓冲时间**: 2天 (风险应对)

---

## 🔗 相关文档

### 现有文档
- [PLAN.md](file:///c:/Users/Max/Desktop/ys/PLAN.md) - 原始项目开发计划
- [打包计划.md](file:///c:/Users/Max/Desktop/ys/打包计划.md) - 中文版打包计划
- [builder_gui.py](file:///c:/Users/Max/Desktop/ys/builder/builder_gui.py) - 生成器主界面代码
- [launcher_core.py](file:///c:/Users/Max/Desktop/ys/template/launcher_core.py) - 启动器核心逻辑

### 参考资源
- [Python Embeddable Package](https://www.python.org/downloads/windows/)
- [PyInstaller 文档](https://pyinstaller.org/)
- [Windows PE 文件格式](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
- [Tkinter 文档](https://docs.python.org/3/library/tkinter.html)

---

## 📝 更新记录

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-02-24 | AI Assistant | 初始版本创建，包含完整改造计划 |
| 1.1 | - | - | 预留更新记录 |

---

## 📞 联系与支持

如有问题或建议，请通过以下方式联系：

1. **项目仓库**: (待创建)
2. **问题反馈**: (待建立反馈渠道)
3. **技术讨论**: (待建立讨论区)

**免责声明**: 本项目仅供合法娱乐使用，请遵守当地法律法规，不得用于非法用途。

---

**文档结束**  
*最后更新: 2026-02-24*