"""Testes do Formulário Cliente CAIXA MO 30.844 v012."""

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
from utils.resource_path import modelo_configurado


class TestFormularioCaixa(unittest.TestCase):
    """Valida o carregamento e preenchimento dos 18 campos do MO 30.844 v012."""

    def test_modelo_oficial_formulario_caixa_existe(self):
        caminho = modelo_configurado("modelo_02")
        self.assertIsNotNone(caminho)
        self.assertTrue(caminho.exists())

    def test_perfil_formulario_caixa_carregado(self):
        perfis = carregar_perfis(forcar_disco=True)
        nomes = [p.nome for p in perfis]
        self.assertIn("Form Cliente", nomes)

        perfil = obter_perfil("Form Cliente")
        self.assertIsNotNone(perfil)
        self.assertEqual(len(perfil.formularios), 1)
        self.assertEqual(perfil.formularios[0].nome, "Form Cliente")
        self.assertEqual(perfil.formularios[0].geracao, "por_processo")
        self.assertEqual(perfil.modo_fluxo, "formulario_simples")

    def test_geracao_ponta_a_ponta_com_formulario_caixa(self):
        perfil = obter_perfil("Form Cliente")
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
                "formaPagamentoParcela": "AUTORIZAR_OU_ALTERAR_DEBITO",
                "autorizaBoletoWhatsapp": "Sim",
                "autorizaCobrancaAvaliacao": "Sim",
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

            self.assertEqual(campos["1NOME"].get("/V"), "JOAO DA SILVA")
            self.assertEqual(campos["1CPF"].get("/V"), "529.982.247-25")
            self.assertEqual(campos["AGENCIA"].get("/V"), "1234")
            self.assertEqual(campos["CONTA"].get("/V"), "00012345-6")
            self.assertEqual(campos["PARCELA AUT"].get("/V"), "/Yes_ftsk")
            self.assertEqual(campos["CANCELO DEB"].get("/V"), "/Off")
            self.assertEqual(campos["BOLETO AUT"].get("/V"), "/Yes_ftsk")
            self.assertEqual(campos["AVALIACAO AUT COB"].get("/V"), "/Yes_ftsk")
            self.assertEqual(campos["LOCAL"].get("/V"), "CAMOCIM-CE")
            self.assertEqual(campos["DATA ABREV"].get("/V"), "29/08/2026")
            self.assertEqual(campos["1PARTICIPANTE"].get("/V"), "JOAO DA SILVA")
            self.assertEqual(campos["CPF1"].get("/V"), "529.982.247-25")
            self.assertEqual(campos["2PARTICIPANTE"].get("/V"), "MARIA DE SOUZA")
            self.assertEqual(campos["CPF2"].get("/V"), "111.444.777-35")


if __name__ == "__main__":
    unittest.main()
