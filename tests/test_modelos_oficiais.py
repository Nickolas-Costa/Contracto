"""
Testes que validam o preenchimento diretamente contra os PDFs modelos oficiais reais
(app/assets/templates/), e não apenas contra PDFs sintéticos.

Isso funciona como uma rede de proteção: se os modelos forem atualizados e o
nome de algum campo mudar, estes testes falham imediatamente, indicando
exatamente qual campo precisa ser ajustado em generator_service.py.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader

from models.participant import Participant
from services import generator_service
from services.pdf_service import obter_campos_do_formulario
from utils.resource_path import modelo_padrao_ppe, modelo_padrao_primeiro_imovel
from utils.profile_manager import Perfil, FormularioModelo


class TestModelosOficiaisExistem(unittest.TestCase):
    def test_modelo_ppe_esta_presente(self):
        self.assertIsNotNone(
            modelo_padrao_ppe(), "app/assets/templates/PPE.pdf não foi encontrado."
        )

    def test_modelo_primeiro_imovel_esta_presente(self):
        self.assertIsNotNone(
            modelo_padrao_primeiro_imovel(),
            "app/assets/templates/1 IMOVEL.pdf não foi encontrado.",
        )


class TestCamposBatemComOMapeamento(unittest.TestCase):
    """Confere que TODOS os campos usados no mapeamento padrão realmente
    existem nos PDFs oficiais — ou seja, nenhum campo ficaria em branco."""

    def test_campos_do_ppe(self):
        campos_no_pdf = obter_campos_do_formulario(modelo_padrao_ppe())
        campos_esperados = {
            "NOME COMPLETO",
            "CPF",
            "DIA",
            "MES",
            "ANO",
            "LOCAL ASSINATURA",
        }
        ausentes = campos_esperados - campos_no_pdf
        self.assertEqual(
            ausentes, set(), f"Campos esperados mas ausentes no PPE.pdf real: {ausentes}"
        )

    def test_campos_do_primeiro_imovel(self):
        campos_no_pdf = obter_campos_do_formulario(modelo_padrao_primeiro_imovel())
        campos_esperados = {
            "NOME COMPLETO",
            "CPF",
            "ENDERECO",
            "DATA ASSINATURA",
            "LOCAL ASSINATURA",
        }
        ausentes = campos_esperados - campos_no_pdf
        self.assertEqual(
            ausentes,
            set(),
            f"Campos esperados mas ausentes no 1 IMOVEL.pdf real: {ausentes}",
        )


class TestGeracaoPontaAPontaComPdfsReais(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta_saida = Path(self.tmp.name)
        
        self.perfil_padrao = Perfil(
            nome="Padrão",
            formularios=[
                FormularioModelo(
                    nome="PPE", caminho=str(modelo_padrao_ppe()), geracao="por_participante",
                    mapeamento={"NOME COMPLETO": "participante.nome_completo", "CPF": "participante.cpf_formatado", "DIA": "data.dia", "MES": "data.mes", "ANO": "data.ano", "LOCAL ASSINATURA": "participante.local_assinatura"}
                ),
                FormularioModelo(
                    nome="1 IMOVEL", caminho=str(modelo_padrao_primeiro_imovel()), geracao="por_participante",
                    mapeamento={"NOME COMPLETO": "participante.nome_completo", "CPF": "participante.cpf_formatado", "ENDERECO": "participante.endereco", "DATA ASSINATURA": "participante.data_assinatura", "LOCAL ASSINATURA": "participante.local_assinatura"}
                )
            ]
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_gera_e_preenche_corretamente_com_os_pdfs_reais(self):
        participante = Participant(
            nome_completo="José Roberto Nascimento",
            cpf="123.456.789-09",
            endereco="Rua Coronel José Franco, 100 - Centro - Camocim/CE",
            data_assinatura="23/07/2026",
            local_assinatura="FORTALEZA-CE",
        )

        resultado = generator_service.gerar_documentos(
            [participante],
            self.perfil_padrao,
            self.pasta_saida,
        )

        self.assertEqual(resultado.avisos, [], f"Não deveria haver avisos: {resultado.avisos}")
        self.assertEqual(len(resultado.arquivos_gerados), 2)

        caminho_imovel = self.pasta_saida / "1 IMOVEL - JOSE.pdf"
        caminho_ppe = self.pasta_saida / "PPE - JOSE.pdf"

        campos_imovel = PdfReader(str(caminho_imovel)).get_fields()
        self.assertEqual(campos_imovel["NOME COMPLETO"].value, "José Roberto Nascimento")
        self.assertEqual(campos_imovel["CPF"].value, "123.456.789-09")
        self.assertEqual(
            campos_imovel["ENDERECO"].value, "Rua Coronel José Franco, 100 - Centro - Camocim/CE"
        )
        self.assertEqual(campos_imovel["DATA ASSINATURA"].value, "23/07/2026")
        self.assertEqual(campos_imovel["LOCAL ASSINATURA"].value, "FORTALEZA-CE")

        campos_ppe = PdfReader(str(caminho_ppe)).get_fields()
        self.assertEqual(campos_ppe["NOME COMPLETO"].value, "José Roberto Nascimento")
        self.assertEqual(campos_ppe["CPF"].value, "123.456.789-09")
        self.assertEqual(campos_ppe["DIA"].value, "23")
        self.assertEqual(campos_ppe["MES"].value, "Julho")
        self.assertEqual(campos_ppe["ANO"].value, "2026")
        self.assertEqual(campos_ppe["LOCAL ASSINATURA"].value, "FORTALEZA-CE")


if __name__ == "__main__":
    unittest.main()
