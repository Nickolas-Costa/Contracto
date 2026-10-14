import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.participant import Participant
from services.generator_service import gerar_documentos, resolver_variavel
from services.mapping_engine import resolver_especificacao
from utils.pis_pasep_validator import formatar_pis_pasep, validar_pis_pasep
from utils import profile_manager


def mapear_configurado(nome_perfil, participante, participantes=None):
    perfil = profile_manager.obter_perfil(nome_perfil)
    formulario = perfil.formularios[0]
    todos = participantes or [participante]
    return {
        campo: resolver_especificacao(
            regra,
            lambda origem: resolver_variavel(origem, participante, todos_participantes=todos),
        )
        for campo, regra in formulario.mapeamento.items()
    }


def participante_damp(**alteracoes):
    dados = {
        "dataNascimento": "10/02/1990",
        "pisPasep": "120.44567.89-1",
        "estadoCivil": "DIVORCIADO(A)",
        "mantemUniaoEstavel": "NÃO",
        "profissaoMaiorRendimento": "ENGENHEIRO CIVIL",
        "municipioUfOcupacaoPrincipal": "CAMOCIM/CE",
        "situacaoOcupacional": "ATIVO",
        "municipioUfResidencia": "CAMOCIM/CE",
        "tempoResidenciaAnos": "5",
        "tempoResidenciaMeses": "7",
        "possuiImovel": "NÃO",
        "situacaoImpostoRenda": "ISENTO",
        "irAnoBase": "2025",
        "irExercicio": "2026",
        "enderecoImovelFinanciado": "RUA DAS FLORES, 123 - CENTRO - CAMOCIM/CE",
        "usufruto": "NAO_SOU_USUFRUTUARIO",
        "modalidade": "AQUISICAO_IMOVEL_CONCLUIDO",
        "valorModalidade": "180.000,00",
        "enquadramento": "AQUISICAO_OU_CONSTRUCAO_A_VISTA",
        "fgtsFuturo": "NÃO",
        "utilizaContaFgts": "NÃO",
    }
    dados.update(alteracoes)
    return Participant(
        nome_completo="JOSÉ DA SILVA",
        cpf="529.982.247-25",
        data_assinatura="06/09/2026",
        local_assinatura="CAMOCIM-CE",
        campos_dinamicos=dados,
    )


class TestPisPasep(unittest.TestCase):
    def test_formata_e_valida(self):
        self.assertEqual(formatar_pis_pasep("12044567891"), "120.44567.89-1")
        self.assertTrue(validar_pis_pasep("120.44567.89-1"))
        self.assertFalse(validar_pis_pasep("111.11111.11-1"))


