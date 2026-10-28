"""
Testes de desempenho e benchmarking para a suite de otimizações de performance do Contracto.
"""

import sys
import time
import unittest
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from utils import config_manager
from utils import profile_manager


class TestPerformance(unittest.TestCase):
    """Valida a eficiência dos caches em memória e componentes ultraleves."""

    def setUp(self):
        config_manager.invalidar_cache()
        profile_manager.invalidar_cache()

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


if __name__ == "__main__":
    unittest.main()
