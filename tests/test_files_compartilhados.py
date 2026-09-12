"""Utilitários de arquivo da interface (abrir pasta, preencher entry)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.files import abrir_pasta, atualizar_entry


class TestAbrirPastaCompartilhado(unittest.TestCase):
    def test_inexistente_devolve_false(self):
        self.assertFalse(abrir_pasta(Path("pasta_que_nao_existe")))

    def test_valida_abre_uma_vez(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("os.startfile", create=True) as abrir:
                self.assertTrue(abrir_pasta(Path(d)))
                abrir.assert_called_once()


class TestAtualizarEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import customtkinter as ctk

        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def tearDown(self):
        from ui import theme

        theme._ICONS_CACHE.clear()

    def test_editavel_e_somente_leitura(self):
        import customtkinter as ctk

        editavel = ctk.CTkEntry(self.root)
        somente = ctk.CTkEntry(self.root)
        try:
            atualizar_entry(editavel, "abc")
            self.assertEqual(editavel.get(), "abc")
            self.assertEqual(str(editavel.cget("state")), "normal")
            atualizar_entry(somente, "xyz", somente_leitura=True)
            self.assertEqual(somente.get(), "xyz")
            self.assertEqual(str(somente.cget("state")), "disabled")
        finally:
            editavel.destroy()
            somente.destroy()

    def test_delegadores_mantem_comportamento(self):
        from ui.main_window import MainWindow
        from utils.files import atualizar_entry

        import customtkinter as ctk

        self.assertFalse(MainWindow._abrir_pasta(Path("pasta_que_nao_existe")))
        entrada = ctk.CTkEntry(self.root)
        try:
            atualizar_entry(entrada, "texto", somente_leitura=True)
            self.assertEqual(entrada.get(), "texto")
            self.assertEqual(str(entrada.cget("state")), "disabled")
        finally:
            entrada.destroy()


if __name__ == "__main__":
    unittest.main()
