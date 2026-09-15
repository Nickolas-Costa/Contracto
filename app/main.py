"""
Ponto de entrada da aplicação.

Interface padrão: WebView (`frontend/`) sobre a API local.
Interface legada Tk (`ui/`) mantida como backup de consulta — abrir com
`python main.py --tk` a partir da pasta `app/`.
"""

import sys
import traceback

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("contracto.app.v4")
    except Exception:
        pass

from utils.instancia_unica import InstanciaJaEmExecucao, InstanciaUnica
from utils.logger import configurar_logger


def escolher_interface(argumentos: list[str] | None = None) -> str:
    """Devolve "tk" com `--tk`; qualquer outro caso abre a WebView."""
    args = sys.argv[1:] if argumentos is None else argumentos
    return "tk" if "--tk" in args else "web"


def _tratar_excecao_global(tipo, valor, tb):
    """Registra exceção não capturada e avisa sem fechar silenciosamente."""
    logger = configurar_logger()
    logger.critical(
        "Exceção não tratada: %s: %s\n%s",
        tipo.__name__,
        valor,
        "".join(traceback.format_tb(tb)),
    )

    try:
        import customtkinter as ctk
        from ui.alert_modal import AlertModal
        if ctk.CTk._top_level_list:
            top = ctk.CTk._top_level_list[0]
            AlertModal(
                top,
                "Erro Inesperado",
                f"{tipo.__name__}: {valor}",
                ["O erro foi registrado no arquivo de log do sistema."],
            )
        else:
            from tkinter import messagebox
            messagebox.showerror(
                "Erro Inesperado",
                f"Ocorreu um erro inesperado:\n\n{tipo.__name__}: {valor}"
            )
    except Exception:
        pass


def iniciar_web() -> None:
    """Abre a interface WebView (padrão)."""
    from webview_shell import main as iniciar_shell

    iniciar_shell(ui=True)


def iniciar_tk() -> None:
    """Abre a interface legada Tk (backup; `python main.py --tk`)."""
    import customtkinter as ctk

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    from ui.main_window import MainWindow

    app = MainWindow()
    configurar_logger().info("Janela principal criada")
    app.mainloop()


def main() -> None:
    # Configurar logger antes de tudo
    logger = configurar_logger()
    logger.info("Iniciando aplicação Contracto")

    # Segunda cópia? Avisa e encerra sem abrir outra janela.
    try:
        guarda_instancia = InstanciaUnica()
        guarda_instancia.adquirir()
    except InstanciaJaEmExecucao:
        logger.info("Segunda instância bloqueada pelo mutex.")
        from tkinter import messagebox
        try:
            messagebox.showinfo(
                "Contracto",
                "O Contracto já está aberto. Use a janela existente.",
            )
        except Exception:
            pass
        sys.exit(0)
    except OSError:
        logger.warning("Mutex indisponível; seguindo sem trava de instância.")
        guarda_instancia = None

    # Instalar tratamento global de exceções
    sys.excepthook = _tratar_excecao_global

    modo = escolher_interface()
    logger.info(f"Interface selecionada: {modo}")
    try:
        if modo == "tk":
            iniciar_tk()
        else:
            iniciar_web()
    finally:
        if guarda_instancia is not None:
            guarda_instancia.liberar()
    logger.info("Aplicação encerrada")


if __name__ == "__main__":
    main()
