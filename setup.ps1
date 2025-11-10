# Setup script para azptu CLI (PowerShell)

Write-Host ""
Write-Host "========================================"
Write-Host "      azptu - Azure PTU CLI Setup"
Write-Host "========================================"
Write-Host ""

# Verificar Python
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "[INFO] Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Python não encontrado. Instale Python 3.8+ primeiro." -ForegroundColor Red
    Write-Host "Baixe em: https://python.org/downloads" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Verificar Azure CLI
try {
    $azVersion = & az --version 2>&1 | Select-Object -First 1
    Write-Host "[INFO] Azure CLI encontrado" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] Azure CLI não encontrado." -ForegroundColor Yellow
    Write-Host "Instale Azure CLI para usar azptu." -ForegroundColor Yellow
    Write-Host "Baixe em: https://docs.microsoft.com/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host ""
}

# Instalar dependências
Write-Host "[INFO] Instalando dependências Python..." -ForegroundColor Cyan
try {
    & pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Erro na instalação"
    }
} catch {
    Write-Host "[ERRO] Falha ao instalar dependências." -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host ""
Write-Host "[SUCESSO] azptu CLI instalado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Comandos disponíveis:" -ForegroundColor Cyan
Write-Host "  .\azptu.bat --help           (Windows Batch)"
Write-Host "  .\azptu.ps1 --help           (PowerShell)"
Write-Host "  python azptu.py --help       (Qualquer sistema)"
Write-Host ""
Write-Host "Próximo passo:" -ForegroundColor Yellow
Write-Host "  1. az login                  (autenticar no Azure)"
Write-Host "  2. .\azptu.bat version       (verificar instalação)"
Write-Host "  3. .\azptu.bat --help        (ver todos os comandos)"
Write-Host ""
Read-Host "Pressione Enter para continuar"