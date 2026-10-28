"""Abrir pasta (puro, sem Tk): rejeita o que não é diretório existente."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.files_fs import abrir_pasta


class TestAbrirPastaCompartilhado(unittest.TestCase):
    def test_inexistente_devolve_false(self):
        self.assertFalse(abrir_pasta(Path("pasta_que_nao_existe")))

    def test_valida_abre_uma_vez(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("os.startfile", create=True) as abrir:
                self.assertTrue(abrir_pasta(Path(d)))
                abrir.assert_called_once()


if __name__ == "__main__":
    unittest.main()
