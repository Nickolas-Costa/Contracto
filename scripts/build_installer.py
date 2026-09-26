"""Compila o instalador Windows do Contracto com Inno Setup.

Regras:
- lê a versão canônica a partir de app/version.py;
- valida que o Inno Setup (iscc.exe) esteja instalado antes do build;
- compila o arquivo packaging/Contracto.iss para um .exe no diretório dist.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
APP_VERSION_FILE = REPO_ROOT / "app" / "version.py"
ISS_FILE = REPO_ROOT / "packaging" / "Contracto.iss"
DIST_DIR = REPO_ROOT / "dist"


def read_version() -> str:
    sys.path.insert(0, str(REPO_ROOT / "app"))
    import version  # type: ignore

    return str(version.__version__).strip()


def find_iscc() -> str:
    candidates = [
        os.environ.get("ISCC_PATH"),
        shutil.which("iscc"),
        shutil.which("iscc.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "Inno Setup não encontrado. Instale o ISCC.exe ou defina ISCC_PATH antes de continuar."
    )


def main() -> int:
    try:
        version = read_version()
    except Exception as exc:  # pragma: no cover - bloqueio de build de release
        print(f"[ERRO] Não foi possível ler a versão do app: {exc}")
        return 1

    if not ISS_FILE.exists():
        print(f"[ERRO] Script do instalador ausente: {ISS_FILE}")
        return 1

    if not (REPO_ROOT / "app" / "dist").exists():
        print("[ERRO] App empacotado não encontrado em app/dist. Rode o build do executável antes do instalador.")
        return 1

    exe_path = REPO_ROOT / "app" / "dist" / f"Contracto_v{version}.exe"
    if not exe_path.exists():
        print(f"[ERRO] Executável esperado ausente: {exe_path}")
        return 1

    DIST_DIR.mkdir(exist_ok=True)

    try:
        iscc = find_iscc()
    except FileNotFoundError as exc:
        print(f"[ERRO] {exc}")
        return 1

    cmd = [iscc, str(ISS_FILE)]
    print(f"[1/2] Compilando instalador Contracto v{version}...")
    print(f"  comando: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))
    except subprocess.CalledProcessError as exc:
        print(f"[ERRO] Falha na compilação do instalador (código {exc.returncode}).")
        return exc.returncode

    installer_name = f"Contracto_Installer_v{version}.exe"
    installer_path = DIST_DIR / installer_name
    if not installer_path.exists():
        print(f"[ERRO] Instalador final não encontrado em {installer_path}.")
        return 1

    print(f"[2/2] Instalador pronto: {installer_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
