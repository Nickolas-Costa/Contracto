import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.rtf_converter import RtfConversionError, converter_rtf_para_pdf


class TestRtfConverter(unittest.TestCase):
    def test_arquivo_inexistente_lanca_erro(self):
        caminho_inexistente = Path("caminho_inexistente_12345.rtf")
        caminho_saida = Path("saida.pdf")

        with self.assertRaises(RtfConversionError):
            converter_rtf_para_pdf(caminho_inexistente, caminho_saida)

    @patch("services.rtf_converter._executar_conversao_word_com")
    def test_conversao_sucesso(self, mock_word):
        # Simular arquivo existente
        with patch.object(Path, "exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=b"{\\rtf1 teste}")):
            
            caminho_in = Path("documento.rtf")
            caminho_out = Path("documento.pdf")

            res = converter_rtf_para_pdf(caminho_in, caminho_out)
            self.assertEqual(res, caminho_out)
            mock_word.assert_called_once()


if __name__ == "__main__":
    unittest.main()
