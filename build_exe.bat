@echo off
REM =========================================================================
REM Script de build do Contracto (.exe) com PyInstaller
REM
REM Pre-requisitos:
REM   1. Python 3.12+ com pip
REM   2. Ambiente virtual ativo (.venv\Scripts\activate)
REM   3. Dependencias instaladas (pip install -r requirements-dev.txt)
REM
REM Uso:
REM   build_exe.bat
REM
REM Shell Tauri (ADR 0029) + sidecar Python. Requer Rust (MSVC), VS Build Tools e Node.
REM Saidas (sempre versionadas, em dist\):
REM   Contracto_Setup_v<VERSAO>.exe          (instalador NSIS do Tauri)
REM   Contracto_v<VERSAO>.zip                (portatil: Contracto.exe + pasta sidecar)
REM   *.sha256.txt                           (verificacao dos dois)
REM
REM Feche o Contracto antes de rodar: a instancia unica impede gravar o .exe
REM com outro nome em execucao e o antivirus pode bloquear a gravacao.
REM =========================================================================

echo.
echo ==========================================
echo  Build do Contracto - Preparacao de Docs
echo ==========================================
echo.

if not exist .\.venv\Scripts\python.exe (
    echo [AVISO] Ambiente virtual .venv nao encontrado!
    echo [INFO] Criando ambiente virtual em .venv e instalando dependencias...
    echo.
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERRO] O comando 'python' nao foi encontrado no PATH do Windows nesta maquina!
        echo        Instale o Python 3.12 ou superior e marque a opcao 'Add python.exe to PATH'.
        echo.
        pause
        exit /b 1
    )
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual com 'python -m venv .venv'.
        echo.
        pause
        exit /b 1
    )
    echo [INFO] Instalando dependencias do projeto - requirements-dev.txt...
    echo.
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias no .venv!
        echo.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual .venv criado e configurado com sucesso!
    echo.
)

.\.venv\Scripts\python.exe -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [AVISO] PyInstaller nao foi encontrado no ambiente virtual .venv!
    echo [INFO] Instalando dependencias de desenvolvimento - requirements-dev.txt...
    echo.
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller via pip.
        echo        Certifique-se de que a maquina esta conectada a internet ou execute manualmente:
        echo        .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
        echo.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller instalado com sucesso.
    echo.
)

set APP_VERSION=
for /f "delims=" %%v in ('.\.venv\Scripts\python.exe -c "from app import version; print(version.__version__)"') do set APP_VERSION=%%v
echo Versao detectada: %APP_VERSION%
echo.

if "%APP_VERSION%"=="" (
    echo [ERRO] Nao foi possivel determinar a versao da aplicacao em app/version.py.
    echo.
    pause
    exit /b 1
)

REM Verificar se o ambiente virtual esta ativo
if not defined VIRTUAL_ENV (
    echo [AVISO] Ambiente virtual nao detectado.
    echo         Recomenda-se ativar com: .venv\Scripts\activate
    echo.
)

echo [1/3] Encerrando instancias abertas e limpando builds intermediarios...
taskkill /F /IM Contracto.exe /FI "USERNAME eq %USERNAME%" 2>nul
taskkill /F /IM Contracto_sidecar.exe /FI "USERNAME eq %USERNAME%" 2>nul
if exist build\sidecar rmdir /s /q build\sidecar
if exist src-tauri	argeteleaseundle rmdir /s /q src-tauri	argeteleaseundle
echo.

echo [2/3] Preparando dependencias (Ghostscript local)...
.\.venv\Scripts\python.exe scripts\setup_gs.py
if errorlevel 1 (
    echo [ERRO] Build interrompido no passo 2/3: preparo do Ghostscript.
    echo.
    pause
    exit /b 1
)
echo.

echo [3/3] Sidecar (PyInstaller) + shell Tauri + instalador NSIS...
where cargo >nul 2>nul
if errorlevel 1 if not exist "%USERPROFILE%\.cargoin\cargo.exe" (
    echo [ERRO] Rust nao encontrado. Instale com rustup ^(stable-x86_64-pc-windows-msvc^) e o VS Build Tools ^(C++^).
    pause
    exit /b 1
)
.\.venv\Scripts\python.exe scriptsuild_tauri.py
if errorlevel 1 (
    echo [ERRO] Falha no build do Tauri. A causa esta nas mensagens acima.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Build concluido com sucesso!
echo ==========================================
echo.
echo Instalador:
echo   dist\Contracto_Setup_v%APP_VERSION%.exe
echo Portatil:
echo   dist\Contracto_v%APP_VERSION%.zip
echo   dist\Contracto_v%APP_VERSION%.zip.sha256.txt
echo.
echo IMPORTANTE:
echo   - O usuario final nao precisa de Python; o Ghostscript vai embutido no sidecar.
echo   - O instalador remove a instalacao antiga do Inno Setup; os dados em %%APPDATA%%\Contracto ficam.
echo   - Para distribuir, envie o instalador ou o ZIP junto do arquivo SHA-256 correspondente.
echo.
pause
