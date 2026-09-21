"""Entry-point da aplicação Contracto.

A versão padrão utiliza a interface WebView sobre a API local em loopback.
A interface legada em Tkinter continua disponível como fallback operacional e
para manutenção de compatibilidade, sendo aberta com `python main.py --tk`.

A lógica principal aqui é manter a inicialização mínima e previsível: validação
existência de uma instância única, escolha da interface e registro de falhas
não capturadas para diagnóstico.
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
    """Define a interface ativa do processo.

    Qualquer argumento diferente de `--tk` mantém a interface moderna WebView.
    A escolha centraliza a decisão em um único ponto para facilitar manutenção e
    testes de boot da aplicação.
    """
    args = sys.argv[1:] if argumentos is None else argumentos
    return "tk" if "--tk" in args else "web"


def _tratar_excecao_global(tipo, valor, tb):
    """Registra falhas não capturadas sem esconder o problema ao usuário.

    Centraliza o tratamento de exceções globais para facilitar diagnóstico de
    incidentes em produção e manter uma mensagem legível em caso de erro crítico.
    """
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
    """Inicializa o shell WebView, que é a interface padrão da aplicação."""
    from webview_shell import main as iniciar_shell

    iniciar_shell(ui=True)


def iniciar_tk() -> None:
    """Inicializa o cliente legada em Tkinter para compatibilidade e manutenção.

    A abertura por esse caminho é intencionalmente explícita e não deve ser usada
    como padrão de uso em desenvolvimento normal.
    """
    import customtkinter as ctk

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    from ui.main_window import MainWindow

    app = MainWindow()
    configurar_logger().info("Janela principal criada")
    app.mainloop()


def main() -> None:
    # O logger deve existir antes de qualquer etapa crítica para registrar falhas
    # de inicialização com contexto útil de diagnóstico.
    logger = configurar_logger()
    logger.info("Iniciando aplicação Contracto")

    # Impede múltiplas instâncias da aplicação e evita sobreposição de janelas.
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
