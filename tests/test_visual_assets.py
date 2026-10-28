"""Versão centralizada e ícones do aplicativo (a UI de produção é a WebView)."""

import sys
import unittest
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

import version


class TestVisualAssets(unittest.TestCase):
    def test_version_is_current(self):
        """Verifica se a versão centralizada está definida como 5.0.0."""
        self.assertEqual(version.__version__, "5.0.0")

    def test_icones_do_aplicativo_existem(self):
        """O instalador, o atalho e o PyInstaller dependem destes arquivos."""
        for nome in ("app_icon.ico", "app_icon.png", "LOGO_OFICIAL_CONTRACTO.png"):
            self.assertTrue((app_dir / "assets" / "icons" / nome).is_file(), nome)


if __name__ == "__main__":
    unittest.main()
