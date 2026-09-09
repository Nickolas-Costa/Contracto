import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add app to path to import utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from utils.ghostscript_setup import localizar_ghostscript


def versao_ghostscript(gs_exe: Path) -> str:
    """Versão do executável (`gs --version`) ou 'desconhecida'."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.run(
            [str(gs_exe), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
        )
        versao = proc.stdout.strip().splitlines()
        return versao[0].strip() if versao and proc.returncode == 0 else "desconhecida"
    except (OSError, subprocess.SubprocessError):
        return "desconhecida"


def main(argumentos: list | None = None) -> int:
    """Prepara o Ghostscript embutido. Devolve código de saída (0 = ok).

    Sem Ghostscript, falha (1), exceto com `--allow-without-gs`, que gera
    um executável sem o motor de PDF/A.
    """
    permitir_sem_gs = "--allow-without-gs" in (argumentos if argumentos is not None else sys.argv[1:])
    print("Verificando Ghostscript local para empacotamento...")
    gs_exe = localizar_ghostscript()
    if not gs_exe:
        print("[AVISO] Ghostscript não encontrado no sistema.")
        if permitir_sem_gs:
            print("Seguindo sem o Ghostscript embutido (--allow-without-gs).")
            print("O executável gerado NÃO converterá para PDF/A.")
            return 0
        print("[ERRO] Causa da interrupção do build: Ghostscript não encontrado.")
        print("Sem ele, o executável sairia sem o motor de conversão para PDF/A.")
        print("Instale o Ghostscript ou use --allow-without-gs para seguir mesmo assim.")
        return 1

    print(f"Ghostscript {versao_ghostscript(gs_exe)} em: {gs_exe}")

    gs_bin_dir = gs_exe.parent
    assets_gs_dir = Path(__file__).resolve().parent.parent / "app" / "assets" / "gs"

    if assets_gs_dir.resolve() == gs_bin_dir.parent.resolve():
        print("Ghostscript já está na pasta assets. Nada a fazer.")
        return 0

    gs_lib_dir = gs_bin_dir.parent / "lib"
    if not gs_lib_dir.exists():
        print(f"[AVISO] Pasta lib não encontrada em {gs_lib_dir}. Copiando apenas pasta bin.")


    # Limpar anterior
    if assets_gs_dir.exists():
        shutil.rmtree(assets_gs_dir)

    assets_gs_dir.mkdir(parents=True)

    # Copiar bin e lib
    print(f"Copiando Ghostscript de {gs_bin_dir.parent} para {assets_gs_dir}")
    try:
        shutil.copytree(gs_bin_dir, assets_gs_dir / "bin")
        if gs_lib_dir.exists():
            shutil.copytree(gs_lib_dir, assets_gs_dir / "lib")
    except OSError as exc:
        print(f"[ERRO] Falha ao copiar o Ghostscript: {exc}")
        return 1

    print("Ghostscript embutido com sucesso para o build!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
