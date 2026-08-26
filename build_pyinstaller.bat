@echo off
setlocal
cd /d "%~dp0"

if exist __pycache__ rmdir /s /q __pycache__

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name ThzLimpezaJanelas ^
  --icon assets\icon.ico ^
  --version-file assets\version_info.txt ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  main.py

if errorlevel 1 goto :err

echo.
echo OK: dist\ThzLimpezaJanelas.exe
goto :eof

:err
echo FALHA no build PyInstaller
exit /b 1
