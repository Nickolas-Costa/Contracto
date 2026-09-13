"""Participante modular: fonte única, propriedades e herança por perfil."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.participant import Participant
from utils.profile_manager import CampoEntrada


class TestFonteUnica(unittest.TestCase):
    def test_kwargs_legados_viram_dicionario(self):
        p = Participant(nome_completo="A", cpf="1", endereco="Rua",
                        data_assinatura="01/01/2026", local_assinatura="X")
        self.assertEqual(p.obter_campo("endereco"), "Rua")
        self.assertEqual(p.endereco, "Rua")
        self.assertNotIn("endereco", Participant.__dataclass_fields__)

    def test_propriedades_espelham_atribuicao(self):
        p = Participant()
        p.data_assinatura = "02/02/2026"
        self.assertEqual(p.obter_campo("data_assinatura"), "02/02/2026")
        p.local_assinatura = "Y"
        self.assertEqual(p.campos_dinamicos["local_assinatura"], "Y")

    def test_local_padrao_preservado(self):
        self.assertEqual(Participant().local_assinatura, "CAMOCIM-CE")
        self.assertEqual(Participant().obter_campo("local_assinatura"), "CAMOCIM-CE")

    def test_alias_nome(self):
        p = Participant()
        p.definir_campo("nome", "Zé")
        self.assertEqual(p.nome_completo, "Zé")
        self.assertEqual(p.obter_campo("nome"), "Zé")


class TestHerancaPorPerfil(unittest.TestCase):
    def _campos(self):
        return [
            CampoEntrada(id="cidade", rotulo="Cidade", escopo="global"),
            CampoEntrada(id="apelido", rotulo="Apelido", escopo="participante"),
        ]

    def test_copia_so_compartilhados_do_perfil(self):
        principal = Participant(nome_completo="P", cpf="1")
        principal.definir_campo("cidade", "Camocim")
        principal.definir_campo("apelido", "Lico")
        outro = Participant(nome_completo="Q", cpf="2")
        outro.copiar_dados_compartilhados(principal, self._campos())
        self.assertEqual(outro.obter_campo("cidade"), "Camocim")
        self.assertEqual(outro.obter_campo("apelido"), "")

    def test_copia_legada_sem_campos(self):
        principal = Participant(nome_completo="P", cpf="1", endereco="Rua")
        principal.definir_campo("x", "1")
        outro = Participant(nome_completo="Q", cpf="2")
        outro.copiar_dados_compartilhados(principal)
        self.assertEqual(outro.endereco, "Rua")
        self.assertEqual(outro.obter_campo("x"), "1")


class TestResolvedorEstavel(unittest.TestCase):
    def test_chaves_classicas_resolvem(self):
        from services.generator_service import resolver_variavel

        p = Participant(nome_completo="Maria", cpf="52998224725",
                        data_assinatura="15/07/2026", local_assinatura="CAMOCIM-CE")
        self.assertEqual(resolver_variavel("participante.nome", p), "Maria")
        self.assertEqual(resolver_variavel("participante.data_assinatura", p), "15/07/2026")
        self.assertEqual(resolver_variavel("data.ano", p), "2026")


if __name__ == "__main__":
    unittest.main()
