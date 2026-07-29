"""
Ponto de entrada da aplicação.

Executar com:
    python main.py
(a partir da pasta `app/`)
"""

import sys
import traceback

import customtkinter as ctk

from utils.logger import configurar_logger


def _tratar_excecao_global(tipo, valor, tb):
    """Tratamento global de exceções não capturadas.
    
    Registra no log e exibe uma mensagem amigável ao usuário,
    evitando que a aplicação feche silenciosamente.
    """
    logger = configurar_logger()
    logger.critical(
        "Exceção não tratada: %s: %s\n%s",
        tipo.__name__,
        valor,
        "".join(traceback.format_tb(tb)),
    )
    
    # Tentar mostrar uma mensagem para o usuário
    try:
        from tkinter import messagebox
        messagebox.showerror(
            "Erro Inesperado",
            f"Ocorreu um erro inesperado:\n\n{tipo.__name__}: {valor}\n\n"
            f"O erro foi registrado no arquivo de log.\n"
            f"Se o problema persistir, entre em contato com o suporte."
        )
    except Exception:
        pass


def main() -> None:
    # Configurar logger antes de tudo
    logger = configurar_logger()
    logger.info("Iniciando aplicação Contracto")
    
    # Instalar tratamento global de exceções
    sys.excepthook = _tratar_excecao_global
    
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    from ui.main_window import MainWindow
    
    app = MainWindow()
    logger.info("Janela principal criada")
    app.mainloop()
    logger.info("Aplicação encerrada")


if __name__ == "__main__":
    main()
