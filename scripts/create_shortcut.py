import os
import sys

def main():
    try:
        import win32com.client
    except ImportError:
        print("[AVISO] pywin32 não instalado. Atalho não será criado.")
        sys.exit(0)

    user_profile = os.environ.get('USERPROFILE', '')
    desktop_candidates = [
        os.path.join(user_profile, 'OneDrive', 'Desktop'),
        os.path.join(user_profile, 'Desktop'),
    ]
    
    desktop = None
    for d in desktop_candidates:
        if os.path.exists(d):
            desktop = d
            break
            
    if not desktop:
        print("[AVISO] Pasta Desktop não encontrada. Atalho não será criado.")
        sys.exit(0)

    path = os.path.join(desktop, 'Contracto.lnk')
    
    # Caminho do executável compilado
    projeto_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(projeto_raiz, "app"))
    import version
    
    target = os.path.join(projeto_raiz, "app", "dist", f"Contracto_v{version.__version__}.exe")
    
    if not os.path.exists(target):
        print(f"[ERRO] Executável não encontrado em {target}")
        sys.exit(1)
        
    icon_path = os.path.join(projeto_raiz, "app", "assets", "icons", "app_icon.ico")
    
    try:
        print(f"Criando atalho em {path} apontando para {target}...")
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"
        else:
            shortcut.IconLocation = f"{target},0"
        shortcut.save()
        
        # Notificar o Windows para recarregar o cache de ícones da Área de Trabalho
        try:
            import ctypes
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_IDLIST = 0x0000
            ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        except Exception:
            pass

        print("Atalho criado com sucesso na Área de Trabalho!")
    except Exception as e:
        print(f"[AVISO] Não foi possível salvar o atalho na área de trabalho: {e}")

if __name__ == "__main__":
    main()