class TestDampConfiguracao(unittest.TestCase):
    def test_pis_opcional_e_ocupacao_exibida_apos_a_situacao(self):
        perfil = profile_manager.obter_perfil("MO 29300 (DAMP)")
        campos = perfil.obter_campos_participante()
        por_id = {campo.id: campo for campo in campos}
        self.assertFalse(por_id["pisPasep"].obrigatorio)
        self.assertLess(
            [campo.id for campo in campos].index("situacaoOcupacional"),
            [campo.id for campo in campos].index("profissaoMaiorRendimento"),
        )
        self.assertEqual(
            por_id["profissaoMaiorRendimento"].visivel_quando,
            [{"situacaoOcupacional": ["ATIVO"]}],
        )

    def test_casado_com_comunhao_parcial(self):
        p = participante_damp(
            estadoCivil="CASADO(A)",
            regimeCasamento="COMUNHÃO PARCIAL DE BENS",
            dataCasamentoOuUniaoEstavel="15/05/2018",
            mantemUniaoEstavel="SIM",
        )
        campos = mapear_configurado("MO 29300 (DAMP)", p)
        self.assertEqual(campos["regime_de_comunhao"], "COMUNHÃO PARCIAL DE BENS")
        self.assertEqual(campos["DATA_CASAMENTO"], "15/05/2018")
        self.assertEqual(campos["uniao_estavel_desde_DATA"], "")
        self.assertEqual((campos["mantenho_uniao_estavel"], campos["nao_mantenho_uniao"]), ("/Off", "/Off"))

    def test_solteiro_com_uniao_e_divorciado_sem_uniao(self):
        com_uniao = mapear_configurado("MO 29300 (DAMP)", participante_damp(
            estadoCivil="SOLTEIRO(A)", mantemUniaoEstavel="SIM",
            dataCasamentoOuUniaoEstavel="01/01/2020",
        ))
        sem_uniao = mapear_configurado("MO 29300 (DAMP)", participante_damp())
        self.assertEqual(com_uniao["uniao_estavel_desde_DATA"], "01/01/2020")
        self.assertEqual(com_uniao["mantenho_uniao_estavel"], "/Yes")
        self.assertEqual(sem_uniao["nao_mantenho_uniao"], "/Yes")
        self.assertEqual(sem_uniao["uniao_estavel_desde_DATA"], "")

    def test_situacoes_ocupacionais_e_imovel(self):
        esperado = {
            "ATIVO": ("/Off", "/Off"),
            "DESEMPREGADO": ("/Yes", "/Off"),
            "APOSENTADO_OU_PENSIONISTA": ("/Off", "/Yes"),
        }
        for situacao, marcacoes in esperado.items():
            with self.subTest(situacao=situacao):
                campos = mapear_configurado("MO 29300 (DAMP)", participante_damp(situacaoOcupacional=situacao))
                self.assertEqual((campos["estou_desempregado"], campos["sou_aposentado_pensionista"]), marcacoes)
        campos = mapear_configurado("MO 29300 (DAMP)", participante_damp(possuiImovel="SIM", municipioUfImovelPossuido="SOBRAL/CE"))
        self.assertEqual(campos["possuo_imovel_"], "/Yes")
        self.assertEqual(campos["possuo_imovel_local"], "SOBRAL/CE")

    def test_ir_isento_e_entregue(self):
        isento = mapear_configurado("MO 29300 (DAMP)", participante_damp())
        entregue = mapear_configurado("MO 29300 (DAMP)", participante_damp(situacaoImpostoRenda="DECLARACAO_ENTREGUE"))
        self.assertEqual(isento["sou_isento_ir_"], "/Yes")
        self.assertEqual(isento["ir_dec_ano_base"], "")
        self.assertEqual(entregue["declarei_ir"], "/Yes")
        self.assertEqual(entregue["ir_isento_ano_base"], "")

    def test_sete_modalidades_sao_exclusivas(self):
        modalidades = {
            "AQUISICAO_IMOVEL_CONCLUIDO": "imovel_concluido",
            "AQUISICAO_IMOVEL_EM_CONSTRUCAO": "construcao_empreendimento",
            "AQUISICAO_TERRENO_E_CONSTRUCAO": "terreno_e_construcao",
            "CONSTRUCAO_EM_TERRENO_PROPRIO": "terreno_proprio",
            "CCFGTS_REFORMA_OU_AMPLIACAO": "ccfgts_reforma",
            "CCFGTS_CONCLUSAO": "ccfgts_conclusao",
            "CCFGTS_MATERIAL_DE_CONSTRUCAO": "aquisicao_de_material_construcao",
        }
        for opcao, campo in modalidades.items():
            with self.subTest(opcao=opcao):
                valores = mapear_configurado("MO 29300 (DAMP)", participante_damp(modalidade=opcao))
                self.assertEqual(valores[campo], "/Yes")
                self.assertEqual(sum(valores[nome] == "/Yes" for nome in modalidades.values()), 1)

    def test_seis_enquadramentos_e_fgts(self):
        enquadramentos = {
            "AQUISICAO_OU_CONSTRUCAO_A_VISTA": "aquisicao_construcao_a_vista_0b9j",
            "CCFGTS_PMCMV_OU_OPERACOES_ESPECIAIS": "fgts_operacoes_especiais",
            "PRO_COTISTA": "carta_de_credito_pro_cotista_7j9t",
            "SBPE_COM_USO_DO_FGTS": "carta_de_credito_SBPE1",
            "SBPE_CONJUGE_OU_COMPANHEIRO": "carta_de_credito_SBPE_CONJUGE",
            "AQUISICAO_MATERIAL_CONSTRUCAO_AMC": "ccfgts_amc",
        }
        for opcao, campo in enquadramentos.items():
            valores = mapear_configurado("MO 29300 (DAMP)", participante_damp(
                enquadramento=opcao, possui36MesesFgts="SIM", jaRecebeuSubsidio="NÃO",
            ))
            self.assertEqual(valores[campo], "/Yes")
            self.assertEqual(sum(valores[nome] == "/Yes" for nome in enquadramentos.values()), 1)
        conta = mapear_configurado("MO 29300 (DAMP)", participante_damp(
            fgtsFuturo="SIM", utilizaContaFgts="SIM", numeroOperacaoFgts="12345", autorizaSaqueFgts="SIM",
        ))
        self.assertEqual(conta["fgts_futuro_sim"], "/Yes")
        self.assertEqual(conta["operacao_utilizacao_fgts_sim"], "/Yes")
        self.assertEqual(conta["autorizo_a_caixa_fgts"], "/Yes")
        sem_conta = mapear_configurado("MO 29300 (DAMP)", participante_damp(
            utilizaContaFgts="NÃO", numeroOperacaoFgts="VALOR ANTIGO", autorizaSaqueFgts="SIM",
        ))
        self.assertEqual(sem_conta["n_da_operacao_fgts"], "")
        self.assertEqual(sem_conta["autorizo_a_caixa_fgts"], "/Off")
        for par in (
            ("mantenho_uniao_estavel", "nao_mantenho_uniao"),
            ("possuo_imovel_", "nao_possuo_imovel"),
            ("fgts_futuro_sim", "fgts_futuro_nao"),
            ("operacao_utilizacao_fgts_sim", "operacao_utilizacao_fgts_nao"),
            ("36_meses_sim", "36_meses_nao"),
            ("beneficiado_desconto_sim", "beneficiado_desconto_nao"),
            ("possui_36_meses_sim-amc", "possui_36_meses_nao-amc"),
        ):
            if par[0] in conta and par[1] in conta:
                self.assertLessEqual(sum(conta[nome] != "/Off" for nome in par), 1)

    def test_textos_longos_data_e_ausencia_de_assinatura(self):
        texto = "Á" * 300
        campos = mapear_configurado("MO 29300 (DAMP)", participante_damp(
            profissaoMaiorRendimento=texto, enderecoImovelFinanciado=texto,
        ))
        self.assertEqual(campos["profissao_PROPONENTE"], texto)
        self.assertEqual(campos["local_imovel"], texto)
        self.assertEqual(campos["dia_assinatura"], "06")
        self.assertEqual(campos["mes_assinatura"], "SETEMBRO")
        self.assertEqual(campos["ano_assinatura"], "2026")
        self.assertFalse(any("assinatura_digital" in nome.lower() for nome in campos))


