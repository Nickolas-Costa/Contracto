"""
Testes unitários para o módulo de loaders animados, ciclo de rotação e carregamento de ícones adaptativos.
"""

import sys
import unittest
from pathlib import Path

# Adiciona o diretório app ao path
app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from ui.animated_loader import (
    SimpleLoader,
    AnimatedGifLabel,
)
from ui.theme import get_icon
import version


class TestVisualAssets(unittest.TestCase):
    """Valida a existência dos ícones vetoriais e o componente de carregamento leve."""

    def test_version_is_v4_5_9(self):
        """Verifica se a versão centralizada está definida como 4.5.9."""
        self.assertEqual(version.__version__, "4.5.9")

    def test_simple_loader_instantiation(self):
        """Verifica se o componente SimpleLoader pode ser instanciado sem erros."""
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()
        try:
            loader = SimpleLoader(root, width=150, height=6)
            self.assertIsNotNone(loader)
            loader.stop_animation()
            
            compat_label = AnimatedGifLabel(root)
            self.assertIsNotNone(compat_label)
            compat_label.stop_animation()
        finally:
            root.destroy()

    def test_get_icon_loads_valid_ctk_image(self):
        """Verifica se a função get_icon retorna CTkImage com sucesso para ícones padrão."""
        icon_names = [
            "home", "profiles", "settings", "help", "question_circle",
            "calendar", "location", "advance", "back", "success", "folder",
            "trash", "check", "edit", "copy", "user_add", "finish"
        ]
        for nome in icon_names:
            dark_file = app_dir / "assets" / "icons" / f"{nome}_dark.png"
            light_file = app_dir / "assets" / "icons" / f"{nome}_light.png"
            self.assertTrue(dark_file.exists(), f"Ícone escuro {dark_file} não existe.")
            self.assertTrue(light_file.exists(), f"Ícone claro {light_file} não existe.")

            img = get_icon(nome, (20, 20))
            self.assertIsNotNone(img)

    def test_main_window_initialization(self):
        """Verifica se MainWindow inicializa e carrega todas as telas e ícones sem exceções."""
        from ui.main_window import MainWindow
        win = MainWindow()
        win.withdraw()
        try:
            self.assertIsNotNone(win.icon_home)
            self.assertIsNotNone(win.icon_profiles)
            self.assertIsNotNone(win.icon_settings)
            self.assertIsNotNone(win.icon_calendar)
            self.assertIsNotNone(win.icon_help)

            # Testar navegação entre telas
            win._mostrar_tela("perfis")
            win._mostrar_tela("config")
            win._mostrar_tela("inicio")
        finally:
            win.destroy()


if __name__ == "__main__":
    unittest.main()
