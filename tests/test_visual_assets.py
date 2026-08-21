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
    LOADER_FILENAMES,
    get_next_loader_path,
    reset_loader_cycle,
)
from ui.theme import get_icon
import version


class TestVisualAssets(unittest.TestCase):
    """Valida a existência dos 30 ícones vetoriais e 10 loaders GIF dinâmicos."""

    def setUp(self):
        reset_loader_cycle()

    def test_version_is_v4_3(self):
        """Verifica se a versão centralizada está definida como 4.3."""
        self.assertEqual(version.__version__, "4.3")

    def test_all_10_loaders_exist(self):
        """Verifica se todos os 10 arquivos GIF de spinner existem fisicamente."""
        self.assertEqual(len(LOADER_FILENAMES), 10)
        for nome in LOADER_FILENAMES:
            caminho = app_dir / "assets" / "loaders" / nome
            self.assertTrue(caminho.exists(), f"Loader {nome} não encontrado em {caminho}")

    def test_loader_rotation_cycle(self):
        """Verifica se a rotação circular de loaders avança corretamente e recomeça após 10 itens."""
        reset_loader_cycle()
        primeiro = get_next_loader_path()
        self.assertEqual(primeiro.name, LOADER_FILENAMES[0])

        for i in range(1, 10):
            p = get_next_loader_path()
            self.assertEqual(p.name, LOADER_FILENAMES[i])

        # O 11º deve voltar ao início (índice 0)
        reinicio = get_next_loader_path()
        self.assertEqual(reinicio.name, LOADER_FILENAMES[0])

    def test_get_icon_loads_valid_ctk_image(self):
        """Verifica se a função get_icon retorna CTkImage com sucesso para ícones padrão."""
        icon_names = ["home", "profiles", "settings", "help", "calendar", "location", "advance", "back", "success", "folder", "trash"]
        for nome in icon_names:
            dark_file = app_dir / "assets" / "icons" / f"{nome}_dark.png"
            light_file = app_dir / "assets" / "icons" / f"{nome}_light.png"
            self.assertTrue(dark_file.exists(), f"Ícone escuro {dark_file} não existe.")
            self.assertTrue(light_file.exists(), f"Ícone claro {light_file} não existe.")

            img = get_icon(nome, (20, 20))
            self.assertIsNotNone(img)


if __name__ == "__main__":
    unittest.main()
