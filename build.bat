@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 恶搞启动器生成工具 - 专业打包系统 v2.0
color 0A

echo ╔══════════════════════════════════════════════════════════════════╗
echo ║        PrankLauncherBuilder - 专业打包系统 v2.0                 ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM ============================================
REM 步骤 0: 环境检查
REM ============================================
echo [1/6] 检查打包环境...

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python 3.8+
    echo 请访问 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set py_version=%%i
echo     [OK] %py_version%

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller -q
)
for /f "tokens=*" %%i in ('pip show pyinstaller ^| findstr /c:"Name:"') do set line=%%i
for /f "tokens=2 delims=:" %%i in ("!line!") do set pyi_version=%%i
echo     [OK] PyInstaller !pyi_version! 已安装

REM 检查依赖
echo [2/6] 检查项目依赖...
if not exist "builder" (
    echo [错误] builder 目录不存在！
    pause
    exit /b 1
)
if not exist "template" (
    echo [错误] template 目录不存在！
    pause
    exit /b 1
)
echo     [OK] 项目结构完整

REM ============================================
REM 步骤 1: 清理旧构建
REM ============================================
echo [3/6] 清理旧的构建文件...
if exist "build_builder" rmdir /s /q "build_builder" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "logs" rmdir /s /q "logs" 2>nul
echo     [OK] 清理完成

REM ============================================
REM 步骤 2: 安装项目依赖
REM ============================================
echo [4/6] 安装 Python 依赖...
if exist "requirements.txt" (
    pip install -r requirements.txt -q
    echo     [OK] 依赖安装完成
)

REM ============================================
REM 步骤 3: 执行 PyInstaller 打包
REM ============================================
echo [5/6] 执行 PyInstaller 打包...
echo     警告: 这可能需要 2-5 分钟，请耐心等待...
echo.

REM 使用优化的 spec 文件进行打包
python -m PyInstaller PrankLauncherBuilder.spec --clean --noconfirm

if exist "dist\PrankLauncherBuilder.exe" (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║                  打包成功！                              ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    
    REM ============================================
    REM 步骤 4: 后处理
    REM ============================================
    echo [6/6] 执行后处理...
    
    REM 复制资源文件
    if exist "assets\*.ico" (
        echo     复制图标文件...
        mkdir "dist\assets" 2>nul
        xcopy "assets\*.ico" "dist\assets\" /Y /Q 2>nul
    )
    
    REM 复制模板文件（确保完整性）
    if not exist "dist\template" mkdir "dist\template"
    xcopy "template\*.py" "dist\template\" /Y /Q 2>nul
    xcopy "template\*.txt" "dist\template\" /Y /Q 2>nul
    
    REM 复制依赖说明
    echo PrankLauncherBuilder - 依赖说明 > "dist\README.txt"
    echo ==================== >> "dist\README.txt"
    echo. >> "dist\README.txt"
    echo 使用方法: >> "dist\README.txt"
    echo 1. 双击 PrankLauncherBuilder.exe 运行 >> "dist\README.txt"
    echo 2. 配置目标程序和其他参数 >> "dist\README.txt"
    echo 3. 点击"开始生成"创建恶搞exe >> "dist\README.txt"
    echo. >> "dist\README.txt"
    echo 注意事项: >> "dist\README.txt"
    echo - 本程序需要 Windows 7+ 操作系统 >> "dist\README.txt"
    echo - 首次运行可能需要几秒钟解压依赖 >> "dist\README.txt"
    echo - 杀毒软件可能会报毒，这是正常现象 >> "dist\README.txt"
    
    REM 清理调试文件
    if exist "dist\*.pdb" del /q "dist\*.pdb" 2>nul
    if exist "dist\*.exp" del /q "dist\*.exp" 2>nul
    if exist "dist\*.lib" del /q "dist\*.lib" 2>nul
    
    REM 计算文件大小
    for %%I in (dist\PrankLauncherBuilder.exe) do (
        set /a size_mb=%%~zI/1048576
        set /a size_kb=%%~zI/1024
        echo.
        echo ╔══════════════════════════════════════════════════════════╗
        echo ║                  打包完成！                                ║
        echo ╠══════════════════════════════════════════════════════════╣
        echo ║ 输出文件: dist\PrankLauncherBuilder.exe                 ║
        echo ║ 文件大小: !size_mb! MB (!size_kb! KB)                   ║
        echo ╚══════════════════════════════════════════════════════════╝
    )
    
    REM 自动打开输出目录
    start "" explorer.exe "dist"
    
) else (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║                  打包失败！                                ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo 可能的错误原因：
    echo   1. Python 环境不完整
    echo   2. 依赖包未安装
    echo   3. 模板文件缺失
    echo.
    echo 请检查控制台输出的错误信息
    echo.
)

echo.
pause
endlocal
