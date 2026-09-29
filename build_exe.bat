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
REM Saidas (sempre versionadas):
REM   app\dist\Contracto_v<VERSAO>.exe      (executavel principal)
REM   dist\Contracto_v<VERSAO>.exe          (copia para teste rapido)
REM   dist\Contracto_v<VERSAO>.zip (+ .sha256.txt)
REM   dist\Contracto_Installer_v<VERSAO>.exe (somente com Inno Setup)
REM
REM Feche o Contracto antes de rodar: a instancia unica impede gravar o .exe
REM com outro nome em execucao e o antivirus pode bloquear a gravacao.
REM =========================================================================

echo.
echo ==========================================
echo  Build do Contracto - Preparacao de Docs
echo ==========================================
echo.

for /f "delims=" %%v in ('.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'app'); import version; print(version.__version__)"') do set APP_VERSION=%%v
echo Versao detectada: %APP_VERSION%
echo.

REM Verificar se o ambiente virtual esta ativo
if not defined VIRTUAL_ENV (
    echo [AVISO] Ambiente virtual nao detectado.
    echo         Recomenda-se ativar com: .venv\Scripts\activate
    echo.
)

echo [1/6] Encerrando instancias abertas e limpando builds intermediarios...
taskkill /F /IM Contracto_v%APP_VERSION%.exe /FI "USERNAME eq %USERNAME%" 2>nul
taskkill /F /IM Contracto.exe /FI "USERNAME eq %USERNAME%" 2>nul
if exist app\build rmdir /s /q app\build
if exist app\dist rmdir /s /q app\dist
echo         (a pasta dist\ de entrega so e limpa DEPOIS do novo .exe pronto)
echo.

echo [2/6] Preparando dependencias (Ghostscript local)...
.\.venv\Scripts\python.exe scripts\setup_gs.py
if errorlevel 1 (
    echo [ERRO] Build interrompido no passo 2/6: preparo do Ghostscript.
    echo        A causa esta nas mensagens acima desta linha.
    exit /b 1
)
echo.

echo [3/6] Gerando executavel com PyInstaller (via Contracto_v%APP_VERSION%.spec)...
cd app
..\.venv\Scripts\python.exe -m PyInstaller Contracto_v%APP_VERSION%.spec
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel!
    cd ..
    exit /b 1
)
cd ..
if not exist "app\dist\Contracto_v%APP_VERSION%.exe" (
    echo [ERRO] PyInstaller terminou sem gerar app\dist\Contracto_v%APP_VERSION%.exe.
    echo        Feche o Contracto aberto e o antivirus, e rode de novo.
    exit /b 1
)
for %%f in ("app\dist\Contracto_v%APP_VERSION%.exe") do echo [OK] Executavel: %%~nxF (%%~zf bytes, %%~tf)
echo.

echo [4/6] Copiando .exe para dist\ e gerando pacote versionado + SHA-256...
if not exist dist mkdir dist
copy /y "app\dist\Contracto_v%APP_VERSION%.exe" "dist\Contracto_v%APP_VERSION%.exe" >nul
if errorlevel 1 (
    echo [ERRO] Falha ao copiar o executavel para dist\.
    exit /b 1
)
.\.venv\Scripts\python.exe scripts\create_dist_package.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o pacote de distribuicao.
    exit /b 1
)
.\.venv\Scripts\python.exe -c "import hashlib,pathlib; p=pathlib.Path(r'dist\Contracto_v%APP_VERSION%.zip'); f=p.open('rb'); h=hashlib.file_digest(f,'sha256').hexdigest().upper(); f.close(); pathlib.Path(str(p)+'.sha256.txt').write_text('SHA256  '+h+'  '+p.name+'\n', encoding='utf-8')"
if errorlevel 1 (
    echo [ERRO] Falha ao gerar a verificacao SHA-256 do pacote.
    exit /b 1
)
echo.

echo [5/6] Criando atalho na Area de Trabalho...
.\.venv\Scripts\python.exe scripts\create_shortcut.py
echo.

echo [6/6] Compilando instalador Windows com Inno Setup (gate de release)...
where /q iscc
if errorlevel 1 (
    echo [AVISO] Inno Setup ^(ISCC.exe^) nao encontrado no PATH: instalador pulado.
    echo         O .exe e o ZIP ja estao prontos em dist\. Para a release final,
    echo         instale o Inno Setup 6 e rode: .\.venv\Scripts\python.exe scripts\build_installer.py
    goto fim_ok
)
.\.venv\Scripts\python.exe scripts\build_installer.py
if errorlevel 1 (
    echo [ERRO] Falha ao compilar o instalador Windows.
    exit /b 1
)

:fim_ok
echo.
echo ==========================================
echo  Build concluido com sucesso!
echo ==========================================
echo.
echo Executavel principal:
echo   app\dist\Contracto_v%APP_VERSION%.exe
echo.
echo Copia para teste rapido:
echo   dist\Contracto_v%APP_VERSION%.exe
echo.
echo Pacote de distribuicao verificavel:
echo   dist\Contracto_v%APP_VERSION%.zip
echo   dist\Contracto_v%APP_VERSION%.zip.sha256.txt
echo.
echo Instalador (somente com Inno Setup):
echo   dist\Contracto_Installer_v%APP_VERSION%.exe
echo.
echo IMPORTANTE:
echo   - O Usuario final Nao necessita ter o Python instalado na maquina.
echo   - Ghostscript e todas as dependencias estao embutidas no arquivo .exe.
echo   - Para distribuir, envie o instalador ou o ZIP junto do arquivo SHA-256 correspondente.
echo.
pause
