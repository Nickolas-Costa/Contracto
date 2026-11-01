"""Gera o sidecar (app/sidecar.py) com PyInstaller no caminho que o `externalBin` do Tauri espera."""
import shutil
from pathlib import Path

import PyInstaller.__main__

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app"
DESTINO = RAIZ / "src-tauri" / "binaries" / "Contracto_sidecar-x86_64-pc-windows-msvc.exe"


def main():
    dados = [(APP / "assets" / pasta, f"assets/{pasta}") for pasta in ("config", "templates", "icons", "gs")
             if (APP / "assets" / pasta).exists()]
    argumentos = ["--noconfirm", "--onefile", "--console", "--name", "Contracto_sidecar",
                  "--paths", str(APP), "--exclude-module", "tkinter",
                  "--distpath", str(RAIZ / "build" / "sidecar"), "--workpath", str(RAIZ / "build" / "sidecar-work"),
                  "--specpath", str(RAIZ / "build" / "sidecar-work")]
    for origem, alvo in dados:
        argumentos += ["--add-data", f"{origem};{alvo}"]
    for modulo in ("uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto", "uvicorn.lifespan.on",
                   "pikepdf", "pypdfium2", "win32com.client"):
        argumentos += ["--hidden-import", modulo]
    PyInstaller.__main__.run(argumentos + [str(APP / "sidecar.py")])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAIZ / "build" / "sidecar" / "Contracto_sidecar.exe", DESTINO)
    print(f"Sidecar pronto: {DESTINO}")


if __name__ == "__main__":
    main()
