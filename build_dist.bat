@echo off
echo === Building PrankBuilder Distribution (Fixed) ===

REM 1. Clean previous builds
if exist "PrankBuilder_Dist" rmdir /s /q "PrankBuilder_Dist"
mkdir "PrankBuilder_Dist"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PrankBuilder.spec del /q PrankBuilder.spec

REM 2. Package Builder GUI with FORCE CLEAN and FULL TKINTER COLLECTION
echo Packaging main program...
echo Note: This might take a bit longer due to --clean and --collect-all...

pyinstaller --noconsole --onefile --clean --name "PrankBuilder" --add-data "template;template" --collect-all tkinter builder/builder_gui.py

if errorlevel 1 (
    echo [ERROR] Packaging failed!
    echo Please make sure you have the latest PyInstaller installed: pip install --upgrade pyinstaller
    pause
    exit /b 1
)

REM 3. Move file to distribution directory
move "dist\PrankBuilder.exe" "PrankBuilder_Dist\"

REM 4. Create README
echo This is a portable builder tool. > "PrankBuilder_Dist\README.txt"
echo. >> "PrankBuilder_Dist\README.txt"
echo [Requirements] >> "PrankBuilder_Dist\README.txt"
echo This tool requires a Python environment to build EXEs. >> "PrankBuilder_Dist\README.txt"
echo 1. If Python and PyInstaller are installed, just run PrankBuilder.exe. >> "PrankBuilder_Dist\README.txt"
echo 2. If not installed, download "Python Embeddable Package" and extract it to a folder named "python_embedded" here. >> "PrankBuilder_Dist\README.txt"

REM 5. Clean up temporary files
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PrankBuilder.spec del /q PrankBuilder.spec

echo.
echo === Build Complete! ===
echo Distribution package location: %~dp0PrankBuilder_Dist
echo You can zip the PrankBuilder_Dist folder and send it to anyone.
echo.
pause
