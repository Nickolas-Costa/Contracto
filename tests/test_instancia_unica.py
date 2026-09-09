"""Trava de instância única (mutex nomeado do Windows)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.instancia_unica import InstanciaJaEmExecucao, InstanciaUnica


@unittest.skipUnless(sys.platform == "win32", "mutex nomeado é Windows-only")
class TestInstanciaUnica(unittest.TestCase):
    def test_segunda_aquisicao_mesmo_nome_bloqueia(self):
        primeira = InstanciaUnica(r"Local\ContractoTesteUnico")
        primeira.adquirir()
        try:
            with self.assertRaises(InstanciaJaEmExecucao):
                InstanciaUnica(r"Local\ContractoTesteUnico").adquirir()
        finally:
            primeira.liberar()

    def test_nomes_diferentes_coexistem(self):
        primeira = InstanciaUnica(r"Local\ContractoTesteA")
        segunda = InstanciaUnica(r"Local\ContractoTesteB")
        primeira.adquirir()
        segunda.adquirir()
        try:
            self.assertIsNotNone(primeira._handle)
            self.assertIsNotNone(segunda._handle)
        finally:
            primeira.liberar()
            segunda.liberar()

    def test_liberar_permite_readquirir(self):
        guarda = InstanciaUnica(r"Local\ContractoTesteReuso")
        guarda.adquirir()
        guarda.liberar()
        with InstanciaUnica(r"Local\ContractoTesteReuso"):
            pass

    def test_context_manager_libera_ao_sair(self):
        with InstanciaUnica(r"Local\ContractoTesteCtx") as guarda:
            handle = guarda._handle
            self.assertTrue(handle)
        self.assertIsNone(guarda._handle)


if __name__ == "__main__":
    unittest.main()
