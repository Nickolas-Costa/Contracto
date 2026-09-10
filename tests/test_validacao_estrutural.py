"""Validação estrutural detalhada (lista todos os problemas de uma vez)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils.profile_manager import (
    CampoEntrada,
    FormularioModelo,
    Perfil,
    problemas_estruturais,
)


def _perfil_valido(nome="Válido"):
    return Perfil(
        nome=nome,
        formularios=[FormularioModelo(nome="Doc", caminho="", mapeamento={})],
        campos_entrada=[CampoEntrada(id="nome", rotulo="Nome")],
    )


class TestProblemasEstruturais(unittest.TestCase):
    def test_limpo_nao_aponta_nada(self):
        self.assertEqual(problemas_estruturais(_perfil_valido()), [])

    def test_nome_vazio_e_duplicado(self):
        self.assertIn(
            "sem nome",
            " ".join(problemas_estruturais(Perfil(nome="  "))),
        )
        criticas = problemas_estruturais(_perfil_valido("X"), ("X", "Y"))
        self.assertTrue(any("X" in p and "outro perfil" in p for p in criticas))

    def test_campos_apontam_rotulo_e_id(self):
        perfil = _perfil_valido()
        perfil.campos_entrada = [
            CampoEntrada(id="", rotulo="SemId"),
            CampoEntrada(id="dup", rotulo="A"),
            CampoEntrada(id="dup", rotulo="B"),
            CampoEntrada(id="ruim", rotulo="Tipo", tipo="DESCONHECIDO"),
            CampoEntrada(id="lista", rotulo="Lista", tipo="SELECAO", opcoes=[]),
        ]
        criticas = problemas_estruturais(perfil)
        texto = " ".join(criticas)
        self.assertIn("SemId", texto)
        self.assertIn("dup", texto)
        self.assertIn("DESCONHECIDO", texto)
        self.assertIn("Lista", texto)
        self.assertGreaterEqual(len(criticas), 4)

    def test_formulario_aponta_nome(self):
        perfil = _perfil_valido()
        perfil.formularios = [
            FormularioModelo(nome="F1", caminho="", geracao="estranha", mapeamento={}),
            FormularioModelo(nome="F2", caminho="", mapeamento="nao-dict"),
        ]
        criticas = problemas_estruturais(perfil)
        self.assertTrue(any("F1" in p for p in criticas))
        self.assertTrue(any("F2" in p for p in criticas))


if __name__ == "__main__":
    unittest.main()
