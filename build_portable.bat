@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 恶搞启动器生成工具 - 便携版打包 v2.0
color 0E

echo ╔══════════════════════════════════════════════════════════════════╗
echo ║        PrankLauncherBuilder - 便携版打包工具 v2.0              ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo [信息] 此脚本将创建一个完全独立的便携版本
echo [信息] 便携版包含嵌入式 Python 环境，无需系统安装 Python
echo.

REM ============================================
REM 设置变量
REM ============================================
set "SCRIPT_DIR=%~dp0"
set "OUTPUT_DIR=%SCRIPT_DIR%PrankBuilder_Portable"
set "PYTHON_EMBED_DIR=%SCRIPT_DIR%python_embedded"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

REM ============================================
REM 检查嵌入式 Python 是否存在
REM ============================================
echo [检查] 检查嵌入式 Python 环境...
if not exist "%PYTHON_EMBED_DIR%\python.exe" (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════╗
    echo ║                    嵌入式 Python 未找到！                    ║
    echo ╚═══════════════════════════════════════════════════════════════╝
    echo.
    echo [下载] 正在准备下载嵌入式 Python...
    echo [信息] 下载链接: %PYTHON_URL%
    echo.
    echo [手动下载步骤]
    echo 1. 访问: %PYTHON_URL%
    echo 2. 下载文件到: %SCRIPT_DIR%python_embeddable.zip
    echo 3. 解压到: %SCRIPT_DIR%python_embedded
    echo 4. 运行此脚本再次打包
    echo.
    echo [自动下载]
    echo 如果你有 7-Zip，可以尝试自动下载并解压...
    echo.
    
    set /p user_choice="是否尝试自动下载? (y/n): "
    if /i "%user_choice%"=="y" (
        echo [下载] 正在下载 Python 嵌入式包...
        powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile 'python_embeddable.zip'}"
        
        if exist "python_embeddable.zip" (
            echo [解压] 正在解压...
            powershell -Command "& {Expand-Archive -Path 'python_embeddable.zip' -DestinationPath 'python_embedded' -Force}"
            
            if exist "%PYTHON_EMBED_DIR%\python.exe" (
                echo [成功] Python 嵌入式环境已准备好！
            ) else (
                echo [失败] 自动下载失败，请手动操作
                pause
                exit /b 1
            )
        ) else (
            echo [失败] 下载失败，请手动下载
            pause
            exit /b 1
        )
    ) else (
        echo [取消] 用户取消，请手动下载后重试
        pause
        exit /b 0
    )
)

echo [OK] 嵌入式 Python 环境已就绪

REM ============================================
REM 检查 PyInstaller
REM ============================================
echo [检查] 检查 PyInstaller...
if not exist "%PYTHON_EMBED_DIR%\Scripts\pyinstaller.exe" (
    echo [安装] 正在安装 PyInstaller...
    "%PYTHON_EMBED_DIR%\python.exe" -m pip install pyinstaller pefile -q
    echo [OK] PyInstaller 安装完成
) else (
    echo [OK] PyInstaller 已安装
)

REM ============================================
REM 创建输出目录
REM ============================================
echo.
echo [准备] 创建便携版目录...
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%\template"
mkdir "%OUTPUT_DIR%\assets"
mkdir "%OUTPUT_DIR%\logs"

echo [OK] 输出目录: %OUTPUT_DIR%

REM ============================================
REM 复制项目文件
REM ============================================
echo [复制] 复制项目文件...

REM 复制 builder 目录
xcopy "%SCRIPT_DIR%builder" "%OUTPUT_DIR%\builder\" /E /I /Q /Y

REM 复制模板文件
xcopy "%SCRIPT_DIR%template\*" "%OUTPUT_DIR%\template\" /Y /Q

REM 复制资源文件（如果存在）
if exist "%SCRIPT_DIR%assets\*" (
    xcopy "%SCRIPT_DIR%assets\*" "%OUTPUT_DIR%\assets\" /Y /Q
)

REM 复制配置文件
if exist "%SCRIPT_DIR%requirements.txt" copy "%SCRIPT_DIR%requirements.txt" "%OUTPUT_DIR%\" /Y
if exist "%SCRIPT_DIR%PLAN.md" copy "%SCRIPT_DIR%PLAN.md" "%OUTPUT_DIR%\" /Y

echo [OK] 项目文件复制完成

REM ============================================
REM 安装 PyInstaller 到嵌入式环境
REM ============================================
echo [安装] 安装 PyInstaller 到便携环境...
"%PYTHON_EMBED_DIR%\python.exe" -m pip install pyinstaller pefile pywin32 -q --target="%PYTHON_EMBED_DIR%\Lib\site-packages"
echo [OK] PyInstaller 安装完成

REM ============================================
REM 执行打包
REM ============================================
echo.
echo [打包] 开始打包便携版...
echo [警告] 这可能需要 3-5 分钟，请耐心等待...
echo.

REM 切换到输出目录执行打包
cd "%OUTPUT_DIR%"

