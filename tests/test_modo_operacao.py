"""
Testes unitários para a separação de modos (Contrato/Avançado x Simples) e filtragem de perfis.
"""

import unittest

from app.utils.profile_manager import (
    carregar_perfis,
    listar_perfis_por_modo,
    listar_nomes_perfis_por_modo,
)


class TestModosOperacao(unittest.TestCase):
    """Valida o isolamento dos perfis entre Modo Contrato (Avançado) e Modo Simples."""

    def setUp(self):
        carregar_perfis(forcar_disco=True)

    def test_perfis_modo_contrato(self):
        perfis_contrato = listar_perfis_por_modo("contrato")
        nomes = [p.nome for p in perfis_contrato]

        self.assertIn("MCMV", nomes)
        self.assertIn("SBPE", nomes)
        self.assertNotIn("Form Cliente", nomes)
        self.assertNotIn("ITBI", nomes)
        self.assertNotIn("Isenção de Tributos", nomes)

    def test_perfis_modo_simples(self):
        perfis_simples = listar_perfis_por_modo("simples")
        nomes = [p.nome for p in perfis_simples]

        self.assertIn("Form Cliente", nomes)
        self.assertIn("ITBI", nomes)
        self.assertIn("Isenção de Tributos", nomes)
        self.assertNotIn("MCMV", nomes)
        self.assertNotIn("SBPE", nomes)

    def test_listar_nomes_perfis_por_modo(self):
        nomes_avancado = listar_nomes_perfis_por_modo("avancado")
        nomes_simples = listar_nomes_perfis_por_modo("simples")

        self.assertIn("MCMV", nomes_avancado)
        self.assertIn("Form Cliente", nomes_simples)


if __name__ == "__main__":
    unittest.main()
