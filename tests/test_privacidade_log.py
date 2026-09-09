"""Mascaramento de dados pessoais no log.

Garante que CPF, CNPJ e e-mail nunca sejam gravados em claro,
incluindo mensagens de exceção e tracebacks.
"""

import io
import logging
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.logger import FormatadorPrivado, configurar_logger, mascarar_dados_pessoais


class TestMascararDadosPessoais(unittest.TestCase):
    def test_cpf_formatado(self):
        texto = mascarar_dados_pessoais("cliente 529.982.247-25 gerado")
        self.assertNotIn("529.982.247-25", texto)
        self.assertIn("***.***.***-**", texto)

    def test_cpf_sem_formatacao(self):
        texto = mascarar_dados_pessoais("cpf 52998224725 fim")
        self.assertNotIn("52998224725", texto)

    def test_cnpj_formatado(self):
        texto = mascarar_dados_pessoais("empresa 11.222.333/0001-81 ok")
        self.assertNotIn("11.222.333/0001-81", texto)

    def test_email_preserva_dominio(self):
        texto = mascarar_dados_pessoais("contato maria.silva@exemplo.com.br aqui")
        self.assertNotIn("maria.silva@", texto)
        self.assertIn("***@exemplo.com.br", texto)

    def test_texto_comum_intacto(self):
        texto = "Gerando documento 3/5 em PDF/A-2b"
        self.assertEqual(mascarar_dados_pessoais(texto), texto)


class TestFormatadorPrivado(unittest.TestCase):
    def _registrar(self, mensagem, **kwargs):
        logger = logging.getLogger("contracto.teste_privacidade")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        fluxo = io.StringIO()
        handler = logging.StreamHandler(fluxo)
        handler.setFormatter(FormatadorPrivado("%(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
        try:
            logger.error(mensagem, **kwargs)
        except TypeError:
            logger.error(mensagem)
        return fluxo.getvalue()

    def test_mensagem_com_cpf_mascarada(self):
        saida = self._registrar("Falha ao abrir 529.982.247-25")
        self.assertNotIn("529.982.247-25", saida)

    def test_traceback_mascarado(self):
        try:
            raise ValueError("cliente maria@exemplo.com falhou")
        except ValueError:
            logger = logging.getLogger("contracto.teste_privacidade_tb")
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)
            fluxo = io.StringIO()
            handler = logging.StreamHandler(fluxo)
            handler.setFormatter(FormatadorPrivado("%(message)s"))
            logger.addHandler(handler)
            logger.propagate = False
            logger.exception("erro ao gerar")
            saida = fluxo.getvalue()
        self.assertNotIn("maria@exemplo.com", saida)
        self.assertIn("ValueError", saida)

    def test_configurar_logger_usa_formatador_privado(self):
        import tempfile
        from unittest.mock import patch

        import utils.logger as modulo_logger

        with tempfile.TemporaryDirectory() as d:
            with patch(
                "utils.config_manager._diretorio_config",
                return_value=Path(d),
            ):
                modulo_logger._logger_configurado = False
                try:
                    logger = modulo_logger.configurar_logger()
                    formatadores = [
                        type(h.formatter).__name__
                        for h in logger.handlers
                        if h.formatter is not None
                    ]
                    self.assertIn("FormatadorPrivado", formatadores)
                finally:
                    for h in list(logger.handlers):
                        h.close()
                        logger.removeHandler(h)
                    modulo_logger._logger_configurado = False


if __name__ == "__main__":
    unittest.main()
