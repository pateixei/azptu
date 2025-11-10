@echo off
REM Setup script para azptu CLI

echo.
echo ========================================
echo       azptu - Azure PTU CLI Setup
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.8+ primeiro.
    echo Baixe em: https://python.org/downloads
    pause
    exit /b 1
)

echo [INFO] Python encontrado: 
python --version

REM Verificar se Azure CLI está instalado
az --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Azure CLI nao encontrado. 
    echo Instale Azure CLI para usar azptu.
    echo Baixe em: https://docs.microsoft.com/cli/azure/install-azure-cli
    echo.
)

REM Instalar dependências Python
echo [INFO] Instalando dependencias Python...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [SUCESSO] azptu CLI instalado com sucesso!
echo.
echo Comandos disponiveis:
echo   .\azptu.bat --help           (Windows Batch)
echo   .\azptu.ps1 --help           (PowerShell)
echo   python azptu.py --help       (Qualquer sistema)
echo.
echo Proximo passo:
echo   1. az login                  (autenticar no Azure)
echo   2. .\azptu.bat version       (verificar instalacao)
echo   3. .\azptu.bat --help        (ver todos os comandos)
echo.
pause