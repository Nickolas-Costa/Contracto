"""
Testes unitários para o Formulário de ITBI e mapeamento de seus 25 campos.
"""

import tempfile
import unittest
from pathlib import Path
import pypdf

from app.models.participant import Participant
from app.services.generator_service import gerar_documentos
from app.utils.profile_manager import obter_perfil, carregar_perfis
from app.utils.resource_path import modelo_padrao_itbi


class TestFormularioITBI(unittest.TestCase):
    """Valida o modelo, perfil e preenchimento dos campos da Declaração de ITBI."""

    def test_modelo_oficial_itbi_existe(self):
        caminho = modelo_padrao_itbi()
        self.assertIsNotNone(caminho)
        self.assertTrue(caminho.exists())

    def test_perfil_itbi_carregado(self):
        perfis = carregar_perfis(forcar_disco=True)
        nomes = [p.nome for p in perfis]
        self.assertIn("ITBI", nomes)

        perfil = obter_perfil("ITBI")
        self.assertIsNotNone(perfil)
        self.assertEqual(len(perfil.formularios), 1)
        self.assertEqual(perfil.modo_fluxo, "formulario_simples")

    def test_geracao_ponta_a_ponta_com_itbi(self):
        perfil = obter_perfil("ITBI")
        self.assertIsNotNone(perfil)

        p = Participant(
            nome_completo="FRANCISCO PEREIRA",
            cpf="123.456.789-00",
            endereco="RUA DAS OLIVEIRAS, 45",
            data_assinatura="30/08/2026",
            local_assinatura="CAMOCIM-CE",
            campos_dinamicos={
                "nome_vendedor": "CONSTRUTORA MAR AZUL LTDA",
                "cpf_cnpj_vendedor": "12.345.678/0001-99",
                "matricula": "98.765",
                "cartorio_oficio": "2º",
                "cartorio_local": "CAMOCIM-CE",
                "iptu": "01.02.003.004",
                "area_terreno": "250,00",
                "area_construida": "70,00",
                "fracao_ideal": "100,00",
                "comprador_telefone": "(88) 98888-7777",
                "comprador_email": "francisco@email.com",
                "endereco_imovel": "RUA DAS OLIVEIRAS, 45 - CAMOCIM-CE",
                "valor_compra": "190.000,00",
                "valor_avaliacao": "195.000,00",
                "valor_financiado": "150.000,00",
                "valor_subsidio": "20.000,00",
                "valor_recursos": "10.000,00",
                "valor_fgts": "10.000,00",
                "solicitar_isencao": "Sim",
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pasta_saida = Path(tmpdir)
            resultado = gerar_documentos(
                participantes=[p],
                perfil=perfil,
                pasta_saida=pasta_saida,
            )

            self.assertEqual(len(resultado.arquivos_gerados), 1)
            pdf_gerado = resultado.arquivos_gerados[0]
            self.assertTrue(pdf_gerado.exists())

            reader = pypdf.PdfReader(str(pdf_gerado))
            campos = reader.get_fields() or {}

            self.assertEqual(campos["NOME_VENDEDOR"].get("/V"), "CONSTRUTORA MAR AZUL LTDA")
            self.assertEqual(campos["CPF_CNPJ_VENDEDOR"].get("/V"), "12.345.678/0001-99")
            self.assertEqual(campos["MATRICULA"].get("/V"), "98.765")
            self.assertEqual(campos["COMPRADOR_NOME"].get("/V"), "FRANCISCO PEREIRA")
            self.assertEqual(campos["COMPRADOR_CPF"].get("/V"), "123.456.789-00")
            self.assertEqual(campos["VALOR_COMPRA"].get("/V"), "190.000,00")
            self.assertEqual(campos["LOCAL_ASSINATURA"].get("/V"), "CAMOCIM-CE")
            self.assertEqual(campos["DIA"].get("/V"), "30")
            self.assertEqual(campos["MES"].get("/V"), "Agosto")
            self.assertEqual(campos["ANO"].get("/V"), "2026")


if __name__ == "__main__":
    unittest.main()
