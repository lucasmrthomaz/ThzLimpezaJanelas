@echo off
setlocal
cd /d "%~dp0"

if exist __pycache__ rmdir /s /q __pycache__

python -m nuitka --onefile ^
  --enable-plugin=pyside6 ^
  --windows-console-mode=disable ^
  --windows-icon-from-ico=assets\icon.ico ^
  --output-filename=ThzLimpezaJanelas.exe ^
  --output-dir=dist-nuitka ^
  --assume-yes-for-downloads ^
  main.py

if errorlevel 1 goto :err

echo.
echo OK: dist-nuitka\ThzLimpezaJanelas.exe
goto :eof

:err
echo FALHA no build Nuitka
exit /b 1
