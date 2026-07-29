"""
Logger centralizado da aplicação.

Configura logging para arquivo e console com formatação padronizada.
Em produção (executável), o log é salvo ao lado do executável.
Em desenvolvimento, é salvo na pasta do projeto.
"""

import logging
import sys
from pathlib import Path


_logger_configurado = False


def configurar_logger() -> logging.Logger:
    """Configura e retorna o logger principal da aplicação.
    
    O log é salvo em `app.log` no diretório do executável (produção)
    ou no diretório de trabalho atual (desenvolvimento).
    """
    global _logger_configurado
    
    logger = logging.getLogger("contracto")
    
    if _logger_configurado:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formato compacto com timestamp
    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Handler para arquivo
    if getattr(sys, "_MEIPASS", None):
        # Em produção: log ao lado do executável
        log_dir = Path(sys.executable).parent
    else:
        # Em desenvolvimento: log na raiz do projeto
        log_dir = Path(__file__).resolve().parent.parent
    
    log_path = log_dir / "app.log"
    try:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)
    except OSError:
        # Se não conseguir criar o arquivo de log, segue sem ele
        pass
    
    # Handler para console (apenas em desenvolvimento)
    if not getattr(sys, "_MEIPASS", None):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formato)
        logger.addHandler(console_handler)
    
    _logger_configurado = True
    return logger


def obter_logger(nome: str = "contracto") -> logging.Logger:
    """Retorna um logger filho do logger principal."""
    return logging.getLogger(f"contracto.{nome}")