class TestCatalogoENovosPdfs(unittest.TestCase):
    def setUp(self):
        profile_manager.invalidar_cache()
        self.perfis = profile_manager.carregar_perfis(forcar_disco=True)

    def test_ordem_e_ids(self):
        self.assertEqual([p.nome for p in self.perfis[:3]], ["MO 29300 (DAMP)", "Form Cliente", "Seguro"])
        self.assertEqual(self.perfis[0].identificador, "inicial_01")

    def test_geracao_damp_e_seguro(self):
        damp = profile_manager.obter_perfil("MO 29300 (DAMP)")
        seguro = profile_manager.obter_perfil("Seguro")
        p = participante_damp(declaracaoSaudeSeguro="DESCONHECO_POSSUIR")
        with tempfile.TemporaryDirectory() as tmp:
            res_damp = gerar_documentos([p], damp, Path(tmp))
            self.assertEqual(res_damp.avisos, [])
            campos_damp = PdfReader(str(res_damp.arquivos_gerados[0])).get_fields()
            self.assertEqual(campos_damp["PROPONENTE_NOME"].get("/V"), "JOSÉ DA SILVA")
            self.assertEqual(campos_damp["nao_mantenho_uniao"].get("/V"), "/Yes")

            res_seguro = gerar_documentos([p], seguro, Path(tmp))
            self.assertEqual(res_seguro.avisos, [])
            campos_seguro = PdfReader(str(res_seguro.arquivos_gerados[0])).get_fields()
            self.assertEqual(campos_seguro["PROP1"].get("/V"), "JOSÉ DA SILVA")
            self.assertEqual(campos_seguro["DESC1"].get("/V"), "/Yes_ejfc")
            self.assertEqual(campos_seguro["POS1"].get("/V"), "/Off")

    def test_mapeador_seguro_exclusivo_e_cliente_exclusivo(self):
        p = participante_damp(declaracaoSaudeSeguro="DECLARO_POSSUIR", formaPagamentoParcela="CANCELAR_DEBITO")
        seguro = mapear_configurado("Seguro", p, [p])
        cliente = mapear_configurado("Form Cliente", p, [p])
        self.assertEqual((seguro["DESC1"], seguro["POS1"]), ("/Off", "/Yes_ejfc"))
        self.assertEqual((cliente["PARCELA AUT"], cliente["CANCELO DEB"]), ("/Off", "/Yes_ftsk"))

    def test_todos_os_campos_configurados_existem_nos_pdfs(self):
        for nome in ("MO 29300 (DAMP)", "Form Cliente", "Seguro"):
            perfil = profile_manager.obter_perfil(nome)
            formulario = perfil.formularios[0]
            from services.generator_service import resolver_caminho_formulario
            caminho = resolver_caminho_formulario(formulario)
            campos_pdf = set((PdfReader(str(caminho)).get_fields() or {}).keys())
            self.assertEqual(set(formulario.mapeamento) - campos_pdf, set(), nome)

    def test_campos_de_valor_nao_cobrem_o_simbolo_monetario(self):
        perfil = profile_manager.obter_perfil("MO 29300 (DAMP)")
        from services.generator_service import resolver_caminho_formulario
        reader = PdfReader(str(resolver_caminho_formulario(perfil.formularios[0])))
        nomes_esperados = {
            "aquisicao_imovel_concluido_valor", "aquisicao_imovel_construcao_valor",
            "aquisicao_terreno_construcao_valor",
            "construcao_terreno_proprio_valor", "ccfgts_reforma_ampliacao_valor",
            "ccfgts_conclusao_valor",
            "ccfgts_aquisicao_material_valor",
        }
        retangulos = {}
        for pagina in reader.pages:
            for referencia in pagina.get("/Annots") or []:
                widget = referencia.get_object()
                pai = widget.get("/Parent") or widget
                nome = str(pai.get("/T", ""))
                if nome in nomes_esperados:
                    retangulos[nome] = list(widget.get("/Rect", []))
        self.assertEqual(len(retangulos), 7)
        self.assertGreater(min(float(retangulo[0]) for retangulo in retangulos.values()), 250)

    def test_configuracao_de_mapeamento_persiste_sem_ser_sobrescrita(self):
        with tempfile.TemporaryDirectory() as tmp:
            arquivo = Path(tmp) / "profiles.json"
            with patch("utils.profile_manager._caminho_perfis", return_value=arquivo):
                profile_manager.invalidar_cache()
                perfis = profile_manager.carregar_perfis(forcar_disco=True)
                damp = next(p for p in perfis if p.nome == "MO 29300 (DAMP)")
                damp.formularios[0].mapeamento["PROPONENTE_ESTADO_CIVIL"] = {"constante": "CONFIGURADO PELO USUÁRIO"}
                profile_manager.salvar_perfis(perfis)
                profile_manager.invalidar_cache()
                reaberto = profile_manager.carregar_perfis(forcar_disco=True)
                damp_reaberto = next(p for p in reaberto if p.identificador == "inicial_01")
                self.assertEqual(
                    damp_reaberto.formularios[0].mapeamento["PROPONENTE_ESTADO_CIVIL"],
                    {"constante": "CONFIGURADO PELO USUÁRIO"},
                )

    def test_motor_aceita_formulario_arbitrario_sem_codigo_especifico(self):
        participante = Participant(
            nome_completo="MARIA TESTE",
            cpf="529.982.247-25",
            campos_dinamicos={"preferenciaContato": "EMAIL"},
        )
        configuracao_usuario = {
            "CAMPO_NOME_LIVRE": {"origem": "participante.nome_completo"},
            "CHECK_EMAIL_LIVRE": {
                "condicoes": [{"participante.preferenciaContato": ["EMAIL"]}],
                "valor_verdadeiro": "/MarcadoPeloPdf",
                "valor_falso": "/Off",
            },
        }
        resultado = {
            campo: resolver_especificacao(
                regra,
                lambda origem: resolver_variavel(origem, participante),
            )
            for campo, regra in configuracao_usuario.items()
        }
        self.assertEqual(resultado["CAMPO_NOME_LIVRE"], "MARIA TESTE")
        self.assertEqual(resultado["CHECK_EMAIL_LIVRE"], "/MarcadoPeloPdf")


if __name__ == "__main__":
    unittest.main()
