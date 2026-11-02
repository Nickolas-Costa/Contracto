"""Gera o sidecar (app/sidecar.py) com PyInstaller (onedir, para não extrair 60 MB a cada abertura) em src-tauri/binaries/sidecar/."""
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app"
DESTINO = RAIZ / "src-tauri" / "binaries" / "sidecar"


def arquivo_de_versao() -> Path:
    """Recurso de versão do .exe: o Gerenciador de Tarefas mostra "Contracto" no lugar de "Contracto_sidecar"."""
    sys.path.insert(0, str(APP))
    import version
    partes = [int(x) for x in version.__version__.split(".")] + [0]
    t = ", ".join(map(str, partes[:4]))
    caminho = RAIZ / "build" / "sidecar-work" / "versao.txt"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({t}), prodvers=({t}), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('041604b0', [
    StringStruct('CompanyName', 'Nickolas-Costa'), StringStruct('FileDescription', 'Contracto'),
    StringStruct('FileVersion', '{version.__version__}'), StringStruct('InternalName', 'Contracto_sidecar'),
    StringStruct('OriginalFilename', 'Contracto_sidecar.exe'), StringStruct('ProductName', 'Contracto'),
    StringStruct('ProductVersion', '{version.__version__}')])]), VarFileInfo([VarStruct('Translation', [1046, 1200])])])
""", encoding="utf-8")
    return caminho


def main():
    dados = [(APP / "assets" / pasta, f"assets/{pasta}") for pasta in ("config", "templates", "icons", "gs")
             if (APP / "assets" / pasta).exists()]
    argumentos = ["--noconfirm", "--onedir", "--console", "--name", "Contracto_sidecar",
                  "--paths", str(APP), "--icon", str(APP / "assets" / "icons" / "app_icon.ico"),
                  "--version-file", str(arquivo_de_versao()), "--exclude-module", "tkinter",
                  "--distpath", str(RAIZ / "build" / "sidecar"), "--workpath", str(RAIZ / "build" / "sidecar-work"),
                  "--specpath", str(RAIZ / "build" / "sidecar-work")]
    for origem, alvo in dados:
        argumentos += ["--add-data", f"{origem};{alvo}"]
    for modulo in ("uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto", "uvicorn.lifespan.on",
                   "pikepdf", "pypdfium2", "win32com.client"):
        argumentos += ["--hidden-import", modulo]
    PyInstaller.__main__.run(argumentos + [str(APP / "sidecar.py")])
    shutil.rmtree(DESTINO, ignore_errors=True)
    shutil.copytree(RAIZ / "build" / "sidecar" / "Contracto_sidecar", DESTINO)
    print(f"Sidecar pronto: {DESTINO}")


if __name__ == "__main__":
    main()
