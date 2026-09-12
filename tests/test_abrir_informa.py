"""Abrir arquivo/pasta informa sucesso ou falha (sem exceção silenciosa)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))


class TestAbrirInformaFalha(unittest.TestCase):
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
        from ui.success_modal import SuccessModal

        try:
            if SuccessModal._instancia_ativa is not None:
                SuccessModal._instancia_ativa.dismiss()
        except Exception:
            pass

    def _modal(self, destino):
        from ui.success_modal import SuccessModal

        return SuccessModal(
            self.root, "Ok", "Sub", arquivos_gerados=[], pasta_destino=destino
        )

    def test_inexistente_devolve_false(self):
        with tempfile.TemporaryDirectory() as d:
            modal = self._modal(Path(d))
            try:
                self.assertFalse(modal._abrir_arquivo(Path(d) / "falta.pdf"))
                modal.pasta_destino = Path(d) / "falta"
                self.assertFalse(modal._abrir_pasta_destino())
            finally:
                modal.dismiss()

    def test_valido_tenta_abrir_uma_vez(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            (pasta / "doc.pdf").write_bytes(b"%PDF-1.4")
            modal = self._modal(pasta)
            try:
                with patch("os.startfile", create=True) as abrir:
                    self.assertTrue(modal._abrir_arquivo(pasta / "doc.pdf"))
                    abrir.assert_called_once()
                with patch("os.startfile", create=True) as abrir:
                    self.assertTrue(modal._abrir_pasta_destino())
                    abrir.assert_called_once()
            finally:
                modal.dismiss()


if __name__ == "__main__":
    unittest.main()
