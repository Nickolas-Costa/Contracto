"""Avisos e boas-vindas: contenção na tela, Escape e texto do guia."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))


class TestToastWelcomeTeclado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import customtkinter as ctk

        cls.root = ctk.CTk()
        cls.root.geometry("900x700")
        cls.root.update()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def tearDown(self):
        from ui import theme

        theme._ICONS_CACHE.clear()
        try:
            ativo = getattr(self.root, "_feedback_toast_ativo", None)
            if ativo is not None and ativo.winfo_exists():
                ativo._dismiss()
        except Exception:
            pass

    def test_toast_cabe_na_janela(self):
        from ui.feedback_toast import show_toast

        toast = show_toast(
            self.root,
            "Modo Avançado ativado. Agora com o conjunto completo de formulários do contrato.",
            "info",
        )
        self.root.update()
        self.root.update()
        self.assertLessEqual(
            toast.winfo_x() + toast.winfo_width(), self.root.winfo_width()
        )
        self.assertGreaterEqual(toast.winfo_x(), 0)

    def test_escape_dispensa_toast(self):
        from ui.feedback_toast import show_toast

        toast = show_toast(self.root, "Olá", "success")
        self.root.focus_force()
        self.root.update()
        self.root.event_generate("<Escape>")
        self.root.update()
        self.assertFalse(toast.winfo_exists())

    def test_boas_vindas_nao_se_esconde_sozinho(self):
        from ui.welcome_modal import WelcomeModal

        modal = WelcomeModal(self.root)
        try:
            self.assertTrue(modal.card._contracto_fixo)
            self.assertTrue(modal.overlay._contracto_fixo)
        finally:
            modal.dismiss()

    def test_texto_guia_sem_jargao(self):
        import inspect

        from ui import welcome_modal

        fonte = inspect.getsource(welcome_modal)
        for trecho in ("gerente", "pontuação automática", "pontuacao automatica"):
            self.assertNotIn(trecho, fonte)


if __name__ == "__main__":
    unittest.main()
