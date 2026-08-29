"""
Testes unitários para o validador e formatador de CNPJ (Numérico Tradicional e Novo Alfanumérico).
"""

import unittest
from utils.cnpj_validator import (
    limpar_cnpj,
    validar_cnpj,
    formatar_cnpj,
    CnpjInvalidoError,
)


class TestCnpjValidator(unittest.TestCase):
    """Validações de CNPJ tradicional e alfanumérico segundo IN RFB 2.229/2024."""

    def test_limpar_cnpj(self):
        self.assertEqual(limpar_cnpj("00.000.000/0001-91"), "00000000000191")
        self.assertEqual(limpar_cnpj("12.abc.345/01de-35"), "12ABC34501DE35")
        self.assertEqual(limpar_cnpj(""), "")

    def test_validar_cnpj_numerico_tradicional(self):
        # CNPJ Banco do Brasil
        self.assertTrue(validar_cnpj("00.000.000/0001-91"))
        self.assertTrue(validar_cnpj("00000000000191"))

        # CNPJ Petrobras
        self.assertTrue(validar_cnpj("33.000.167/0001-01"))
        self.assertTrue(validar_cnpj("33000167000101"))

        # CNPJs inválidos
        self.assertFalse(validar_cnpj("00.000.000/0001-92"))
        self.assertFalse(validar_cnpj("33.000.167/0001-00"))
        self.assertFalse(validar_cnpj("00000000000000"))
        self.assertFalse(validar_cnpj("11111111111111"))
        self.assertFalse(validar_cnpj("12345"))
        self.assertFalse(validar_cnpj("00.000.000/0001-9199"))

    def test_validar_novo_cnpj_alfanumerico(self):
        # 12.ABC.345/01DE-35 calculado matematicamente via Módulo 11 ASCII
        self.assertTrue(validar_cnpj("12.ABC.345/01DE-35"))
        self.assertTrue(validar_cnpj("12abc34501de35"))

        # DV incorreto no alfanumérico
        self.assertFalse(validar_cnpj("12.ABC.345/01DE-34"))
        self.assertFalse(validar_cnpj("12.ABC.345/01DE-99"))

        # DVs alfanuméricos são proibidos pela RFB (devem ser estritamente dígitos)
        self.assertFalse(validar_cnpj("12.ABC.345/01DE-3A"))
        self.assertFalse(validar_cnpj("12.ABC.345/01DE-AB"))

    def test_formatar_cnpj(self):
        self.assertEqual(formatar_cnpj("00000000000191"), "00.000.000/0001-91")
        self.assertEqual(formatar_cnpj("12abc34501de35"), "12.ABC.345/01DE-35")

        with self.assertRaises(CnpjInvalidoError):
            formatar_cnpj("00000000000199")

        with self.assertRaises(CnpjInvalidoError):
            formatar_cnpj("12345")


if __name__ == "__main__":
    unittest.main()
