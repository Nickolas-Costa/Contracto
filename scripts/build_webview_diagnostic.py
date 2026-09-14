"""Empacota a base em pasta isolada; não substitui a distribuição de produção.

Uso: .venv/Scripts/python.exe scripts/build_webview_diagnostic.py
Depois: dist/webview-diagnostic/ContractoBase/ContractoBase.exe --self-test
"""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--console",
               "--name", "ContractoBase", "--distpath", str(root / "dist" / "webview-diagnostic"),
               "--workpath", str(root / "build" / "webview-diagnostic"),
               "--specpath", str(root / "build" / "webview-diagnostic"),
               "--paths", str(root / "app"),
               "--hidden-import", "uvicorn.logging", "--hidden-import", "uvicorn.loops.auto",
               "--hidden-import", "uvicorn.protocols.http.auto", "--hidden-import", "uvicorn.lifespan.on"]
    command += ["--add-data", f"{root / 'frontend'}:frontend"]
    for folder in ("config", "templates", "icons", "gs"):
        if not (root / 'app' / 'assets' / folder).exists():
            if folder == "gs":
                print("Ghostscript não embutido: PDF/A requer instalação detectável no Windows.")
                continue
            raise FileNotFoundError(f"Recurso necessário ausente: {folder}")
        command += ["--add-data", f"{root / 'app' / 'assets' / folder}:assets/{folder}"]
    command.append(str(root / "app" / "webview_shell.py"))
    subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
