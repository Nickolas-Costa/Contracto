"""
Testes unitários para o módulo app/utils/document_validator.py.
Valida auto-formatação progressiva em tempo real e validação de CPF, CNPJ (inclusive alfanumérico) e CPF/CNPJ híbrido.
"""

import unittest
from utils.document_validator import (
    limpar_documento,
    limpar_apenas_digitos,
    formatar_cpf_progressivo,
    formatar_cnpj_progressivo,
    formatar_cpf_ou_cnpj_progressivo,
    formatar_data_progressiva,
    validar_cpf_ou_cnpj,
)


class TestDocumentValidator(unittest.TestCase):

    def test_limpar_documento(self):
        self.assertEqual(limpar_documento(" 12.345.678/0001-90 "), "12345678000190")
        self.assertEqual(limpar_documento("12.abc.345/0001-90"), "12ABC345000190")
        self.assertEqual(limpar_documento(""), "")
        self.assertEqual(limpar_documento(None), "")

    def test_formatar_cpf_progressivo(self):
        self.assertEqual(formatar_cpf_progressivo("123"), "123")
        self.assertEqual(formatar_cpf_progressivo("1234"), "123.4")
        self.assertEqual(formatar_cpf_progressivo("123456"), "123.456")
        self.assertEqual(formatar_cpf_progressivo("1234567"), "123.456.7")
        self.assertEqual(formatar_cpf_progressivo("123456789"), "123.456.789")
        self.assertEqual(formatar_cpf_progressivo("1234567890"), "123.456.789-0")
        self.assertEqual(formatar_cpf_progressivo("12345678901"), "123.456.789-01")
        # Se passar já com pontos
        self.assertEqual(formatar_cpf_progressivo("123.456.789-01"), "123.456.789-01")

    def test_formatar_cnpj_progressivo(self):
        self.assertEqual(formatar_cnpj_progressivo("12"), "12")
        self.assertEqual(formatar_cnpj_progressivo("123"), "12.3")
        self.assertEqual(formatar_cnpj_progressivo("12345"), "12.345")
        self.assertEqual(formatar_cnpj_progressivo("123456"), "12.345.6")
        self.assertEqual(formatar_cnpj_progressivo("12345678"), "12.345.678")
        self.assertEqual(formatar_cnpj_progressivo("123456780001"), "12.345.678/0001")
        self.assertEqual(formatar_cnpj_progressivo("12345678000190"), "12.345.678/0001-90")

    def test_formatar_cpf_ou_cnpj_progressivo(self):
        # Até 11 digitos formata como CPF
        self.assertEqual(formatar_cpf_ou_cnpj_progressivo("12345678901"), "123.456.789-01")
        # Acima de 11 digitos formata como CNPJ
        self.assertEqual(formatar_cpf_ou_cnpj_progressivo("12345678000190"), "12.345.678/0001-90")

    def test_formatar_data_progressiva(self):
        self.assertEqual(formatar_data_progressiva("15"), "15")
        self.assertEqual(formatar_data_progressiva("150"), "15/0")
        self.assertEqual(formatar_data_progressiva("1507"), "15/07")
        self.assertEqual(formatar_data_progressiva("15072"), "15/07/2")
        self.assertEqual(formatar_data_progressiva("15072026"), "15/07/2026")

    def test_validar_cpf_ou_cnpj(self):
        # CPF Válido
        valido, msg = validar_cpf_ou_cnpj("52998224725")
        self.assertTrue(valido)
        self.assertEqual(msg, "")

        # CPF Inválido
        valido, msg = validar_cpf_ou_cnpj("11111111111")
        self.assertFalse(valido)
        self.assertIn("inválido", msg)

        # CNPJ Numérico Válido
        valido, msg = validar_cpf_ou_cnpj("00.000.000/0001-91")
        self.assertTrue(valido)
        self.assertEqual(msg, "")

        # CNPJ Alfanumérico Válido (IN RFB 2229/2024)
        valido, msg = validar_cpf_ou_cnpj("12.ABC.345/01DE-35")
        self.assertTrue(valido)
        self.assertEqual(msg, "")

        # Documento com tamanho incompatível
        valido, msg = validar_cpf_ou_cnpj("12345")
        self.assertFalse(valido)
        self.assertIn("esperado 11 dígitos", msg)


if __name__ == "__main__":
    unittest.main()
