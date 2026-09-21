"""Paridade Tk -> WebView: todos os perfis reais compõem, paginam e validam."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestParidadePerfis(unittest.TestCase):
    def test_todos_perfis_compoem(self):
        import sys
        sys.path.insert(0, str(ROOT / "app"))
        from utils.profile_manager import carregar_perfis
        from services.profile_composer import combinar_perfis
        from services.form_validation import preparar_participantes
        from models.participant import Participant

        perfis = carregar_perfis()
        self.assertGreater(len(perfis), 0, "catálogo vazio")
        for perfil in perfis:
            with self.subTest(perfil=perfil.nome):
                resultado = combinar_perfis([perfil])
                self.assertEqual(resultado.erros, [], perfil.nome)
                self.assertIsNotNone(resultado.perfil)
                paginas = resultado.perfil.obter_abas_disponiveis()
                self.assertGreater(len(paginas), 0)
                if resultado.perfil.usar_paginacao:
                    self.assertGreaterEqual(len(paginas), 1)
                # Campos condicionais e calculados têm forma válida.
                for campo in resultado.perfil.campos_entrada:
                    for grupo in campo.visivel_quando:
                        self.assertIsInstance(grupo, dict)
                    if campo.calculo:
                        self.assertIsInstance(campo.calculo, str)
                        self.assertNotIn("__", campo.calculo)

    def test_modo_simples_vs_avancado(self):
        import sys
        sys.path.insert(0, str(ROOT / "app"))
        from utils.profile_manager import carregar_perfis
        from services.profile_composer import combinar_perfis

        perfis = carregar_perfis()
        simples = [p for p in perfis if p.modo_fluxo == "formulario_simples"]
        contratos = [p for p in perfis if p.modo_fluxo == "contrato"]
        self.assertGreater(len(simples) + len(contratos), 0)
        if len(simples) >= 2:
            combinado = combinar_perfis(simples[:2])
            # Pode haver conflito legítimo; se houver, a mensagem cita o campo.
            if combinado.perfil is None:
                self.assertTrue(any("campo interno" in e for e in combinado.erros))

    def test_compose_expõe_paginacao(self):
        import sys
        sys.path.insert(0, str(ROOT / "app"))
        from server import LocalServer

        with LocalServer() as server:
            ids = list(server.jobs.profiles.keys())[:1]
            self.assertTrue(ids)
            req = type("R", (), {"profile_ids": ids})()
            out = server.jobs.compose(req)
            self.assertIn("usar_paginacao", out)
            self.assertIn("paginas", out)
            self.assertIn("agrupamento_paginas", out)
            self.assertIsInstance(out["paginas"], list)

    def test_jobs_list_endpoint(self):
        import sys
        sys.path.insert(0, str(ROOT / "app"))
        from server import LocalServer

        with LocalServer() as server:
            self.assertEqual(server.jobs.list_jobs(), [])


if __name__ == "__main__":
    unittest.main()
