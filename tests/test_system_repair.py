import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.system_repair_service import (
    _encerrar_processos_orfaos,
    _limpar_arquivos_temporarios,
    _verificar_modelos_padrao,
    executar_diagnostico_e_reparo,
)


class TestSystemRepairService(unittest.TestCase):
    def test_verificar_modelos_padrao(self):
        """Verifica se os modelos oficiais existem no ambiente."""
        self.assertTrue(_verificar_modelos_padrao())

    @patch("services.system_repair_service.subprocess.run")
    def test_encerrar_processos_orfaos(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        total = _encerrar_processos_orfaos()
        if sys.platform == "win32":
            self.assertGreater(total, 0)
            # Verifica se flags CREATE_NO_WINDOW foram passadas
            for call in mock_run.call_args_list:
                _, kwargs = call
                self.assertIn("creationflags", kwargs)

    def test_limpar_arquivos_temporarios(self):
        """Testa se a função de limpeza executa sem erros."""
        removidos = _limpar_arquivos_temporarios()
        self.assertIsInstance(removidos, int)

    def test_executar_diagnostico_e_reparo(self):
        """Executa a rotina completa e valida o objeto de resultado retornado."""
        resultado = executar_diagnostico_e_reparo()
        self.assertIsNotNone(resultado.titulo)
        self.assertIsInstance(resultado.detalhes, list)
        self.assertGreater(len(resultado.detalhes), 0)


if __name__ == "__main__":
    unittest.main()
