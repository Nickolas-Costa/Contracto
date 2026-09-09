"""BaseModal: herança única, instância única, teclado e foco."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))


class TestBaseModal(unittest.TestCase):
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
        from ui.alert_modal import AlertModal
        from ui.base_modal import BaseModal
        from ui.confirm_modal import ConfirmModal
        from ui.loading_modal import LoadingModal
        from ui.success_modal import SuccessModal
        from ui.welcome_modal import WelcomeModal
        from ui.word_travado_modal import WordTravadoModal

        for cls in (
            AlertModal, ConfirmModal, LoadingModal,
            SuccessModal, WelcomeModal, WordTravadoModal, BaseModal,
        ):
            try:
                if cls._instancia_ativa is not None:
                    cls._instancia_ativa.dismiss()
            except Exception:
                pass

    def test_todos_herdam_base(self):
        from ui.alert_modal import AlertModal
        from ui.base_modal import BaseModal
        from ui.confirm_modal import ConfirmModal
        from ui.loading_modal import LoadingModal
        from ui.success_modal import SuccessModal
        from ui.welcome_modal import WelcomeModal
        from ui.word_travado_modal import WordTravadoModal

        for cls in (
            AlertModal, ConfirmModal, LoadingModal,
            SuccessModal, WelcomeModal, WordTravadoModal,
        ):
            self.assertTrue(issubclass(cls, BaseModal), cls.__name__)

    def test_alerta_sem_lista_nao_quebra(self):
        from ui.alert_modal import AlertModal

        modal = AlertModal(self.root, "Título", "Subtítulo")
        self.assertTrue(modal.card.winfo_exists())
        modal.dismiss()
        self.assertFalse(modal.card.winfo_exists())

    def test_segunda_abertura_fecha_anterior(self):
        from ui.alert_modal import AlertModal

        primeiro = AlertModal(self.root, "A", "a", ["e1"])
        segundo = AlertModal(self.root, "B", "b", ["e2"])
        self.assertFalse(primeiro.card.winfo_exists())
        self.assertTrue(segundo.card.winfo_exists())
        self.assertIs(AlertModal._instancia_ativa, segundo)
        segundo.dismiss()

    def test_escape_fecha_alerta(self):
        from ui.alert_modal import AlertModal

        modal = AlertModal(self.root, "A", "a", ["e1"])
        modal.card.event_generate("<Escape>")
        modal.card.update()
        self.assertFalse(modal.card.winfo_exists())
        self.assertIsNone(AlertModal._instancia_ativa)

    def test_grab_so_nos_dialogos_bloqueantes(self):
        from ui.alert_modal import AlertModal
        from ui.loading_modal import LoadingModal

        alerta = AlertModal(self.root, "A", "a", ["e1"])
        try:
            self.assertEqual(self.root.grab_current(), alerta.card)
        finally:
            alerta.dismiss()
        carga = LoadingModal(self.root, message="Carregando...")
        try:
            self.assertIsNone(self.root.grab_current())
        finally:
            carga.dismiss()

    def test_confirmar_e_cancelar(self):
        from ui.confirm_modal import ConfirmModal

        feitas = []
        modal = ConfirmModal(
            self.root, "T?", "S",
            on_confirm=lambda: feitas.append("ok"),
            on_cancel=lambda: feitas.append("no"),
        )
        modal._do_confirm()
        self.assertEqual(feitas, ["ok"])
        modal2 = ConfirmModal(self.root, "T?", "S", on_cancel=lambda: feitas.append("no"))
        modal2._do_cancel()
        self.assertEqual(feitas, ["ok", "no"])


if __name__ == "__main__":
    unittest.main()
