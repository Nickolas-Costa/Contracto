"""Rotação do arquivo de log e níveis por ambiente."""

import logging
import sys
import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import utils.logger as modulo_logger


class TestRotacaoENiveis(unittest.TestCase):
    def _fechar(self, logger: logging.Logger) -> None:
        for handler in list(logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
            logger.removeHandler(handler)

    def _configurar(self, diretorio: Path, meipass):
        if meipass is None:
            if hasattr(modulo_logger.sys, "_MEIPASS"):
                delattr(modulo_logger.sys, "_MEIPASS")
        else:
            modulo_logger.sys._MEIPASS = meipass
        with patch(
            "utils.config_manager._diretorio_config", return_value=diretorio
        ):
            modulo_logger._logger_configurado = False
            try:
                return modulo_logger.configurar_logger()
            finally:
                modulo_logger._logger_configurado = False

    def tearDown(self):
        self._fechar(logging.getLogger("contracto"))
        if hasattr(modulo_logger.sys, "_MEIPASS"):
            delattr(modulo_logger.sys, "_MEIPASS")

    def test_arquivo_usa_rotacao_2mb_5_copias(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._configurar(Path(d), None)
            try:
                rotativos = [
                    h for h in logger.handlers
                    if isinstance(h, RotatingFileHandler)
                ]
                self.assertEqual(len(rotativos), 1)
                self.assertEqual(rotativos[0].maxBytes, 2 * 1024 * 1024)
                self.assertEqual(rotativos[0].backupCount, 5)
            finally:
                self._fechar(logger)

    def test_desenvolvimento_registra_detalhe_e_mostra_console(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._configurar(Path(d), None)
            try:
                self.assertEqual(logger.level, logging.DEBUG)
                consoles = [
                    h for h in logger.handlers
                    if isinstance(h, logging.StreamHandler)
                    and not isinstance(h, RotatingFileHandler)
                ]
                self.assertEqual(len(consoles), 1)
            finally:
                self._fechar(logger)

    def test_producao_resumida_e_sem_console(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._configurar(Path(d), "C:\\fake")
            try:
                self.assertEqual(logger.level, logging.INFO)
                consoles = [
                    h for h in logger.handlers
                    if isinstance(h, logging.StreamHandler)
                    and not isinstance(h, RotatingFileHandler)
                ]
                self.assertEqual(len(consoles), 0)
            finally:
                self._fechar(logger)

    def test_rotacao_acontece_ao_estourar(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._configurar(Path(d), None)
            try:
                for handler in list(logger.handlers):
                    if isinstance(handler, RotatingFileHandler):
                        handler.maxBytes = 200
                        handler.backupCount = 2
                for i in range(30):
                    logger.debug("linha de preenchimento %03d " % i + "x" * 40)
                for handler in logger.handlers:
                    try:
                        handler.flush()
                    except Exception:
                        pass
                self.assertTrue((Path(d) / "logs" / "app.log.1").exists())
            finally:
                self._fechar(logger)


if __name__ == "__main__":
    unittest.main()
