"""Contraste da insígnia do toast (glifo branco sobre a cor do tipo)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

LIMITE_AA = 4.5


def _luminancia(hex_cor: str) -> float:
    h = hex_cor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def contraste_com_branco(hex_cor: str) -> float:
    claro, escuro = sorted([_luminancia(hex_cor), _luminancia("#FFFFFF")], reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


class TestContrasteToast(unittest.TestCase):
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

    def test_insignias_fixas_passam_aa(self):
        from ui.feedback_toast import FeedbackToast

        for tipo in ("success", "warning", "error"):
            toast = FeedbackToast(self.root, "msg", type=tipo)
            try:
                cor = toast.type_config[tipo]["color"]
                self.assertGreaterEqual(
                    contraste_com_branco(cor), LIMITE_AA, tipo
                )
            finally:
                toast.destroy()


if __name__ == "__main__":
    unittest.main()
