import os
import shutil
import sys
from pathlib import Path

# Add app to path to import utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from utils.ghostscript_setup import localizar_ghostscript

def main():
    print("Verificando Ghostscript local para empacotamento...")
    gs_exe = localizar_ghostscript()
    if not gs_exe:
        print("[AVISO] Ghostscript não encontrado no sistema.")
        print("O PyInstaller vai compilar sem o Ghostscript embutido.")
        print("Instale o Ghostscript se quiser que ele venha embutido.")
        sys.exit(0)
    
    gs_bin_dir = gs_exe.parent
    assets_gs_dir = Path(__file__).resolve().parent.parent / "app" / "assets" / "gs"
    
    if assets_gs_dir.resolve() == gs_bin_dir.parent.resolve():
        print("Ghostscript já está na pasta assets. Nada a fazer.")
        return

    gs_lib_dir = gs_bin_dir.parent / "lib"
    if not gs_lib_dir.exists():
        print(f"[AVISO] Pasta lib não encontrada em {gs_lib_dir}. Copiando apenas pasta bin.")
    
        
    # Limpar anterior
    if assets_gs_dir.exists():
        shutil.rmtree(assets_gs_dir)
        
    assets_gs_dir.mkdir(parents=True)
    
    # Copiar bin e lib
    print(f"Copiando Ghostscript de {gs_bin_dir.parent} para {assets_gs_dir}")
    shutil.copytree(gs_bin_dir, assets_gs_dir / "bin")
    if gs_lib_dir.exists():
        shutil.copytree(gs_lib_dir, assets_gs_dir / "lib")
    
    print("Ghostscript embutido com sucesso para o build!")

if __name__ == "__main__":
    main()