REM 执行打包命令
"%PYTHON_EMBED_DIR%\python.exe" -m PyInstaller PrankLauncherBuilder.spec --clean --noconfirm --distpath "%OUTPUT_DIR%\dist"

REM ============================================
REM 复制输出文件
REM ============================================
if exist "%OUTPUT_DIR%\dist\PrankLauncherBuilder.exe" (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════╗
    echo ║                    便携版打包成功！                          ║
    echo ╚═══════════════════════════════════════════════════════════════╝
    echo.
    
    echo [整理] 整理输出文件...
    
    REM 移动 exe 到根目录
    move "%OUTPUT_DIR%\dist\PrankLauncherBuilder.exe" "%OUTPUT_DIR%\" >nul
    
    REM 删除临时目录
    rmdir /s /q "%OUTPUT_DIR%\dist" 2>nul
    rmdir /s /q "%OUTPUT_DIR%\build" 2>nul
    rmdir /s /q "%OUTPUT_DIR%\build_builder" 2>nul
    
    REM 复制必要资源
    if exist "template" xcopy "template" "%OUTPUT_DIR%\template\" /E /I /Y /Q >nul
    if exist "assets" xcopy "assets" "%OUTPUT_DIR%\assets\" /E /I /Y /Q >nul
    
    REM 创建便携版说明文件
    echo PrankLauncherBuilder 便携版 > "%OUTPUT_DIR%\README.txt"
    echo =============================== >> "%OUTPUT_DIR%\README.txt"
    echo. >> "%OUTPUT_DIR%\README.txt"
    echo 版本: v2.0 便携版 >> "%OUTPUT_DIR%\README.txt"
    echo. >> "%OUTPUT_DIR%\README.txt"
    echo 使用方法: >> "%OUTPUT_DIR%\README.txt"
    echo 1. 双击 PrankLauncherBuilder.exe 启动程序 >> "%OUTPUT_DIR%\README.txt"
    echo 2. 无需安装 Python >> "%OUTPUT_DIR%\README.txt"
    echo 3. 无需安装任何依赖 >> "%OUTPUT_DIR%\README.txt"
    echo. >> "%OUTPUT_DIR%\README.txt"
    echo 文件说明: >> "%OUTPUT_DIR%\README.txt"
    echo - PrankLauncherBuilder.exe: 主程序 >> "%OUTPUT_DIR%\README.txt"
    echo - template/: 启动器模板目录 >> "%OUTPUT_DIR%\README.txt"
    echo - assets/: 图标资源目录 >> "%OUTPUT_DIR%\README.txt"
    echo - logs/: 日志目录 >> "%OUTPUT_DIR%\README.txt"
    echo. >> "%OUTPUT_DIR%\README.txt"
    echo 系统要求: >> "%OUTPUT_DIR%\README.txt"
    echo - Windows 7/8/10/11 64位 >> "%OUTPUT_DIR%\README.txt"
    echo - 至少 100MB 磁盘空间 >> "%OUTPUT_DIR%\README.txt"
    echo. >> "%OUTPUT_DIR%\README.txt"
    echo 注意事项: >> "%OUTPUT_DIR%\README.txt"
    echo - 首次启动可能需要几秒钟初始化 >> "%OUTPUT_DIR%\README.txt"
    echo - 杀毒软件可能报毒，添加信任即可 >> "%OUTPUT_DIR%\README.txt"
    echo - 推荐将整个文件夹移动到任意位置使用 >> "%OUTPUT_DIR%\README.txt"
    
    REM 计算最终文件大小
    set total_size=0
    for /r "%OUTPUT_DIR%" %%f in (*) do (
        set /a total_size+=%%~zf
    )
    set /a total_size_mb=total_size/1048576
    
    echo.
    echo ╔═══════════════════════════════════════════════════════════════╗
    echo ║                    便携版打包完成！                          ║
    echo ╠═══════════════════════════════════════════════════════════════╣
    echo ║ 输出目录: %OUTPUT_DIR%          ║
    echo ║ 总体大小: %total_size_mb% MB                              ║
    echo ╚═══════════════════════════════════════════════════════════════╝
    echo.
    echo [完成] 便携版已准备就绪！
    echo [提示] 可以打包 %OUTPUT_DIR% 文件夹分发给其他用户
    echo.
    
    REM 询问是否打开目录
    set /p open_dir="是否打开输出目录? (y/n): "
    if /i "%open_dir%"=="y" (
        start "" explorer.exe "%OUTPUT_DIR%"
    )
    
) else (
    echo.
    echo ╔═══════════════════════════════════════════════════════════════╗
    echo ║                    便携版打包失败！                          ║
    echo ╚═══════════════════════════════════════════════════════════════╝
    echo.
    echo [错误] 打包过程中出现错误
    echo [建议] 请检查以下内容:
    echo   1. 嵌入式 Python 是否完整
    echo   2. 项目文件是否齐全
    echo   3. 磁盘空间是否充足
    echo.
    echo [调试] 查看控制台输出的错误信息
    echo.
)

cd "%SCRIPT_DIR%"
pause
endlocal






