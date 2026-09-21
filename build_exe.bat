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
REM O executavel sera gerado em: app\dist\Contracto_v<VERSAO>.exe
REM O pacote de distribuicao sera gerado em: dist\Contracto_v<VERSAO>.zip (+ .sha256.txt)
REM =========================================================================

echo.
echo ==========================================
echo  Build do Contracto - Preparacao de Docs
echo ==========================================
echo.

if not exist .\.venv\Scripts\python.exe (
    echo [ERRO] Ambiente virtual .venv nao foi encontrado nesta maquina!
    echo.
    echo Para solucionar, execute os comandos abaixo no terminal CMD ou PowerShell:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\python.exe -m pip install --upgrade pip
    echo   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    echo.
    pause
    exit /b 1
)

set APP_VERSION=
for /f "delims=" %%v in ('.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'app'); import version; print(version.__version__)"') do set APP_VERSION=%%v

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

echo [1/5] Limpando builds anteriores e processos abertos...
taskkill /F /IM Contracto_v%APP_VERSION%.exe /FI "USERNAME eq %USERNAME%" 2>nul
taskkill /F /IM Contracto.exe /FI "USERNAME eq %USERNAME%" 2>nul
if exist app\build rmdir /s /q app\build
if exist app\dist rmdir /s /q app\dist
if exist dist rmdir /s /q dist
echo.

echo [2/5] Preparando dependencias (Ghostscript local)...
.\.venv\Scripts\python.exe scripts\setup_gs.py
if errorlevel 1 (
    echo [ERRO] Build interrompido no passo 2/5: preparo do Ghostscript.
    echo        A causa esta nas mensagens acima desta linha.
    echo.
    pause
    exit /b 1
)
echo.

echo [3/5] Lendo versao e gerando executavel com PyInstaller (via Contracto_v%APP_VERSION%.spec)...
echo Versao detectada: %APP_VERSION%

.\.venv\Scripts\python.exe scripts\generate_spec.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o arquivo de especificacao .spec do PyInstaller!
    echo.
    pause
    exit /b 1
)

cd app
..\.venv\Scripts\python.exe -m PyInstaller Contracto_v%APP_VERSION%.spec
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel!
    cd ..
    echo.
    pause
    exit /b 1
)
cd ..
echo.

echo [4/5] Criando atalho na Area de Trabalho...
.\.venv\Scripts\python.exe scripts\create_shortcut.py
echo.

echo [5/5] Gerando pacote de distribuicao versionado + SHA-256...
.\.venv\Scripts\python.exe scripts\create_dist_package.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o pacote de distribuicao.
    echo.
    pause
    exit /b 1
)
.\.venv\Scripts\python.exe -c "import hashlib,pathlib; p=pathlib.Path(r'dist\Contracto_v%APP_VERSION%.zip'); f=p.open('rb'); h=hashlib.file_digest(f,'sha256').hexdigest().upper(); f.close(); pathlib.Path(str(p)+'.sha256.txt').write_text('SHA256  '+h+'  '+p.name+'\n', encoding='utf-8')"
if errorlevel 1 (
    echo [ERRO] Falha ao gerar a verificacao SHA-256 do pacote.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Build concluido com sucesso!
echo ==========================================
echo.
echo Executavel gerado em:
echo   app\dist\Contracto_v%APP_VERSION%.exe
echo.
echo Pacote de distribuicao verificavel:
echo   dist\Contracto_v%APP_VERSION%.zip
echo   dist\Contracto_v%APP_VERSION%.zip.sha256.txt
echo.
echo IMPORTANTE:
echo   - O Usuario final Nao necessita ter o Python instalado na maquina.
echo   - Ghostscript e todas as dependencias estao embutidas no arquivo .exe.
echo   - Para distribuir, envie o ZIP junto do arquivo SHA-256 correspondente.
echo.
pause
