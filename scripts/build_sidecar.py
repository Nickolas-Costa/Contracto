"""Gera o sidecar (app/sidecar.py) com PyInstaller (onedir, para não extrair 60 MB a cada abertura) em src-tauri/binaries/sidecar/."""
import shutil
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app"
DESTINO = RAIZ / "src-tauri" / "binaries" / "sidecar"


def main():
    dados = [(APP / "assets" / pasta, f"assets/{pasta}") for pasta in ("config", "templates", "icons", "gs")
             if (APP / "assets" / pasta).exists()]
    argumentos = ["--noconfirm", "--onedir", "--console", "--name", "Contracto_sidecar",
                  "--paths", str(APP), "--exclude-module", "tkinter",
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
