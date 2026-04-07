@echo off
setlocal
cd /d "%~dp0"

echo [Checking] Python environment...
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Python found. Launching script...
    python builder/builder_gui.py
    exit /b
)

echo [Warning] Python not found in PATH.
echo [Checking] Compiled EXE...
if exist "dist\PrankLauncherBuilder.exe" (
    echo [OK] Found compiled EXE. Launching...
    start "" "dist\PrankLauncherBuilder.exe"
    exit /b
)

echo.
echo [Error] Cannot find Python or PrankLauncherBuilder.exe!
echo.
echo 1. Please install Python 3.11+ (and add to PATH)
echo 2. OR run "build_portable.bat" once to download the environment
echo 3. OR find PrankLauncherBuilder.exe in current directory
echo.
pause
