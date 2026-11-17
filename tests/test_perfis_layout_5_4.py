"""Perfis tolerantes a chaves novas, campo Prefeitura do ITBI e telefone sem validador."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader

from services.form_validation import valor_valido
from models.participant import Participant
from services.generator_service import gerar_documentos
from api.jobs import Jobs
from utils import config_manager, profile_manager
from utils.profile_manager import CampoEntrada, carregar_perfis, duplicar_perfil, invalidar_cache
from utils.resource_path import mapeamento_configurado, modelo_configurado


class TestPerfisLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.tmp.name) / "contracto_profiles.json"
        patcher = patch("utils.profile_manager._caminho_perfis", return_value=self.arquivo)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(invalidar_cache)
        invalidar_cache()

    def test_chave_desconhecida_nao_apaga_perfis_do_usuario(self):
        campo = {"id": "x", "rotulo": "X", "campo_do_futuro": 1}
        self.arquivo.write_text(json.dumps([{
            "nome": "Meu perfil", "campo_do_futuro": True, "campos_entrada": [campo],
            "formularios": [{"nome": "F", "caminho": "", "chave_nova": 1}],
        }]), encoding="utf-8")
        perfis = {p.nome: p for p in carregar_perfis()}
        self.assertEqual([c.id for c in perfis["Meu perfil"].campos_entrada], ["x"])

    def test_duplicar_preserva_atributos_dos_campos(self):
        perfil = next(p for p in carregar_perfis() if p.nome == "ITBI")
        perfil.campos_entrada[0].rotulos_opcoes = {"A": "Opção A"}
        perfil.campos_entrada[0].apresentacao = "checkbox"
        profile_manager.salvar_perfis(carregar_perfis() and [perfil if p.nome == "ITBI" else p for p in carregar_perfis()])
        copia = duplicar_perfil("ITBI", "ITBI 2")
        self.assertEqual(copia.campos_entrada[0].rotulos_opcoes, {"A": "Opção A"})
        self.assertEqual(copia.campos_entrada[0].apresentacao, "checkbox")

    def test_itbi_ganha_prefeitura_em_instalacao_nova_e_existente(self):
        def ids():
            return [c.id for c in next(p for p in carregar_perfis(True) if p.nome == "ITBI").campos_entrada]
        self.assertEqual(ids()[ids().index("cartorio_local") + 1], "prefeitura")
        # Perfil já gravado por versão anterior (sem o campo): a correção o insere uma única vez.
        antigo = next(p for p in carregar_perfis() if p.nome == "ITBI")
        antigo.campos_entrada = [c for c in antigo.campos_entrada if c.id != "prefeitura"]
        antigo.correcoes_aplicadas = []
        profile_manager.salvar_perfis([antigo])
        invalidar_cache()
        self.assertEqual(ids().count("prefeitura"), 1)
        invalidar_cache()
        self.assertEqual(ids().count("prefeitura"), 1)

    def test_template_do_itbi_tem_campo_prefeitura_mapeado(self):
        campos = PdfReader(str(modelo_configurado("modelo_06"))).get_fields()
        self.assertIn("PREFEITURA", campos)
        self.assertEqual(mapeamento_configurado("modelo_06")["PREFEITURA"], "global.prefeitura")

    def test_telefone_so_tem_mascara_sem_validador(self):
        campo = CampoEntrada(id="comprador_telefone", rotulo="Telefone", tipo="TELEFONE", obrigatorio=False)
        self.assertTrue(valor_valido(campo, "123"))
        self.assertTrue(valor_valido(campo, "(88) 98888-7777"))


class TestMunicipiosItbi(unittest.TestCase):
    def test_normalizar_descarta_itens_invalidos_e_repetidos(self):
        lista = [{"prefeitura": " FORTALEZA-CE ", "comarca": "FORTALEZA-CE", "texto_isencao": "Lei X", "lixo": 1},
                 {"prefeitura": "fortaleza-ce"}, {"comarca": "sem prefeitura"}, "texto", None]
        self.assertEqual(config_manager.normalizar_municipios(lista),
                         [{"prefeitura": "FORTALEZA-CE", "comarca": "FORTALEZA-CE", "texto_isencao": "Lei X"}])
        self.assertEqual(config_manager.normalizar_municipios("x"), [])

    def test_catalogo_injeta_sugestoes_e_padroes_do_municipio(self):
        config = {"municipios_itbi": [{"prefeitura": "A-CE", "comarca": "A", "texto_isencao": "Lei A"},
                                      {"prefeitura": "B-CE", "comarca": "B", "texto_isencao": "Lei B"}],
                  "municipios_itbi_padrao": "B-CE"}
        itbi = next(p for p in carregar_perfis() if p.nome == "ITBI")
        with patch("utils.config_manager.carregar_config", return_value=config):
            campos = {c["id"]: c for c in Jobs(profiles=[itbi]).catalog()[0]["fields"]}
        self.assertEqual([s["prefeitura"] for s in campos["prefeitura"]["sugestoes"]], ["A-CE", "B-CE"])
        self.assertEqual((campos["prefeitura"]["valor_padrao"], campos["cartorio_local"]["valor_padrao"],
                          campos["texto_isencao"]["valor_padrao"]), ("B-CE", "B", "Lei B"))

    def test_pdf_do_itbi_leva_prefeitura_e_texto_da_isencao(self):
        itbi = obter = next(p for p in carregar_perfis() if p.nome == "ITBI")
        p = Participant(nome_completo="FULANO", cpf="529.982.247-25", endereco="RUA A", data_assinatura="01/09/2026",
                        local_assinatura="X", campos_dinamicos={"prefeitura": "X-CE", "texto_isencao": "Lei de X.",
                                                                "enquadramento_isencao": "Sim"})
        with tempfile.TemporaryDirectory() as tmp:
            saida = gerar_documentos(participantes=[p], perfil=itbi, pasta_saida=Path(tmp)).arquivos_gerados[0]
            campos = PdfReader(str(saida)).get_fields()
        self.assertEqual(campos["PREFEITURA"].get("/V"), "X-CE")
        self.assertEqual(campos["TEXTO_ISENCAO"].get("/V"), "Lei de X.")


class TestEnderecoEmPartes(unittest.TestCase):
    def _jobs(self):
        perfil = profile_manager.Perfil(
            nome="QA", modo_fluxo="formulario_simples", max_participantes=1,
            campos_entrada=[CampoEntrada(id="local", rotulo="Local", tipo="ENDERECO", obrigatorio=False, escopo="global")],
            formularios=[profile_manager.FormularioModelo("D", "x.pdf")])
        jobs = Jobs(profiles=[perfil])
        return jobs, list(jobs.profiles)[0]

    def test_endereco_em_partes_combina_com_perfil_que_pede_so_texto(self):
        from services.profile_composer import combinar_perfis
        def perfil(nome, tipo):
            return profile_manager.Perfil(nome=nome, modo_fluxo="formulario_simples",
                                          campos_entrada=[CampoEntrada(id="endereco", rotulo="Endereço", tipo=tipo)])
        for ordem in (("TEXTO", "ENDERECO"), ("ENDERECO", "TEXTO")):
            resultado = combinar_perfis([perfil("A", ordem[0]), perfil("B", ordem[1])])
            self.assertEqual(resultado.erros, [])
            self.assertEqual(resultado.perfil.campos_entrada[0].tipo, "ENDERECO")

    def test_partes_do_endereco_sao_aceitas_e_outras_chaves_continuam_recusadas(self):
        from api.jobs import ApiError
        from api.models import PreviewInput
        jobs, pid = self._jobs()
        base = {"nome_completo": "A", "cpf": "52998224725"}
        ok = PreviewInput(profile_ids=[pid], participants=[{**base, "campos_dinamicos": {"local": "x", "local_uf": "CE", "local_cep": "62400-000"}}])
        self.assertEqual(jobs.preview(ok)["issues"], [])
        ruim = PreviewInput(profile_ids=[pid], participants=[{**base, "campos_dinamicos": {"local_outro": "x"}}])
        with self.assertRaises(ApiError):
            jobs.preview(ruim)


if __name__ == "__main__":
    unittest.main()
