"""
Testes automatizados de segurança e conformidade (Hardening).
Verifica a presença da sandbox -dSAFER no Ghostscript, validação de diretórios em _abrir_pasta,
isolamento de processos no taskkill e sanitização de nomes reservados do Windows.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from services.pdfa_converter import converter_para_pdfa
from services.system_repair_service import _encerrar_processos_orfaos
from ui.main_window import MainWindow
from utils.filename_utils import _sanitizar_nome_arquivo, nome_documento_processo
from models.participant import Participant


class TestSecurityHardening(unittest.TestCase):
    """Testes de validação das proteções e correções de segurança."""

    @patch("services.pdfa_converter.subprocess.run")
    @patch("services.pdfa_converter._obter_caminho_ghostscript")
    def test_ghostscript_includes_dsafer_flag(self, mock_gs_path, mock_subprocess_run):
        """Verifica se -dSAFER está presente na chamada do Ghostscript."""
        mock_gs_path.return_value = Path("C:/gs/bin/gswin64c.exe")
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_subprocess_run.return_value = mock_proc

        caminho_in = Path(__file__).resolve()
        caminho_out = Path(__file__).parent / "saida_teste_pdfa.pdf"

        # Mock existence
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            converter_para_pdfa(caminho_in, caminho_out)

        self.assertTrue(mock_subprocess_run.called)
        args_chamada = mock_subprocess_run.call_args[0][0]
        self.assertIn("-dSAFER", args_chamada, "A flag -dSAFER DEVE estar presente nos argumentos do Ghostscript!")

    @patch("ui.main_window.os.startfile")
    @patch("ui.main_window.subprocess.run")
    def test_abrir_pasta_rejects_non_directory_and_executables(self, mock_subp, mock_startfile):
        """Verifica se _abrir_pasta rejeita arquivos comuns ou executáveis."""
        # Testar com arquivo que não é pasta
        arquivo_ficticio = Path(__file__)  # é arquivo .py, não diretório
        MainWindow._abrir_pasta(arquivo_ficticio)

        self.assertFalse(mock_startfile.called, "os.startfile NÃO deve ser executado para arquivos!")
        self.assertFalse(mock_subp.called, "subprocess xdg-open NÃO deve ser executado para arquivos!")

        # Testar com diretório existente legítimo
        diretorio_real = Path(__file__).parent
        MainWindow._abrir_pasta(diretorio_real)

        if os.name == "nt":
            self.assertTrue(mock_startfile.called, "os.startfile deve ser chamado para diretório válido no Windows")
        else:
            self.assertTrue(mock_subp.called, "xdg-open deve ser chamado para diretório válido em Linux/macOS")

    @patch("services.system_repair_service.subprocess.run")
    def test_taskkill_includes_username_filter(self, mock_subprocess_run):
        """Verifica se taskkill filtra pelo usuário logado."""
        if sys.platform != "win32":
            self.skipTest("Teste específico para plataforma Windows")

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_subprocess_run.return_value = mock_proc

        with patch.dict(os.environ, {"USERNAME": "test_user_contracto"}):
            _encerrar_processos_orfaos()

        self.assertTrue(mock_subprocess_run.called)
        for call in mock_subprocess_run.call_args_list:
            cmd = call[0][0]
            self.assertIn("/FI", cmd)
            self.assertIn("USERNAME eq test_user_contracto", cmd)

    def test_sanitizacao_nomes_reservados_windows(self):
        """Verifica se nomes reservados (CON, PRN, AUX, NUL, COM1, LPT1) são neutralizados."""
        self.assertEqual(_sanitizar_nome_arquivo("CON.pdf"), "DOC_CON.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("con.pdf"), "DOC_con.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("PRN.pdf"), "DOC_PRN.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("aux.pdf"), "DOC_aux.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("NUL.pdf"), "DOC_NUL.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("COM1.pdf"), "DOC_COM1.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("LPT2.pdf"), "DOC_LPT2.pdf")

        # Nomes normais não devem ser modificados
        self.assertEqual(_sanitizar_nome_arquivo("CONTRATO JOAO.pdf"), "CONTRATO JOAO.pdf")
        self.assertEqual(_sanitizar_nome_arquivo("MARIA E JOSE.pdf"), "MARIA E JOSE.pdf")


if __name__ == "__main__":
    unittest.main()
