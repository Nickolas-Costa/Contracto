"""Testes para utils/date_formatter.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.date_formatter import DataInvalidaError, separar_data_por_extenso, validar_data


class TestValidarData(unittest.TestCase):
    def test_data_valida(self):
        self.assertTrue(validar_data("15/07/2026"))

    def test_data_invalida_dia_inexistente(self):
        self.assertFalse(validar_data("31/02/2026"))

    def test_data_formato_errado(self):
        self.assertFalse(validar_data("2026-07-15"))

    def test_data_vazia(self):
        self.assertFalse(validar_data(""))


class TestSepararDataPorExtenso(unittest.TestCase):
    def test_exemplo_do_espec_15_07_2026(self):
        self.assertEqual(separar_data_por_extenso("15/07/2026"), ("15", "Julho", "2026"))

    def test_exemplo_do_espec_01_01_2026(self):
        self.assertEqual(separar_data_por_extenso("01/01/2026"), ("01", "Janeiro", "2026"))

    def test_exemplo_do_espec_22_08_2027(self):
        self.assertEqual(separar_data_por_extenso("22/08/2027"), ("22", "Agosto", "2027"))

    def test_exemplo_do_espec_05_11_2028(self):
        self.assertEqual(separar_data_por_extenso("05/11/2028"), ("05", "Novembro", "2028"))

    def test_primeira_letra_do_mes_maiuscula(self):
        _, mes, _ = separar_data_por_extenso("01/12/2026")
        self.assertTrue(mes[0].isupper())

    def test_data_invalida_levanta_erro(self):
        with self.assertRaises(DataInvalidaError):
            separar_data_por_extenso("31/02/2026")

    def test_data_formato_errado_levanta_erro(self):
        with self.assertRaises(DataInvalidaError):
            separar_data_por_extenso("2026/07/15")

    def test_todos_os_meses(self):
        nomes_esperados = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]
        for mes_numero, nome_esperado in enumerate(nomes_esperados, start=1):
            with self.subTest(mes=mes_numero):
                _, mes, _ = separar_data_por_extenso(f"10/{mes_numero:02d}/2026")
                self.assertEqual(mes, nome_esperado)


if __name__ == "__main__":
    unittest.main()
