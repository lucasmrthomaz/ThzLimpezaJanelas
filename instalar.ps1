# THZ Limpeza de Janelas - Instalador
# Execute: .\instalar.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  THZ Limpeza de Janelas - Instalador" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERRO] Python nao encontrado no PATH." -ForegroundColor Red
    Write-Host "Baixe em: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host 'Marque "Add Python to PATH" durante a instalacao.' -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[1/2] Instalando dependencias..." -ForegroundColor Green
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERRO] Falha ao instalar dependencias." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
Write-Host "[2/2] Instalacao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "Para executar: python main.py" -ForegroundColor Cyan
Write-Host "Ou clique duas vezes em: main.pyw" -ForegroundColor Cyan
Write-Host ""
Read-Host "Pressione Enter para fechar"
