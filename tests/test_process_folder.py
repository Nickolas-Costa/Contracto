"""
Testes para services/process_folder_service.py.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.process_folder_service import caminho_pasta_pdfa, criar_estrutura_pastas


class TestCriarEstruturaPastas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta_base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_cria_estrutura_completa(self):
        pasta_pdfa = criar_estrutura_pastas(self.pasta_base)

        self.assertTrue(pasta_pdfa.exists())
        self.assertTrue((pasta_pdfa / "ASSINADOS").exists())
        self.assertTrue((pasta_pdfa / "ASSINADOS" / "REGISTRADOS").exists())
        self.assertEqual(pasta_pdfa.name, "PDF-A")

    def test_hierarquia_correta(self):
        """REGISTRADOS deve estar DENTRO de ASSINADOS, não ao lado."""
        criar_estrutura_pastas(self.pasta_base)

        registrados = self.pasta_base / "PDF-A" / "ASSINADOS" / "REGISTRADOS"
        self.assertTrue(registrados.exists())

        # Não deve existir REGISTRADOS no mesmo nível de ASSINADOS
        registrados_errado = self.pasta_base / "PDF-A" / "REGISTRADOS"
        self.assertFalse(registrados_errado.exists())

    def test_reutiliza_pastas_existentes(self):
        """Se as pastas já existem, não gera erro."""
        criar_estrutura_pastas(self.pasta_base)

        # Chamar novamente não deve levantar exceção
        pasta_pdfa = criar_estrutura_pastas(self.pasta_base)
        self.assertTrue(pasta_pdfa.exists())

    def test_caminho_pasta_pdfa(self):
        self.assertEqual(
            caminho_pasta_pdfa(self.pasta_base),
            self.pasta_base / "PDF-A",
        )


if __name__ == "__main__":
    unittest.main()
