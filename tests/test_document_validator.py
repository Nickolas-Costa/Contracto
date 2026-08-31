"""
Testes unitários para o módulo app/utils/document_validator.py.
Valida auto-formatação progressiva em tempo real e validação de CPF, CNPJ (inclusive alfanumérico) e CPF/CNPJ híbrido.
"""

import unittest
from utils.document_validator import (
    formatar_area_progressiva,
    formatar_cnpj_progressivo,
    formatar_cpf_ou_cnpj_progressivo,
    formatar_cpf_progressivo,
    formatar_data_progressiva,
    formatar_moeda_progressiva,
    formatar_telefone_progressivo,
    limpar_apenas_digitos,
    limpar_documento,
    validar_cpf_ou_cnpj,
    validar_email,
    validar_telefone,
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

    def test_formatar_moeda_progressiva(self):
        self.assertEqual(formatar_moeda_progressiva(""), "")
        self.assertEqual(formatar_moeda_progressiva("0"), "")
        self.assertEqual(formatar_moeda_progressiva("5"), "0,05")
        self.assertEqual(formatar_moeda_progressiva("50"), "0,50")
        self.assertEqual(formatar_moeda_progressiva("500"), "5,00")
        self.assertEqual(formatar_moeda_progressiva("5000"), "50,00")
        self.assertEqual(formatar_moeda_progressiva("50000"), "500,00")
        self.assertEqual(formatar_moeda_progressiva("500000"), "5.000,00")
        self.assertEqual(formatar_moeda_progressiva("5000000"), "50.000,00")
        self.assertEqual(formatar_moeda_progressiva("18000000"), "180.000,00")
        self.assertEqual(formatar_moeda_progressiva("180.000,00"), "180.000,00")

    def test_formatar_area_progressiva(self):
        self.assertEqual(formatar_area_progressiva(""), "")
        self.assertEqual(formatar_area_progressiva("0"), "")
        self.assertEqual(formatar_area_progressiva("2"), "0,02")
        self.assertEqual(formatar_area_progressiva("20"), "0,20")
        self.assertEqual(formatar_area_progressiva("200"), "2,00")
        self.assertEqual(formatar_area_progressiva("2000"), "20,00")
        self.assertEqual(formatar_area_progressiva("20000"), "200,00")
        self.assertEqual(formatar_area_progressiva("6550"), "65,50")
        self.assertEqual(formatar_area_progressiva("125000"), "1.250,00")

    def test_formatar_telefone_progressivo(self):
        self.assertEqual(formatar_telefone_progressivo(""), "")
        self.assertEqual(formatar_telefone_progressivo("8"), "(8")
        self.assertEqual(formatar_telefone_progressivo("88"), "(88")
        self.assertEqual(formatar_telefone_progressivo("889"), "(88) 9")
        self.assertEqual(formatar_telefone_progressivo("889999"), "(88) 9999")
        self.assertEqual(formatar_telefone_progressivo("8836211234"), "(88) 3621-1234")
        self.assertEqual(formatar_telefone_progressivo("88999999999"), "(88) 99999-9999")

    def test_validar_telefone(self):
        self.assertTrue(validar_telefone(""))
        self.assertTrue(validar_telefone("(88) 3621-1234"))
        self.assertTrue(validar_telefone("(88) 99999-9999"))
        self.assertTrue(validar_telefone("88999999999"))
        self.assertFalse(validar_telefone("123"))
        self.assertFalse(validar_telefone("1234567890123"))

    def test_validar_email(self):
        self.assertTrue(validar_email(""))
        self.assertTrue(validar_email("usuario@exemplo.com"))
        self.assertTrue(validar_email("nome.sobrenome@dominio.com.br"))
        self.assertFalse(validar_email("usuario@"))
        self.assertFalse(validar_email("usuario@exemplo"))
        self.assertFalse(validar_email("usuario.com"))


if __name__ == "__main__":
    unittest.main()
