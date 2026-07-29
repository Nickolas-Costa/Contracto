"""
Script para criar o pacote de distribuição Contracto.zip.

Após o build do executável com PyInstaller, este script:
1. Cria a pasta Contracto/ com a estrutura esperada
2. Copia o executável renomeando para Contracto.exe
3. Inclui o README de distribuição
4. Gera o arquivo Contracto.zip pronto para envio
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path


def main():
    projeto_raiz = Path(__file__).resolve().parent.parent
    exe_original = projeto_raiz / "app" / "dist" / "GeradorDeclaracoesCaixa.exe"
    readme_dist = projeto_raiz / "README_DIST.txt"
    
    if not exe_original.exists():
        print(f"[ERRO] Executável não encontrado em {exe_original}")
        print("Execute build_exe.bat primeiro.")
        sys.exit(1)
    
    # Pasta temporária para montar o pacote
    dist_dir = projeto_raiz / "dist"
    contracto_dir = dist_dir / "Contracto"
    
    # Limpar anterior
    if contracto_dir.exists():
        shutil.rmtree(contracto_dir)
    contracto_dir.mkdir(parents=True)
    
    # 1. Copiar executável com nome novo
    print("Copiando executável como Contracto.exe...")
    shutil.copy2(exe_original, contracto_dir / "Contracto.exe")
    
    # 2. Copiar README
    if readme_dist.exists():
        print("Incluindo README_DIST.txt...")
        shutil.copy2(readme_dist, contracto_dir / "LEIA-ME.txt")
    
    # 3. Criar o ZIP
    zip_path = dist_dir / "Contracto.zip"
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"Gerando {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(contracto_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(dist_dir)
                zf.write(file_path, arcname)
    
    # Tamanho do zip
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\nPacote criado com sucesso!")
    print(f"  {zip_path}")
    print(f"  Tamanho: {zip_size_mb:.1f} MB")
    
    # Limpar pasta temporária
    shutil.rmtree(contracto_dir)
    
    print("\nPronto para distribuição!")


if __name__ == "__main__":
    main()
