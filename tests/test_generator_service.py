import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from models.participant import Participant
from services.generator_service import (
    _proximo_caminho_disponivel,
    gerar_documentos,
    validar_antes_de_gerar,
)
from services.pdf_service import PdfServiceError, obter_campos_do_formulario
from utils.filename_utils import _sanitizar_nome_arquivo
from utils.profile_manager import Perfil, FormularioModelo


def _criar_pdf_modelo(caminho: Path, nomes_dos_campos: list[str]) -> None:
    """Cria um PDF de 1 página com campos de formulário de texto (AcroForm),
    simulando um modelo real da CAIXA, apenas para fins de teste."""
    c = canvas.Canvas(str(caminho), pagesize=(600, 800))
    form = c.acroForm
    y = 750
    for nome_campo in nomes_dos_campos:
        c.drawString(50, y + 15, nome_campo)
        form.textfield(
            name=nome_campo,
            tooltip=nome_campo,
            x=50,
            y=y,
            width=400,
            height=20,
            borderStyle="inset",
            forceBorder=True,
        )
        y -= 50
    c.save()


class TestUtilitariosDeArquivo(unittest.TestCase):
    def test_remove_caracteres_invalidos_do_windows(self):
        self.assertEqual(_sanitizar_nome_arquivo('Jo:ão "Test"?'), "João Test")

    def test_nome_vazio_fica_vazio(self):
        self.assertEqual(_sanitizar_nome_arquivo('???'), "")

    def test_nomes_duplicados_geram_sufixo(self):
        usados: set[str] = set()
        primeiro = _proximo_caminho_disponivel(Path("/saida"), "PPE - João.pdf", usados)
        segundo = _proximo_caminho_disponivel(Path("/saida"), "PPE - João.pdf", usados)
        self.assertEqual(primeiro.name, "PPE - João.pdf")
        self.assertEqual(segundo.name, "PPE - João (2).pdf")


class TestValidarAntesDeGerar(unittest.TestCase):
    def setUp(self):
        self.perfil = Perfil(
            nome="Teste",
            formularios=[
                FormularioModelo(nome="Teste", caminho="teste.pdf", mapeamento={})
            ]
        )
        # Mock file existence for validation
        self.perfil.formularios[0].caminho = str(Path(__file__).resolve())
        
    def test_sem_participantes(self):
        erros = validar_antes_de_gerar([], self.perfil, Path("/saida"))
        self.assertTrue(any("participante" in erro.lower() for erro in erros))

    def test_participante_sem_nome_ou_cpf(self):
        participante = Participant(nome_completo="", cpf="", endereco="Rua A", data_assinatura="15/07/2026")
        erros = validar_antes_de_gerar(
            [participante], self.perfil, Path("/saida")
        )
        self.assertTrue(any("Nome Completo" in erro for erro in erros))
        self.assertTrue(any("CPF" in erro for erro in erros))

    def test_data_invalida(self):
        participante = Participant(
            nome_completo="João", cpf="529.982.247-25", endereco="Rua A", data_assinatura="31/02/2026"
        )
        erros = validar_antes_de_gerar(
            [participante], self.perfil, Path("/saida")
        )
        self.assertTrue(any("inválida" in erro for erro in erros))

    def test_faltando_modelos_e_pasta(self):
        participante = Participant(
            nome_completo="João", cpf="529.982.247-25", endereco="Rua A", data_assinatura="15/07/2026"
        )
        erros = validar_antes_de_gerar([participante], self.perfil, None)
        self.assertEqual(len(erros), 1)  # pasta de saída

    def test_tudo_certo_nao_gera_erros(self):
        participante = Participant(
            nome_completo="João", cpf="529.982.247-25", endereco="Rua A", data_assinatura="15/07/2026"
        )
        erros = validar_antes_de_gerar(
            [participante], self.perfil, Path("/saida")
        )
        self.assertEqual(erros, [])


