"""
Testes unitários para o Formulário de Isenção de Tributos Municipais e herança dos dados de assinatura.
"""

import tempfile
import unittest
from pathlib import Path
import pypdf

from app.models.participant import Participant
from app.services.generator_service import gerar_documentos
from app.utils.profile_manager import obter_perfil, carregar_perfis
from app.utils.resource_path import modelo_padrao_isencao_tributos


class TestFormularioIsencao(unittest.TestCase):
    """Valida o modelo, perfil e preenchimento com herança de assinatura na Isenção."""

    def test_modelo_oficial_isencao_existe(self):
        caminho = modelo_padrao_isencao_tributos()
        self.assertIsNotNone(caminho)
        self.assertTrue(caminho.exists())

    def test_perfil_isencao_carregado(self):
        perfis = carregar_perfis(forcar_disco=True)
        nomes = [p.nome for p in perfis]
        self.assertIn("Isenção de Tributos", nomes)

        perfil = obter_perfil("Isenção de Tributos")
        self.assertIsNotNone(perfil)
        self.assertEqual(len(perfil.formularios), 1)
        self.assertEqual(perfil.modo_fluxo, "formulario_simples")

    def test_geracao_ponta_a_ponta_com_isencao_e_heranca_assinatura(self):
        perfil = obter_perfil("Isenção de Tributos")
        self.assertIsNotNone(perfil)

        p = Participant(
            nome_completo="ANA CLAUDIA MOURA",
            cpf="999.888.777-66",
            endereco="RUA CENTRAL, 100",
            data_assinatura="15/05/2026",
            local_assinatura="CAMOCIM-CE",
            campos_dinamicos={
                "rg": "2008999888-7 SSP/CE",
                "estado_civil": "Solteiro(a)",
                "matricula": "54.321",
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

            # Campos do requerente
            self.assertEqual(campos["NOME COMPLETO"].get("/V"), "ANA CLAUDIA MOURA")
            self.assertEqual(campos["CPF"].get("/V"), "999.888.777-66")
            self.assertEqual(campos["RG"].get("/V"), "2008999888-7 SSP/CE")
            self.assertEqual(campos["ESTADO CIVIL"].get("/V"), "Solteiro(a)")
            self.assertEqual(campos["ENDERECO"].get("/V"), "RUA CENTRAL, 100")
            self.assertEqual(campos["MATRICULA"].get("/V"), "54.321")

            # Campos 2 (Assinatura herdada automaticamente)
            self.assertEqual(campos["NOME_COMPLETO2"].get("/V"), "ANA CLAUDIA MOURA")
            self.assertEqual(campos["2CPF"].get("/V"), "999.888.777-66")

            # Data e Local
            self.assertEqual(campos["LOCAL"].get("/V"), "CAMOCIM-CE")
            self.assertEqual(campos["DIA"].get("/V"), "15")
            self.assertEqual(campos["MES"].get("/V"), "Maio")
            self.assertEqual(campos["ANO"].get("/V"), "2026")


if __name__ == "__main__":
    unittest.main()
