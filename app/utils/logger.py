"""
Logger centralizado da aplicação.

Arquivo com rotação (5 × 2 MB) em `%APPDATA%/Contracto/logs/app.log`,
nível detalhado em desenvolvimento e resumido no executável.
CPF, CNPJ e e-mail são mascarados antes da gravação.
"""

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_logger_configurado = False

# Arquivo de log: 2 MB por arquivo, mantendo os 5 mais recentes.
_TAMANHO_MAXIMO_LOG = 2 * 1024 * 1024
_ARQUIVOS_LOG_GUARDADOS = 5

# CPF formatado (000.000.000-00) ou sequência isolada de 11 dígitos.
_PADRAO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\b\d{11}\b")
# CNPJ formatado (00.000.000/0000-00) ou sequência isolada de 14 dígitos.
_PADRAO_CNPJ = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\b\d{14}\b")
# E-mail (preserva o domínio para depuração).
_PADRAO_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def mascarar_dados_pessoais(texto: str) -> str:
    """Oculta CPF, CNPJ e e-mail antes de registrar no log."""
    texto = _PADRAO_CPF.sub("***.***.***-**", texto)
    texto = _PADRAO_CNPJ.sub("**.***.***/****-**", texto)
    return _PADRAO_EMAIL.sub(r"***@\1", texto)


class FormatadorPrivado(logging.Formatter):
    """Aplica o mascaramento ao texto final (mensagem + traceback)."""

    def format(self, record: logging.LogRecord) -> str:
        return mascarar_dados_pessoais(super().format(record))


def configurar_logger() -> logging.Logger:
    """Configura e retorna o logger principal da aplicação.

    O log é salvo em `%APPDATA%/Contracto/logs/app.log`, com rotação
    automática ao atingir 2 MB (guarda os 5 arquivos mais recentes).
    """
    global _logger_configurado

    em_producao = bool(getattr(sys, "_MEIPASS", None))
    logger = logging.getLogger("contracto")

    if _logger_configurado:
        return logger

    logger.setLevel(logging.INFO if em_producao else logging.DEBUG)
    
    # Formato compacto com timestamp e mascaramento de dados pessoais
    formato = FormatadorPrivado(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Handler para arquivo
    from utils import config_manager
    
    # Em produção e desenvolvimento, salvar na pasta %APPDATA%/Contracto/logs
    log_dir = config_manager._diretorio_config() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = log_dir / "app.log"
    try:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=_TAMANHO_MAXIMO_LOG,
            backupCount=_ARQUIVOS_LOG_GUARDADOS,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO if em_producao else logging.DEBUG)
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)
    except OSError:
        # Se não conseguir criar o arquivo de log, segue sem ele
        pass

    # Handler para console (apenas em desenvolvimento)
    if not em_producao:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formato)
        logger.addHandler(console_handler)
    
    _logger_configurado = True
    return logger


def obter_logger(nome: str = "contracto") -> logging.Logger:
    """Retorna um logger filho do logger principal."""
    return logging.getLogger(f"contracto.{nome}")
