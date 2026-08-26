@echo off
echo ========================================
echo   THZ Limpeza de Janelas - Instalador
echo ========================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Baixe em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [1/2] Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [2/2] Instalacao concluida!
echo.
echo Para executar: python main.py
echo Ou clique duas vezes em: main.pyw
echo.
pause
