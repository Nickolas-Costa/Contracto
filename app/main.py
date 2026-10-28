"""Entry-point da aplicação Contracto.

A interface é a WebView sobre a API local em loopback (a antiga interface
Tkinter foi aposentada na v5.0.0, ADR 0028). Aqui fica só a inicialização
mínima e previsível: instância única, shell WebView e registro de falhas não
capturadas para diagnóstico.
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
        # Aviso nativo do Windows: a janela WebView pode nem existir neste ponto.
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None,
            "Ocorreu um erro inesperado:" + chr(10)*2 + f"{tipo.__name__}: {valor}" + chr(10)*2
            + "O erro foi registrado no log do sistema.",
            "Contracto — erro inesperado",
            0x10,
        )
    except Exception:
        pass


def iniciar_web() -> None:
    """Inicializa o shell WebView, que é a interface padrão da aplicação."""
    from webview_shell import main as iniciar_shell

    iniciar_shell(ui=True)


def main() -> None:
    # O logger deve existir antes de qualquer etapa crítica para registrar falhas
    # de inicialização com contexto útil de diagnóstico.
    logger = configurar_logger()
    logger.info("Iniciando aplicação Contracto")

    # Impede múltiplas instâncias da aplicação e evita sobreposição de janelas.
    # A segunda execução só traz a janela existente para frente e sai em
    # silêncio — sem nenhum modal de aviso.
    try:
        guarda_instancia = InstanciaUnica()
        guarda_instancia.adquirir()
    except InstanciaJaEmExecucao:
        logger.info("Segunda instância: focando janela existente e encerrando sem aviso.")
        try:
            from utils.instancia_unica import focar_janela_existente
            focar_janela_existente()
        except Exception:
            pass
        sys.exit(0)
    except OSError:
        logger.warning("Mutex indisponível; seguindo sem trava de instância.")
        guarda_instancia = None

    # Instalar tratamento global de exceções
    sys.excepthook = _tratar_excecao_global

    try:
        iniciar_web()
    finally:
        if guarda_instancia is not None:
            guarda_instancia.liberar()
    logger.info("Aplicação encerrada")


if __name__ == "__main__":
    main()
