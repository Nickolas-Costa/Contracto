"""
Testes unitários para o Formulário Cliente CAIXA (MO 30.844 v011) e seu perfil dedicado.
"""

import unittest
from pathlib import Path
import tempfile
import pypdf

from models.participant import Participant
from services.generator_service import (
    gerar_documentos,
    resolver_caminho_formulario,
    obter_mapeamento_formulario,
)
from utils.profile_manager import obter_perfil, carregar_perfis
from utils.resource_path import modelo_padrao_formulario_caixa


class TestFormularioCaixa(unittest.TestCase):
    """Valida o carregamento do modelo, perfil e preenchimento dos 28 campos do MO 30.844."""

    def test_modelo_oficial_formulario_caixa_existe(self):
        caminho = modelo_padrao_formulario_caixa()
        self.assertIsNotNone(caminho)
        self.assertTrue(caminho.exists())

    def test_perfil_formulario_caixa_carregado(self):
        perfis = carregar_perfis(forcar_disco=True)
        nomes = [p.nome for p in perfis]
        self.assertIn("Formulário CAIXA", nomes)

        perfil = obter_perfil("Formulário CAIXA")
        self.assertIsNotNone(perfil)
        self.assertEqual(len(perfil.formularios), 1)
        self.assertEqual(perfil.formularios[0].nome, "Formulário Cliente CAIXA")
        self.assertEqual(perfil.formularios[0].geracao, "por_processo")

    def test_geracao_ponta_a_ponta_com_formulario_caixa(self):
        perfil = obter_perfil("Formulário CAIXA")
        self.assertIsNotNone(perfil)

        p1 = Participant(
            nome_completo="JOAO DA SILVA",
            cpf="529.982.247-25",
            endereco="RUA DAS FLORES, 123",
            data_assinatura="29/08/2026",
            local_assinatura="CAMOCIM-CE",
            campos_dinamicos={
                "agencia": "1234",
                "conta_caixa": "00012345-6",
                "autorizo_debito_parcela": "Sim",
                "autorizo_tarifa_avaliacao": "Sim",
            }
        )
        p2 = Participant(
            nome_completo="MARIA DE SOUZA",
            cpf="111.444.777-35",
            endereco="RUA DAS FLORES, 123",
            data_assinatura="29/08/2026",
            local_assinatura="CAMOCIM-CE",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pasta_saida = Path(tmpdir)
            resultado = gerar_documentos(
                participantes=[p1, p2],
                perfil=perfil,
                pasta_saida=pasta_saida,
            )

            self.assertEqual(len(resultado.arquivos_gerados), 1)
            pdf_gerado = resultado.arquivos_gerados[0]
            self.assertTrue(pdf_gerado.exists())
            self.assertEqual(len(resultado.avisos), 0)

            # Verificar valores preenchidos no PDF
            reader = pypdf.PdfReader(str(pdf_gerado))
            campos = reader.get_fields() or {}

            self.assertEqual(campos["NOME_CLIENTE_1"].get("/V"), "JOAO DA SILVA")
            self.assertEqual(campos["CPF1"].get("/V"), "529.982.247-25")
            self.assertEqual(campos["AGENCIA"].get("/V"), "1234")
            self.assertEqual(campos["CONTA_CAIXA"].get("/V"), "00012345-6")
            self.assertEqual(campos["NOMEPROP1PROPOSTA"].get("/V"), "JOAO DA SILVA")
            self.assertEqual(campos["CPFPROP1"].get("/V"), "529.982.247-25")
            self.assertEqual(campos["NOMEPROP2PROPOSTA"].get("/V"), "MARIA DE SOUZA")
            self.assertEqual(campos["CPFPROP2"].get("/V"), "111.444.777-35")
            self.assertEqual(campos["MIP1"].get("/V"), "/Yes_uonn")
            self.assertEqual(campos["MIP2"].get("/V"), "/Yes_uonn")
            self.assertEqual(campos["LOCAL"].get("/V"), "CAMOCIM-CE")
            self.assertEqual(campos["DATA DD/MM/AAAA"].get("/V"), "29/08/2026")
            self.assertEqual(campos["PARTICIP1NOME"].get("/V"), "JOAO DA SILVA")
            self.assertEqual(campos["PARTICIP1CPF"].get("/V"), "529.982.247-25")
            self.assertEqual(campos["PARTICIP2NOME"].get("/V"), "MARIA DE SOUZA")
            self.assertEqual(campos["PARTICIP2CPF"].get("/V"), "111.444.777-35")


if __name__ == "__main__":
    unittest.main()
