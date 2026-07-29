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
REM O executavel sera gerado em: app\dist\GeradorDeclaracoesCaixa.exe
REM O pacote de distribuicao sera gerado em: dist\Contracto.zip
REM =========================================================================

echo.
echo ==========================================
echo  Build do Contracto - Preparacao de Docs
echo ==========================================
echo.

REM Verificar se o ambiente virtual esta ativo
if not defined VIRTUAL_ENV (
    echo [AVISO] Ambiente virtual nao detectado.
    echo         Recomenda-se ativar com: .venv\Scripts\activate
    echo.
)

echo [1/5] Limpando builds anteriores...
if exist app\build rmdir /s /q app\build
if exist app\dist rmdir /s /q app\dist
if exist dist rmdir /s /q dist
echo.

echo [2/5] Preparando dependencias (Ghostscript local)...
.\.venv\Scripts\python.exe scripts\setup_gs.py
if errorlevel 1 (
    echo [ERRO] Falha ao preparar Ghostscript.
    exit /b 1
)
echo.

echo [3/5] Gerando executavel com PyInstaller...
cd app
..\.venv\Scripts\pyinstaller.exe ^
    --noconsole ^
    --onefile ^
    --name "GeradorDeclaracoesCaixa" ^
    --add-data "assets/templates;assets/templates" ^
    --add-data "assets/gs;assets/gs" ^
    main.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel!
    cd ..
    exit /b 1
)
cd ..
echo.

echo [4/5] Criando atalho na Area de Trabalho...
.\.venv\Scripts\python.exe scripts\create_shortcut.py
echo.

echo [5/5] Gerando pacote de distribuicao (Contracto.zip)...
.\.venv\Scripts\python.exe scripts\create_dist_package.py
echo.

echo ==========================================
echo  Build concluido com sucesso!
echo ==========================================
echo.
echo Executavel gerado em:
echo   app\dist\GeradorDeclaracoesCaixa.exe
echo.
echo Pacote de distribuicao:
echo   dist\Contracto.zip
echo.
echo IMPORTANTE:
echo   - O funcionario final NAO precisa ter Python instalado.
echo   - O Ghostscript ja vem embutido no arquivo.
echo   - Para distribuir, envie o arquivo Contracto.zip.
echo.
pause
