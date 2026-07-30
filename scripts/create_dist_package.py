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
    
    # Adicionar app ao PYTHONPATH para conseguir importar version.py
    sys.path.insert(0, str(projeto_raiz / "app"))
    import version
    
    versao = version.__version__
    exe_name = f"Contracto_v{versao}.exe"
    zip_name = f"Contracto_v{versao}.zip"
    
    exe_original = projeto_raiz / "app" / "dist" / exe_name
    
    if not exe_original.exists():
        print(f"[ERRO] Executável não encontrado em {exe_original}")
        print("Execute build_exe.bat primeiro.")
        sys.exit(1)
    
    # Pasta temporária para montar o pacote
    dist_dir = projeto_raiz / "dist"
    contracto_dir = dist_dir / f"Contracto_v{versao}"
    
    # Limpar anterior
    if contracto_dir.exists():
        shutil.rmtree(contracto_dir)
    contracto_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copiar executável com nome novo
    print(f"Copiando executável como {exe_name}...")
    shutil.copy2(exe_original, contracto_dir / exe_name)
    
    # 2. Copiar README
    # (Removido, pois agora temos a Tela de Boas-Vindas interativa dentro do app)
    
    # 3. Criar o ZIP
    zip_path = dist_dir / zip_name
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
