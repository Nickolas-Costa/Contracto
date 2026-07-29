"""
Testes para utils/filename_utils.py.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.participant import Participant
from utils.filename_utils import (
    extrair_primeiro_nome,
    gerar_sufixo_nomes,
    nome_documento_individual,
    nome_documento_processo,
    remover_acentos,
)


class TestRemoverAcentos(unittest.TestCase):
    def test_remove_acentos_basicos(self):
        self.assertEqual(remover_acentos("João"), "Joao")
        self.assertEqual(remover_acentos("ÉRICO"), "ERICO")
        self.assertEqual(remover_acentos("ção"), "cao")

    def test_sem_acentos_nao_altera(self):
        self.assertEqual(remover_acentos("MARIA"), "MARIA")


class TestExtrairPrimeiroNome(unittest.TestCase):
    def test_extrai_primeiro_nome(self):
        self.assertEqual(extrair_primeiro_nome("Maria da Silva"), "MARIA")
        self.assertEqual(extrair_primeiro_nome("João Carlos Pereira"), "JOAO")

    def test_nome_unico(self):
        self.assertEqual(extrair_primeiro_nome("Maria"), "MARIA")

    def test_nome_vazio(self):
        self.assertEqual(extrair_primeiro_nome(""), "PARTICIPANTE")
        self.assertEqual(extrair_primeiro_nome("   "), "PARTICIPANTE")


class TestGerarSufixoNomes(unittest.TestCase):
    def test_um_participante(self):
        participantes = [Participant(nome_completo="Maria da Silva")]
        self.assertEqual(gerar_sufixo_nomes(participantes), "MARIA")

    def test_dois_participantes(self):
        participantes = [
            Participant(nome_completo="Maria da Silva"),
            Participant(nome_completo="João Carlos Pereira"),
        ]
        self.assertEqual(gerar_sufixo_nomes(participantes), "MARIA E JOAO")

    def test_tres_participantes(self):
        participantes = [
            Participant(nome_completo="Maria da Silva"),
            Participant(nome_completo="João Carlos"),
            Participant(nome_completo="Ana Beatriz"),
        ]
        self.assertEqual(gerar_sufixo_nomes(participantes), "MARIA E JOAO E ANA")

    def test_nomes_duplicados(self):
        participantes = [
            Participant(nome_completo="Maria da Silva"),
            Participant(nome_completo="Maria dos Santos"),
        ]
        resultado = gerar_sufixo_nomes(participantes)
        self.assertEqual(resultado, "MARIA E MARIA2")

    def test_lista_vazia(self):
        self.assertEqual(gerar_sufixo_nomes([]), "PARTICIPANTE")


class TestNomeDocumentoProcesso(unittest.TestCase):
    def test_contrato_dois_participantes(self):
        participantes = [
            Participant(nome_completo="Maria da Silva"),
            Participant(nome_completo="João Carlos Pereira"),
        ]
        self.assertEqual(
            nome_documento_processo("CONTRATO", participantes),
            "CONTRATO MARIA E JOAO.pdf",
        )

    def test_planilha_um_participante(self):
        participantes = [Participant(nome_completo="Maria da Silva")]
        self.assertEqual(
            nome_documento_processo("PLANILHA DE EVOLUCAO", participantes),
            "PLANILHA DE EVOLUCAO MARIA.pdf",
        )


class TestNomeDocumentoIndividual(unittest.TestCase):
    def test_ppe(self):
        self.assertEqual(
            nome_documento_individual("PPE", "Maria da Silva"),
            "PPE - MARIA.pdf",
        )

    def test_primeiro_imovel(self):
        self.assertEqual(
            nome_documento_individual("PRIMEIRO IMOVEL", "João Carlos Pereira"),
            "PRIMEIRO IMOVEL - JOAO.pdf",
        )


if __name__ == "__main__":
    unittest.main()
