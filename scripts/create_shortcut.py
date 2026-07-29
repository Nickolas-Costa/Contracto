import os
import sys

def main():
    try:
        import win32com.client
    except ImportError:
        print("[AVISO] pywin32 não instalado. Atalho não será criado.")
        sys.exit(0)

    # Caminho do desktop
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    path = os.path.join(desktop, 'Gerador Declaracoes.lnk')
    
    # Caminho do executável compilado
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "dist", "GeradorDeclaracoesCaixa.exe"))
    
    if not os.path.exists(target):
        print(f"[ERRO] Executável não encontrado em {target}")
        sys.exit(1)
        
    print(f"Criando atalho em {path} apontando para {target}...")
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = target
    shortcut.save()
    
    print("Atalho criado com sucesso na Área de Trabalho!")

if __name__ == "__main__":
    main()
