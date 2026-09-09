import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from models.participant import Participant
from services.generator_service import gerar_documentos_de_perfis
from services.mapping_audit import conferir_mapeamento, renderizar_pagina_destacada
from services.profile_composer import combinar_perfis
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


def _criar_pdf(caminho: Path, campo: str) -> None:
    documento = canvas.Canvas(str(caminho), pagesize=(300, 200))
    documento.drawString(20, 140, campo)
    documento.acroForm.textfield(name=campo, x=20, y=100, width=200, height=20)
    documento.showPage()
    documento.save()


class TestComposicaoPerfis(unittest.TestCase):
    def test_reune_campos_e_respeita_limite_de_participantes(self):
        primeiro = Perfil(
            nome="Primeiro", max_participantes=1,
            campos_entrada=[CampoEntrada(id="nome", rotulo="Nome")],
        )
        segundo = Perfil(
            nome="Segundo", max_participantes=4,
            campos_entrada=[CampoEntrada(id="telefone", rotulo="Telefone")],
        )

        resultado = combinar_perfis([primeiro, segundo])

        self.assertEqual(resultado.erros, [])
        self.assertEqual(resultado.perfil.max_participantes, 4)
        limites = {campo.id: campo.ate_participante for campo in resultado.perfil.campos_entrada}
        self.assertEqual(limites, {"nome": 1, "telefone": 4})
        self.assertTrue(resultado.perfil.usar_paginacao)

    def test_impede_campos_com_mesmo_nome_interno_e_tipos_diferentes(self):
        texto = Perfil(campos_entrada=[CampoEntrada(id="referencia", rotulo="Referência", tipo="TEXTO")])
        data = Perfil(campos_entrada=[CampoEntrada(id="referencia", rotulo="Referência", tipo="DATA")])

        resultado = combinar_perfis([texto, data])

        self.assertIsNone(resultado.perfil)
        self.assertTrue(any("tipos TEXTO e DATA" in erro for erro in resultado.erros))

    def test_identifica_paginas_com_o_nome_de_cada_formulario(self):
        primeiro = Perfil(
            nome="ITBI",
            campos_entrada=[CampoEntrada(id="vendedor", rotulo="Vendedor", aba="Dados do Vendedor")],
            agrupamento_paginas={"Dados do Vendedor": "Partes da operação"},
        )
        segundo = Perfil(
            nome="DAMP",
            campos_entrada=[CampoEntrada(id="modalidade", rotulo="Modalidade", aba="Operação")],
        )

        resultado = combinar_perfis([primeiro, segundo])

        self.assertEqual(
            resultado.perfil.obter_abas_disponiveis(),
            ["ITBI • Partes da operação", "DAMP • Operação"],
        )

    def test_gera_todos_os_formularios_sem_sobrescrever_nomes_iguais(self):
        with tempfile.TemporaryDirectory() as diretorio:
            pasta = Path(diretorio)
            modelo_a = pasta / "a.pdf"
            modelo_b = pasta / "b.pdf"
            _criar_pdf(modelo_a, "NOME")
            _criar_pdf(modelo_b, "NOME")
            formulario_a = FormularioModelo("DOCUMENTO", str(modelo_a), mapeamento={"NOME": "participante.nome"})
            formulario_b = FormularioModelo("DOCUMENTO", str(modelo_b), mapeamento={"NOME": "participante.nome"})
            perfis = [Perfil(formularios=[formulario_a]), Perfil(formularios=[formulario_b])]
            participante = Participant(nome_completo="Maria", cpf="52998224725")

            resultado = gerar_documentos_de_perfis([participante], perfis, pasta)

            self.assertEqual(len(resultado.arquivos_gerados), 2)
            self.assertEqual({arquivo.name for arquivo in resultado.arquivos_gerados}, {
                "DOCUMENTO - MARIA.pdf", "DOCUMENTO - MARIA (2).pdf",
            })
            for arquivo in resultado.arquivos_gerados:
                self.assertEqual(PdfReader(str(arquivo)).get_fields()["NOME"].value, "Maria")


class TestConferenciaMapeamento(unittest.TestCase):
    def test_classifica_ligacoes_e_incompatibilidades(self):
        campos = {
            "NOME": {"tipo": "/Tx", "estados": []},
            "ACEITE": {"tipo": "/Btn", "estados": ["/Off", "/Sim"]},
            "LIVRE": {"tipo": "/Tx", "estados": []},
        }
        mapeamento = {
            "NOME": "participante.nome",
            "ACEITE": {"origem": "participante.aceite", "valor_verdadeiro": "/Yes"},
            "ANTIGO": "participante.valor",
        }

        resultado = conferir_mapeamento(campos, mapeamento)

        self.assertEqual(resultado.ligados, ["NOME"])
        self.assertEqual(resultado.sem_ligacao, ["LIVRE"])
        self.assertEqual(resultado.nao_encontrados, ["ANTIGO"])
        self.assertEqual(resultado.estados_invalidos, ["ACEITE"])

    def test_renderiza_a_previa_sem_alterar_o_pdf(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "modelo.pdf"
            _criar_pdf(caminho, "NOME")
            tamanho_original = caminho.stat().st_size
            conferencia = conferir_mapeamento(
                {"NOME": {"tipo": "/Tx", "estados": []}},
                {"NOME": "participante.nome"},
            )

            imagem, total = renderizar_pagina_destacada(caminho, 0, conferencia)

            self.assertEqual(total, 1)
            self.assertGreater(imagem.width, 0)
            self.assertEqual(caminho.stat().st_size, tamanho_original)


if __name__ == "__main__":
    unittest.main()
