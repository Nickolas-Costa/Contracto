"""
Testes de desempenho e benchmarking para a suite de otimizações de performance do Contracto.
"""

import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import config_manager
from utils import profile_manager
from ui import theme


class TestPerformance(unittest.TestCase):
    """Valida a eficiência dos caches em memória e componentes ultraleves."""

    def setUp(self):
        config_manager.invalidar_cache()
        profile_manager.invalidar_cache()
        theme.reload_theme()

    def test_config_manager_cache_speed(self):
        """Valida que 10.000 leituras de configuração ocorrem em menos de 0.1 segundos."""
        # Primeira leitura (carrega cache)
        _ = config_manager.obter("perfil_ativo")

        inicio = time.perf_counter()
        for _ in range(10000):
            _ = config_manager.obter("perfil_ativo")
            _ = config_manager.obter("local_padrao")
        duracao = time.perf_counter() - inicio

        self.assertLess(duracao, 0.10, f"Tempo excessivo em config_manager cache: {duracao:.4f}s")

    def test_profile_manager_cache_speed(self):
        """Valida que 5.000 buscas de perfil ocorrem diretamente da memória em menos de 0.30 segundos."""
        # Primeira leitura
        _ = profile_manager.obter_perfil("MCMV")

        inicio = time.perf_counter()
        for _ in range(5000):
            _ = profile_manager.obter_perfil("MCMV")
            _ = profile_manager.listar_nomes_perfis()
        duracao = time.perf_counter() - inicio

        self.assertLess(duracao, 0.30, f"Tempo excessivo em profile_manager cache: {duracao:.4f}s")

    def test_theme_color_cache_speed(self):
        """Valida que 50.000 acessos a cores e temas ocorrem em menos de 0.1 segundos."""
        inicio = time.perf_counter()
        for _ in range(50000):
            _ = theme.get_color_primary()
            _ = theme.get_color_primary_hover()
            _ = theme.get_color_primary_light()
        duracao = time.perf_counter() - inicio

        self.assertLess(duracao, 0.10, f"Tempo excessivo em theme cache: {duracao:.4f}s")

    def test_scroll_do_mouse_avanca_oito_unidades_por_giro(self):
        import customtkinter as ctk

        theme._configurar_rolagem()
        canvas = MagicMock()
        canvas.yview.return_value = (0.0, 0.5)
        scroll = SimpleNamespace(
            _check_if_valid_scroll=lambda _widget: True,
            _shift_pressed=False,
            _parent_canvas=canvas,
        )

        ctk.CTkScrollableFrame._mouse_wheel_all(
            scroll, SimpleNamespace(widget=object(), delta=-120)
        )

        canvas.yview_scroll.assert_called_once_with(8, "units")

    def test_loading_modal_lifecycle_is_instant(self):
        """Valida criação e destruição instantânea do LoadingModal ultraleve sem travamentos."""
        import customtkinter as ctk
        from ui.loading_modal import LoadingModal

        root = ctk.CTk()
        root.withdraw()
        try:
            inicio = time.perf_counter()
            modal = LoadingModal(root, message="Teste Rápido", submessage="Aguarde...")
            modal.atualizar_etapa(1, 3, "Validando...")
            modal.dismiss()
            duracao = time.perf_counter() - inicio

            self.assertLess(duracao, 1.5, f"LoadingModal demorou muito para inicializar/fechar: {duracao:.4f}s")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
