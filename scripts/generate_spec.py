"""Gera o arquivo .spec do PyInstaller dinamicamente com base na versão atual em app/version.py."""

from pathlib import Path
import sys

# Adicionar app ao sys.path para importar version
raiz = Path(__file__).resolve().parent.parent
app_dir = raiz / "app"
sys.path.insert(0, str(app_dir))

import version

versao = version.__version__
spec_file = app_dir / f"Contracto_v{versao}.spec"

spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

block_cipher = None

app_dir = Path('.').resolve()
root_dir = app_dir.parent

datas = [
    (str(root_dir / 'frontend'), 'frontend'),
    (str(app_dir / 'assets' / 'config'), 'assets/config'),
    (str(app_dir / 'assets' / 'templates'), 'assets/templates'),
    (str(app_dir / 'assets' / 'icons'), 'assets/icons'),
]

gs_dir = app_dir / 'assets' / 'gs'
if gs_dir.exists():
    datas.append((str(gs_dir), 'assets/gs'))

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'customtkinter',
    'PIL',
    'pypdf',
    'pikepdf',
    'pypdfium2',
    'pywebview',
    'win32com.client',
]

a = Analysis(
    ['main.py'],
    pathex=[str(app_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Contracto_v{versao}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(app_dir / 'assets' / 'icons' / 'app_icon.ico'),
)
"""

print(f"Gerando especificação PyInstaller: {spec_file.name}...")
spec_file.write_text(spec_content, encoding="utf-8")
print("Arquivo .spec gerado com sucesso!")
