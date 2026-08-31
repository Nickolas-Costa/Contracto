"""
Testes unitários para validação e geração dos formulários únicos (Modo Simples).
Garante que Form Cliente, ITBI e Isenção de Tributos Municipais geram PDFs com sucesso.
"""

import tempfile
import unittest
from pathlib import Path

from models.participant import Participant
from services.generator_service import gerar_documentos, resolver_caminho_formulario
from utils.profile_manager import obter_perfil, carregar_perfis


class TestSimpleFormGeneration(unittest.TestCase):

    def setUp(self):
        carregar_perfis()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pasta_saida = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_gerar_form_cliente(self):
        perfil = obter_perfil("Form Cliente")
        self.assertIsNotNone(perfil)
        p = Participant(
            nome_completo="Maria de Fátima Silva",
            cpf="123.456.789-10",
            data_assinatura="15/08/2026",
            local_assinatura="CAMOCIM-CE",
        )
        p.definir_campo("agencia", "1234")
        p.definir_campo("conta_caixa", "00012345-6")
        p.definir_campo("autorizo_debito_parcela", "Sim")
        p.definir_campo("autorizo_tarifa_avaliacao", "Sim")

        resultado = gerar_documentos([p], perfil, self.pasta_saida)
        self.assertTrue(len(resultado.arquivos_gerados) > 0)
        self.assertTrue(resultado.arquivos_gerados[0].exists())

    def test_gerar_itbi(self):
        perfil = obter_perfil("ITBI")
        self.assertIsNotNone(perfil)
        p = Participant(
            nome_completo="João Batista dos Santos",
            cpf="987.654.321-00",
            data_assinatura="20/08/2026",
            local_assinatura="CAMOCIM-CE",
        )
        p.definir_campo("endereco", "Rua das Acácias, 100")
        p.definir_campo("comprador_telefone", "(88) 99999-8888")
        p.definir_campo("comprador_email", "joao@email.com")
        p.definir_campo("nome_vendedor", "CONSTRUTORA ALVORADA LTDA")
        p.definir_campo("cpf_cnpj_vendedor", "12.345.678/0001-90")
        p.definir_campo("matricula", "98765")
        p.definir_campo("cartorio_oficio", "2º")
        p.definir_campo("cartorio_local", "CAMOCIM-CE")
        p.definir_campo("iptu", "01.02.003.004")
        p.definir_campo("area_terreno", "200,00")
        p.definir_campo("area_construida", "70,00")
        p.definir_campo("fracao_ideal", "100%")
        p.definir_campo("endereco_imovel", "Rua do Sol, 50 - Centro")
        p.definir_campo("valor_compra", "190.000,00")
        p.definir_campo("valor_avaliacao", "195.000,00")
        p.definir_campo("valor_financiado", "150.000,00")
        p.definir_campo("valor_subsidio", "20.000,00")
        p.definir_campo("valor_fgts", "10.000,00")
        p.definir_campo("valor_recursos", "10.000,00")

        resultado = gerar_documentos([p], perfil, self.pasta_saida)
        self.assertTrue(len(resultado.arquivos_gerados) > 0)
        self.assertTrue(resultado.arquivos_gerados[0].exists())

    def test_gerar_isencao_tributos(self):
        perfil = obter_perfil("Isenção de Tributos")
        self.assertIsNotNone(perfil)
        p = Participant(
            nome_completo="Carlos Eduardo Pereira",
            cpf="111.222.333-44",
            data_assinatura="25/08/2026",
            local_assinatura="CAMOCIM-CE",
        )
        p.definir_campo("rg", "2008123456-7 SSP/CE")
        p.definir_campo("estado_civil", "Solteiro(a)")
        p.definir_campo("endereco", "Rua das Palmeiras, 300 - Centro")
        p.definir_campo("matricula", "54321")

        resultado = gerar_documentos([p], perfil, self.pasta_saida)
        self.assertTrue(len(resultado.arquivos_gerados) > 0)
        self.assertTrue(resultado.arquivos_gerados[0].exists())


if __name__ == "__main__":
    unittest.main()
