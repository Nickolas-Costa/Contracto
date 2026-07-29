"""Testes para utils/cpf_validator.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.cpf_validator import CpfInvalidoError, formatar_cpf, limpar_cpf, validar_cpf


class TestLimparCpf(unittest.TestCase):
    """Testes para a função limpar_cpf."""

    def test_remove_pontos_e_traco(self):
        self.assertEqual(limpar_cpf("123.456.789-09"), "12345678909")

    def test_remove_caracteres_nao_numericos(self):
        self.assertEqual(limpar_cpf("abc123.456.789-09xyz"), "12345678909")

    def test_string_so_com_digitos_fica_igual(self):
        self.assertEqual(limpar_cpf("12345678909"), "12345678909")

    def test_string_vazia(self):
        self.assertEqual(limpar_cpf(""), "")


class TestValidarCpf(unittest.TestCase):
    """Testes para a função validar_cpf."""

    def test_cpf_valido_sem_formatacao(self):
        self.assertTrue(validar_cpf("12345678909"))

    def test_cpf_valido_com_formatacao(self):
        self.assertTrue(validar_cpf("123.456.789-09"))

    def test_cpf_invalido_digitos_verificadores_errados(self):
        self.assertFalse(validar_cpf("12345678900"))

    def test_cpf_todos_digitos_iguais_111(self):
        self.assertFalse(validar_cpf("111.111.111-11"))

    def test_cpf_todos_digitos_iguais_000(self):
        self.assertFalse(validar_cpf("000.000.000-00"))

    def test_cpf_todos_digitos_iguais_999(self):
        self.assertFalse(validar_cpf("999.999.999-99"))

    def test_cpf_curto_demais(self):
        self.assertFalse(validar_cpf("1234567"))

    def test_cpf_longo_demais(self):
        self.assertFalse(validar_cpf("123456789012"))

    def test_cpf_com_caracteres_nao_numericos_valido(self):
        # Após a limpeza, deve restar "12345678909" que é válido
        self.assertTrue(validar_cpf("abc123.456.789-09xyz"))

    def test_cpf_vazio(self):
        self.assertFalse(validar_cpf(""))

    def test_outros_cpfs_validos(self):
        cpfs_validos = [
            "529.982.247-25",
            "418.936.560-20",
            "655.538.170-13",
            "763.139.830-50",
        ]
        for cpf in cpfs_validos:
            with self.subTest(cpf=cpf):
                self.assertTrue(validar_cpf(cpf))


class TestFormatarCpf(unittest.TestCase):
    """Testes para a função formatar_cpf."""

    def test_formata_cpf_valido_sem_formatacao(self):
        self.assertEqual(formatar_cpf("12345678909"), "123.456.789-09")

    def test_formata_cpf_valido_ja_formatado(self):
        self.assertEqual(formatar_cpf("123.456.789-09"), "123.456.789-09")

    def test_levanta_erro_para_cpf_curto(self):
        with self.assertRaises(CpfInvalidoError) as ctx:
            formatar_cpf("1234567")
        self.assertIn("11 dígitos", str(ctx.exception))

    def test_levanta_erro_para_cpf_longo(self):
        with self.assertRaises(CpfInvalidoError) as ctx:
            formatar_cpf("123456789012")
        self.assertIn("11 dígitos", str(ctx.exception))

    def test_levanta_erro_para_cpf_invalido_matematicamente(self):
        with self.assertRaises(CpfInvalidoError) as ctx:
            formatar_cpf("12345678900")
        self.assertIn("inválido", str(ctx.exception))

    def test_levanta_erro_para_todos_digitos_iguais(self):
        with self.assertRaises(CpfInvalidoError):
            formatar_cpf("111.111.111-11")

    def test_levanta_erro_para_string_vazia(self):
        with self.assertRaises(CpfInvalidoError):
            formatar_cpf("")


if __name__ == "__main__":
    unittest.main()