class TestGeracaoDeDocumentosPontaAPonta(unittest.TestCase):
    """Testa o fluxo completo: preencher os PDFs modelo (sintéticos) e
    verificar se os valores realmente aparecem nos campos do PDF gerado."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tmp.name)

        self.modelo_ppe = self.pasta / "modelo_ppe.pdf"
        self.modelo_imovel = self.pasta / "modelo_primeiro_imovel.pdf"
        self.pasta_saida = self.pasta / "saida"
        self.pasta_saida.mkdir()

        _criar_pdf_modelo(self.modelo_ppe, ["NOME COMPLETO", "CPF", "DIA", "MES", "ANO", "LOCAL ASSINATURA"])
        _criar_pdf_modelo(self.modelo_imovel, ["NOME COMPLETO", "CPF", "ENDERECO", "DATA ASSINATURA", "LOCAL ASSINATURA"])
        
        self.perfil = Perfil(
            nome="Teste",
            formularios=[
                FormularioModelo(
                    nome="PPE",
                    caminho=str(self.modelo_ppe),
                    geracao="por_participante",
                    mapeamento={
                        "NOME COMPLETO": "participante.nome_completo",
                        "CPF": "participante.cpf_formatado",
                        "DIA": "data.dia",
                        "MES": "data.mes",
                        "ANO": "data.ano",
                        "LOCAL ASSINATURA": "participante.local_assinatura"
                    }
                ),
                FormularioModelo(
                    nome="PRIMEIRO IMOVEL",
                    caminho=str(self.modelo_imovel),
                    geracao="por_participante",
                    mapeamento={
                        "NOME COMPLETO": "participante.nome_completo",
                        "CPF": "participante.cpf_formatado",
                        "ENDERECO": "participante.endereco",
                        "DATA ASSINATURA": "participante.data_assinatura",
                        "LOCAL ASSINATURA": "participante.local_assinatura"
                    }
                )
            ]
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_um_participante_gera_dois_arquivos_com_valores_corretos(self):
        participante = Participant(
            nome_completo="João da Silva",
            cpf="123.456.789-09",
            endereco="Rua das Flores, 123",
            data_assinatura="15/07/2026",
        )

        resultado = gerar_documentos(
            [participante], self.perfil, self.pasta_saida
        )

        self.assertEqual(len(resultado.arquivos_gerados), 2)

        # V2: nomes de arquivo usam primeiro nome em maiúsculas
        caminho_imovel = self.pasta_saida / "PRIMEIRO IMOVEL - JOAO.pdf"
        caminho_ppe = self.pasta_saida / "PPE - JOAO.pdf"
        self.assertTrue(caminho_imovel.exists(), f"Arquivo não encontrado: {caminho_imovel}")
        self.assertTrue(caminho_ppe.exists(), f"Arquivo não encontrado: {caminho_ppe}")

        campos_imovel = PdfReader(str(caminho_imovel)).get_fields()
        self.assertEqual(campos_imovel["NOME COMPLETO"].value, "João da Silva")
        self.assertEqual(campos_imovel["CPF"].value, "123.456.789-09")
        self.assertEqual(campos_imovel["ENDERECO"].value, "Rua das Flores, 123")
        self.assertEqual(campos_imovel["DATA ASSINATURA"].value, "15/07/2026")

        campos_ppe = PdfReader(str(caminho_ppe)).get_fields()
        self.assertEqual(campos_ppe["NOME COMPLETO"].value, "João da Silva")
        self.assertEqual(campos_ppe["CPF"].value, "123.456.789-09")
        self.assertEqual(campos_ppe["DIA"].value, "15")
        self.assertEqual(campos_ppe["MES"].value, "Julho")
        self.assertEqual(campos_ppe["ANO"].value, "2026")

    def test_tres_participantes_compartilham_endereco_e_data(self):
        principal = Participant(
            nome_completo="Maria Souza",
            cpf="529.982.247-25",
            endereco="Av. Central, 500",
            data_assinatura="01/03/2027",
        )
        segundo = Participant(nome_completo="Pedro Souza", cpf="418.936.560-20")
        terceiro = Participant(nome_completo="Ana Souza", cpf="655.538.170-13")

        segundo.copiar_dados_compartilhados(principal)
        terceiro.copiar_dados_compartilhados(principal)

        resultado = gerar_documentos(
            [principal, segundo, terceiro], self.perfil, self.pasta_saida
        )

        self.assertEqual(len(resultado.arquivos_gerados), 6)  # 3 participantes x 2 documentos

        # V2: nomes de arquivo usam primeiro nome em maiúsculas
        for primeiro_nome, nome_completo in [("MARIA", "Maria Souza"), ("PEDRO", "Pedro Souza"), ("ANA", "Ana Souza")]:
            caminho_imovel = self.pasta_saida / f"PRIMEIRO IMOVEL - {primeiro_nome}.pdf"
            self.assertTrue(caminho_imovel.exists(), f"Arquivo não encontrado: {caminho_imovel}")
            campos = PdfReader(str(caminho_imovel)).get_fields()
            self.assertEqual(campos["ENDERECO"].value, "Av. Central, 500")
            self.assertEqual(campos["DATA ASSINATURA"].value, "01/03/2027")
            self.assertEqual(campos["NOME COMPLETO"].value, nome_completo)

    def test_campo_ausente_no_modelo_gera_aviso_mas_nao_impede_geracao(self):
        # Recria o modelo de imóvel SEM o campo ENDERECO, simulando uma
        # alteração onde a Caixa retirou o campo
        self.modelo_imovel.unlink()
        _criar_pdf_modelo(self.modelo_imovel, ["NOME COMPLETO", "CPF", "DATA ASSINATURA"])

        participante = Participant(
            nome_completo="Ana", cpf="123.456.789-09", endereco="Rua X", data_assinatura="01/01/2026"
        )
        resultado = gerar_documentos(
            [participante], self.perfil, self.pasta_saida
        )

        # Tem que gerar o arquivo mesmo com erro
        self.assertEqual(len(resultado.arquivos_gerados), 2)
        # Deve ter um aviso sobre o campo ENDERECO e o LOCAL ASSINATURA faltando
        self.assertTrue(any("ENDERECO" in aviso for aviso in resultado.avisos))
        self.assertTrue(any("LOCAL ASSINATURA" in aviso for aviso in resultado.avisos))

    def test_modelo_totalmente_incompativel_levanta_erro(self):
        modelo_errado = self.pasta / "modelo_errado.pdf"
        _criar_pdf_modelo(modelo_errado, ["CAMPO_QUE_NAO_EXISTE"])
        
        self.perfil.formularios[1].caminho = str(modelo_errado)

        participante = Participant(
            nome_completo="Carlos Lima",
            cpf="763.139.830-50",
            endereco="Rua Y, 10",
            data_assinatura="10/10/2026",
        )

        with self.assertRaises(PdfServiceError):
            gerar_documentos([participante], self.perfil, self.pasta_saida)

    def test_obter_campos_do_formulario(self):
        campos = obter_campos_do_formulario(self.modelo_imovel)
        self.assertEqual(campos, {"NOME COMPLETO", "CPF", "ENDERECO", "DATA ASSINATURA", "LOCAL ASSINATURA"})


if __name__ == "__main__":
    unittest.main()
