"""Leitura de PDFs do cliente: candidatos validados, mapeamento inverso do AcroForm e API."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.pdfgen import canvas

from models.participant import Participant
from services import pdf_extraction as ex
from services.generator_service import gerar_documentos
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil, carregar_perfis
from test_intake_e_pendencias import Base


def _pdf_texto(caminho: Path, linhas: list[str]) -> Path:
    doc = canvas.Canvas(str(caminho))
    for i, linha in enumerate(linhas):
        doc.drawString(50, 780 - 18 * i, linha)
    doc.showPage()
    doc.save()
    return caminho


class TestCandidatos(unittest.TestCase):
    def test_valores_validos_sao_achados_e_invalidos_ignorados(self):
        paginas = ["Nome: JOAO DA SILVA\nCPF: 529.982.247-25\nCPF 111.111.111-11\nData de nascimento: 05/05/1980\n"
                   "Emitido em 31/02/2020\nE-mail: Joao@Email.com\nTelefone (88) 98888-7777\nCEP 62400-000\n"
                   "PIS/PASEP: 123.45678.90-1\nEndereço: RUA A, 12, CENTRO\nProtocolo 123.456.789-00"]
        achados = {(c.tipo, c.valor) for c in ex.candidatos_do_texto(paginas)}
        self.assertIn(("nome", "JOAO DA SILVA"), achados)
        self.assertIn(("cpf", "529.982.247-25"), achados)
        self.assertNotIn(("cpf", "111.111.111-11"), achados)
        self.assertNotIn(("cpf", "123.456.789-00"), achados)
        self.assertIn(("nascimento", "05/05/1980"), achados)
        self.assertNotIn(("nascimento", "31/02/2020"), achados)
        self.assertIn(("email", "joao@email.com"), achados)
        self.assertIn(("telefone", "(88) 98888-7777"), achados)
        self.assertIn(("cep", "62400-000"), achados)
        self.assertIn(("endereco", "RUA A, 12, CENTRO"), achados)

    def test_rotulo_numa_linha_e_valor_na_seguinte(self):
        achados = {(c.tipo, c.valor) for c in ex.candidatos_do_texto(["NOME\nFRANCISCO DAS CHAGAS\nFILIAÇÃO\nX"])}
        self.assertIn(("nome", "FRANCISCO DAS CHAGAS"), achados)

    def test_cnpj_valido_e_matricula(self):
        achados = {(c.tipo, c.valor) for c in ex.candidatos_do_texto(["CNPJ 11.222.333/0001-81\nMatrícula nº 12.345\nRazão Social: MAR AZUL LTDA"])}
        self.assertIn(("cnpj", "11.222.333/0001-81"), achados)
        self.assertIn(("matricula", "12.345"), achados)
        self.assertIn(("razao", "MAR AZUL LTDA"), achados)

    def test_semantica_deduzida_do_id_e_do_tipo(self):
        deduz = lambda **k: ex.semantica_do_campo(CampoEntrada(**k))
        self.assertEqual(deduz(id="cpf_cnpj_vendedor", rotulo="x", tipo="CPF_CNPJ"), "vendedor.documento")
        self.assertEqual(deduz(id="endereco_imovel", rotulo="x", tipo="ENDERECO"), "imovel.endereco")
        self.assertEqual(deduz(id="endereco", rotulo="x"), "pessoa.endereco")
        self.assertEqual(deduz(id="dataNascimento", rotulo="x", tipo="DATA"), "pessoa.nascimento")
        self.assertEqual(deduz(id="qualquer", rotulo="x", semantica="pessoa.mae"), "pessoa.mae")


class TestPadroesDeDocumento(unittest.TestCase):
    CONTRATO = ["A1 - VENDEDOR(ES): CONSTRUTORA MAR AZUL LTDA, pessoa juridica, inscrita no CNPJ sob",
                "nº 11.222.333/0001-81, com sede na Rua Z.",
                "A2 - COMPRADOR(ES) E DEVEDOR(ES) FIDUCIANTE(S), doravante denominado(s) DEVEDOR(ES): FRANCISCO DAS CHAGAS",
                "PESSOA, brasileiro, solteiro, CPF 529.982.247-25, residente e domiciliado(a) em Rua Tal, nº 12, Centro,",
                "Camocim-CE. e MARIA DA SILVA SOUZA, brasileira, solteira, residente na Rua X."]

    def _achados(self, linhas, regras=None):
        texto = chr(10).join(linhas)
        return [(c.tipo, c.valor) for c in sorted(ex.candidatos_do_texto([texto], regras), key=lambda c: c.posicao)]

    def test_contrato_nomes_vendedor_e_endereco_sem_rotulo_fixo(self):
        achados = self._achados(self.CONTRATO)
        self.assertIn(("vendedor", "CONSTRUTORA MAR AZUL LTDA"), achados)
        self.assertLessEqual({"FRANCISCO DAS CHAGAS PESSOA", "MARIA DA SILVA SOUZA"}, {v for t, v in achados if t == "nome"})
        self.assertIn(("endereco", "Rua Tal, nº 12, Centro, Camocim-CE"), achados)

    def test_segundo_proponente_vai_para_o_segundo_participante(self):
        perfil = Perfil(nome="QA", modo_fluxo="contrato", campos_entrada=[], formularios=[])
        leitura = ex.Leitura(paginas=[chr(10).join(self.CONTRATO)])
        nome = next(p for p in ex.propor(leitura, perfil, "participante") if p["campo_id"] == "nome_completo")
        self.assertEqual(nome["ordenadas"][:2], ["FRANCISCO DAS CHAGAS PESSOA", "MARIA DA SILVA SOUZA"])

    def test_cadastro_com_endereco_em_partes_e_nome_por_rotulo_longo(self):
        cadastro = ["ENDEREÇO", "CEP: 62400000", "Logradouro: R 04 LOTEAMENTO VILA VERDE", "Complemento: Número: 1315",
                    "Município: CAMOCIM UF: CE", "Bairro: OLINDA", "Tipo de Imóvel: CASA", "Estado civil: SOLTEIRO",
                    "Nome Completo do Cliente: WALESKA PEREIRA CPF: 529.982.247-25"]
        achados = self._achados(cadastro)
        self.assertIn(("endereco", "R 04 LOTEAMENTO VILA VERDE, 1315, OLINDA, CAMOCIM-CE, 62400-000"), achados)
        self.assertIn(("nome", "WALESKA PEREIRA"), achados)

    def test_regra_do_usuario_frase_antes_e_onde_termina(self):
        regras = [{"tipo": "nome", "antes": "Outorgante :", "ate": "virgula"}]
        self.assertIn(("nome", "JOSE DE SOUSA"), self._achados(["Pelo presente, Outorgante: JOSE DE SOUSA, casado, ..."], regras))
        # regra malformada é ignorada em vez de quebrar a leitura
        self._achados(["x"], [{"tipo": "inventado", "antes": "a", "ate": "virgula"}, {"tipo": "nome", "antes": "", "ate": "x"}])


# Texto das páginas de cadastro (ficções): "Cadastro de Clientes" com renda formal e informal.
CADASTRO_FORMAL = ["""DADOS CADASTRAIS
CPF do Cliente: 12345678900
Nome Completo do Cliente: FULANO DE TAL
Nome Reduzido do Cliente: FULANO TAL
Data de Nascimento: 01/01/2000 Sexo FEMININO
Naturalidade: PARNAIBA / PI
Nacionalidade: BRASILEIRA
Nome do Pai: FRANCISCO
Nome da Mãe: FRANCISCA
Grau de Instrução: SUPERIOR COMPLETO
Tipo de Documento de
Identificação:
DOCUMENTO DE IDENTIFICAÇÃO
Número do Documento: 123123123
Orgão Emissor: SECRETARIA DE SEGURANÇA PÚBLICA
Data de Emissão: 01/01/2026
Estado Civil: DIVORCIADO (A)
PIS/NIS: 123123123123
Tipo de Ocupação: SERVIDOR PUBLICO MUNICIPAL""", """ENDEREÇO
CEP: 62400000
Logradouro: R PERIMETRAL
Complemento: Número: 01
Município: CAMOCIM UF: CE
Bairro: CENTRO
Tipo de Imóvel: CASA
Ocupação do Imóvel: ALUGADA
Telefone Celular: (86) 999999999
E-mail:
Jurídica 07660350000123
Nome da Fonte Pagadora: MUNICIPIO DE CAMOCIM
Admissão: 01/01/2026
Bruta: 100000,00 Líquida: 50000,00"""]
CADASTRO_INFORMAL = ["""DADOS CADASTRAIS
CPF do Cliente: 52998224725
Nome Completo do Cliente: CICLANO SOUSA DO NASCIMENTO
Data de Nascimento: 01/01/2000 Sexo FEMININO
Nome do Pai: JOAO
Nome da Mãe: JOANA
Estado Civil: SOLTEIRO (A)
PIS/NIS:
Tipo de Ocupação: ADMINISTRADOR""", """ENDEREÇO
CEP: 62400000
Logradouro: R 24 DE MAIO
Complemento: Número: 1
Município: CAMOCIM UF: CE
Bairro: BRASILIA
Telefone Celular: (88) 988888888
E-mail: CICLANA@GMAIL.COM
RENDAS COMPROVADAS
Nome da Atividade: ADMINISTRADOR
Data Início: 01/01/2024
Renda Líquida: 1800,00"""]


class TestCadastroDeClientes(unittest.TestCase):
    def _por_tipo(self, paginas):
        achados = {}
        for c in ex.candidatos_do_texto(paginas):
            achados.setdefault(c.tipo, []).append(c.valor)
        return achados

    def test_cadastro_formal_traz_identificacao_endereco_contato_e_renda(self):
        a = self._por_tipo(CADASTRO_FORMAL)
        self.assertEqual(a["nome"], ["FULANO DE TAL"])  # pai, mãe e "reduzido" não viram nome do cliente
        for tipo, valor in {"nascimento": "01/01/2000", "sexo": "FEMININO", "naturalidade": "PARNAIBA / PI", "nacionalidade": "BRASILEIRA", "pai": "FRANCISCO",
                            "mae": "FRANCISCA", "escolaridade": "SUPERIOR COMPLETO", "rg": "123123123", "rg_emissao": "01/01/2026", "estado_civil": "DIVORCIADO (A)",
                            "ocupacao": "SERVIDOR PUBLICO MUNICIPAL", "tipo_imovel": "CASA", "ocupacao_imovel": "ALUGADA", "cnpj": "07.660.350/0001-23",
                            "fonte_pagadora": "MUNICIPIO DE CAMOCIM", "admissao": "01/01/2026", "renda_bruta": "100000,00", "renda_liquida": "50000,00",
                            "municipio_uf": "CAMOCIM-CE", "situacao_ocupacional": "ATIVO"}.items():
            self.assertIn(valor, a.get(tipo, []), tipo)
        self.assertIn("R PERIMETRAL, 01, CENTRO, CAMOCIM-CE, 62400-000", a["endereco"])

    def test_numeros_que_nao_conferem_vem_com_aviso_em_vez_de_sumir(self):
        avisos = {c.tipo: c.aviso for c in ex.candidatos_do_texto(CADASTRO_FORMAL) if c.aviso}
        self.assertIn("cpf", avisos)   # 123.456.789-00 não é CPF válido (dado fictício)
        self.assertIn("pis", avisos)   # 12 dígitos
        self.assertNotIn("cpf", {c.tipo for c in ex.candidatos_do_texto(CADASTRO_INFORMAL) if c.aviso})  # CPF válido: sem aviso

    def test_cadastro_informal_traz_atividade_e_renda_liquida(self):
        a = self._por_tipo(CADASTRO_INFORMAL)
        self.assertEqual(a["nome"], ["CICLANO SOUSA DO NASCIMENTO"])
        self.assertIn("1800,00", a["renda_liquida"])
        self.assertIn("01/01/2024", a["inicio_atividade"])
        self.assertIn("ciclana@gmail.com", a["email"])
        self.assertNotIn("pis", a)  # PIS/NIS vazio no documento

    def test_campos_do_mo_29300_saem_do_cadastro_com_opcoes_do_perfil(self):
        perfil = next(p for p in carregar_perfis() if p.nome == "MO 29300 (DAMP)")
        propostas = {p["campo_id"]: p["valor"] for p in ex.propor(ex.Leitura(paginas=CADASTRO_FORMAL), perfil, "participante")}
        self.assertEqual(propostas["estadoCivil"], "DIVORCIADO(A)")  # "DIVORCIADO (A)" casa com a opção do campo
        self.assertEqual(propostas["situacaoOcupacional"], "ATIVO")
        self.assertEqual(propostas["profissaoMaiorRendimento"], "SERVIDOR PUBLICO MUNICIPAL")
        self.assertEqual(propostas["dataNascimento"], "01/01/2000")
        self.assertEqual(propostas["municipioUfResidencia"], "CAMOCIM-CE")
        self.assertNotIn("enderecoImovelFinanciado", propostas)  # o endereço do cadastro é da pessoa, não do imóvel financiado
        self.assertNotIn("municipioUfOcupacaoPrincipal", propostas)


# Contrato (ficção): cláusulas A1/A2 e página de assinaturas, com o texto quebrado em linhas como no PDF.
CONTRATO_P1 = """MO30818Av015 CONTRATO Nº 8.4444.111111111-1 1
A - QUALIFICAÇÃO DAS PARTES
A1 - VENDEDOR(ES): DONA DOS LOTES LTDA, inscrita no CNPJ 01.001.001/0001-01, situada em R
Antonio Magalhaes, 01, José Siebra Lopes em Camocim/CE, e-mail:
IMOVEIS@DONADOSLOTES.COM.BR com seus atos constitutivos arquivados na JUNTA COMERCIAL
DO ESTADO DO CEARÁ, registrada sob NIRE nº0000000001-1, representada por DONO DOS LOTES,
nacionalidade brasileira, nascido(a) em 01/01/1985, advogado, filho de: PPAI E MAE, e-mail:
DONODOSLOTES@YAHOO.COM.BR, portador(a) de CNH nº 00000000001, expedida por Órgão de
Trânsito/CE em 01/04/2020 e do CPF 555.555.555-55, casado(a) no regime de separação total de
bens, residente e domiciliado(a) em R Artista Plástico Joaquim De Sousa, 01, AP 1, Papicu em
Fortaleza/CE.
A2 - COMPRADOR(ES) E DEVEDOR(ES) FIDUCIANTE(S), doravante denominado(s) DEVEDOR(ES):
FULANO DE TAL, nacionalidade brasileira, nascido(a) em 01/01/1970, servidor público municipal, filho
de: mãe e pai, e-mail: cliente@HOTMAIL.COM, portador(a) de CNH nº 0000000000001, expedida por
Órgão de Trânsito/CE em 01/12/2025 e do CPF 999.999.999-99, casado(a) no regime de comunhão
parcial de bens, na vigência da Lei 6.515/77, e seu cônjuge FULANA DE TAL, nacionalidade brasileira,
nascido(a) em 01/05/1970, corretora, filha de: MAE E PAI, e-mail: FULANA@HOTMAIL.COM,
portador(a) de CNH nº 00000000009, expedida por Órgão de Trânsito/CE em 01/01/2022 e do CPF
666.666.666-66, residentes e domiciliados em R Jose De Alencar, 01, Centro em Camocim/CE.
A3 - CREDORA FIDUCIÁRIA: CAIXA ECONÔMICA FEDERAL-CEF, inscrita no CNPJ 00.360.305/0001-04, neste ato
representada por GERENTE DA CAIXA GERAL, nacionalidade brasileira, casado, nascido(a) em 01/01/1980,
economiário, portador(a) da carteira de identidade 0000000000000001, expedida por SSP/CE."""
CONTRATO_P2 = """E por estarem de acordo com os termos e condições deste contrato, as partes assinam o presente em 3
(três) vias.
CAMOCIM, CE 08 de Novembro de 2026
COMPRADOR(ES)
_________________________________________
FULANO DE TAL- CPF/CNPJ: 382.497.663-34
_________________________________________
FULANA DE TAL - CPF/CNPJ: 724.984.553-53
VENDEDOR(ES)
_________________________________________
DONA DOS LOTES LTDA- CPF/CNPJ: 01.001.001/0001-01"""


class TestContratoComVariosCompradores(unittest.TestCase):
    def setUp(self):
        self.paginas = [CONTRATO_P1, CONTRATO_P2]
        self.cands = ex.candidatos_de_contrato(self.paginas)

    def _de(self, grupo, tipo):
        return sorted((c.pessoa, c.valor) for c in self.cands if c.grupo == grupo and c.tipo == tipo)

    def test_cada_comprador_tem_os_proprios_dados(self):
        self.assertEqual(self._de("comprador", "nome"), [(0, "FULANO DE TAL"), (1, "FULANA DE TAL")])  # "e seu cônjuge FULANA..."
        self.assertEqual(self._de("comprador", "nascimento"), [(0, "01/01/1970"), (1, "01/05/1970")])
        self.assertEqual(self._de("comprador", "ocupacao"), [(0, "servidor público municipal"), (1, "corretora")])
        self.assertEqual(self._de("comprador", "email"), [(0, "cliente@hotmail.com"), (1, "fulana@hotmail.com")])

    def test_casal_divide_estado_civil_regime_e_endereco(self):
        self.assertEqual(self._de("comprador", "estado_civil"), [(0, "casado(a)"), (1, "casado(a)")])  # o do cônjuge vem do 1º
        self.assertEqual(self._de("comprador", "regime_casamento"), [(0, "comunhão parcial de bens"), (1, "comunhão parcial de bens")])
        self.assertEqual(self._de("comprador", "endereco"), [(-2, "R Jose De Alencar, 01, Centro, Camocim-CE")])  # termina no ponto, não em "6.515/77"

    def test_cpf_da_assinatura_vale_quando_o_da_clausula_nao_confere(self):
        cpfs = [(c.pessoa, c.valor, bool(c.aviso)) for c in self.cands if c.grupo == "comprador" and c.tipo == "cpf"]
        self.assertIn((0, "999.999.999-99", True), cpfs)
        self.assertIn((0, "382.497.663-34", False), cpfs)
        self.assertIn((1, "724.984.553-53", False), cpfs)

    def test_vendedor_empresa_nao_herda_dados_do_representante(self):
        self.assertEqual(self._de("vendedor", "nome"), [(0, "DONA DOS LOTES LTDA")])
        self.assertEqual(self._de("vendedor", "cnpj"), [(0, "01.001.001/0001-01")])
        self.assertEqual([c for c in self.cands if c.grupo == "vendedor" and c.tipo in ("cpf", "cnh", "nascimento")], [])
        self.assertEqual([c for c in self.cands if c.grupo == "comprador" and "CAIXA" in c.valor.upper()], [])  # cláusula A3 fica de fora

    def test_cnh_aparece_como_rg_com_aviso(self):
        self.assertTrue(all(c.aviso for c in self.cands if c.tipo == "cnh"))

    def test_data_e_local_do_contrato(self):
        achados = {c.tipo: c.valor for c in self.cands if c.tipo in ("data_assinatura", "local_assinatura")}
        self.assertEqual(achados, {"data_assinatura": "08/11/2026", "local_assinatura": "CAMOCIM-CE"})

    def test_propostas_por_pessoa_nos_formularios(self):
        perfis = {p.nome: p for p in carregar_perfis()}
        leitura = ex.Leitura(paginas=self.paginas)
        isencao = {p["campo_id"]: p for p in ex.propor(leitura, perfis["Isenção de Tributos"], "participante")}
        self.assertEqual([x["valor"] for x in isencao["nome_completo"]["por_pessoa"]], ["FULANO DE TAL", "FULANA DE TAL"])
        self.assertEqual([x["valor"] for x in isencao["cpf"]["por_pessoa"]], ["382.497.663-34", "724.984.553-53"])
        self.assertEqual(isencao["estado_civil"]["valor"], "Casado(a)")
        self.assertIn("CNH", isencao["rg"]["aviso"])  # RG do Isenção aceita o número, avisando que é de CNH
        self.assertEqual(isencao["data_assinatura"]["valor"], "08/11/2026")
        mo = {p["campo_id"]: p["valor"] for p in ex.propor(leitura, perfis["MO 29300 (DAMP)"], "participante")}
        self.assertEqual((mo["estadoCivil"], mo["regimeCasamento"]), ("CASADO(A)", "COMUNHÃO PARCIAL DE BENS"))
        itbi = {p["campo_id"]: p["valor"] for p in ex.propor(leitura, perfis["ITBI"], "compartilhado")}
        self.assertEqual(itbi["nome_vendedor"], "DONA DOS LOTES LTDA")


# União estável e parentes: sem "e seu cônjuge"; cada pessoa começa em "NOME, nacionalidade..." e traz o próprio endereço.
CONTRATO_UNIAO = """A2 - COMPRADOR(ES) E DEVEDOR(ES) FIDUCIANTE(S), doravante denominado(s) DEVEDOR(ES): FULANO DE TAL, nacionalidade
brasileira, nascido(a) em 01/01/1970, motorista, e-mail: fulano@x.com, portador(a) da carteira de identidade 111111, expedida por
SSP/CE em 01/01/2010 e do CPF 529.982.247-25, solteiro(a), em união estável desde 05/03/2015, residente e domiciliado(a) em R A,
01, Centro em Camocim/CE. BELTRANO DE TAL, nacionalidade brasileira, nascido(a) em 02/02/1972, pedreiro, CPF 111.444.777-35,
convivente em união estável, residente e domiciliado(a) em R B, 02, Centro em Camocim/CE. e CICLANA DE TAL, filha de FULANO E
MARIA, nacionalidade brasileira, nascida em 03/03/1995, estudante, CPF 390.533.447-05, solteira, residente e domiciliada em R C,
03, Centro em Camocim/CE, e SICRANO DE TAL, nacionalidade brasileira, nascido(a) em 04/04/1996, CPF 123.456.789-09, solteiro(a).
A3 - CREDORA FIDUCIÁRIA: CAIXA ECONÔMICA FEDERAL-CEF, inscrita no CNPJ 00.360.305/0001-04."""


class TestContratoSemConectorDeConjuge(unittest.TestCase):
    def setUp(self):
        self.cands = ex.candidatos_de_contrato([CONTRATO_UNIAO])

    def _de(self, tipo):
        return sorted((c.pessoa, c.valor) for c in self.cands if c.grupo == "comprador" and c.tipo == tipo)

    def test_quatro_pessoas_pela_assinatura_nome_virgula_nacionalidade(self):
        self.assertEqual(self._de("nome"), [(0, "FULANO DE TAL"), (1, "BELTRANO DE TAL"), (2, "CICLANA DE TAL"), (3, "SICRANO DE TAL")])

    def test_cada_pessoa_tem_o_proprio_endereco_e_documentos(self):
        self.assertEqual(self._de("endereco"), [(0, "R A, 01, Centro, Camocim-CE"), (1, "R B, 02, Centro, Camocim-CE"), (2, "R C, 03, Centro, Camocim-CE")])
        self.assertEqual([v for _, v in self._de("cpf")], ["529.982.247-25", "111.444.777-35", "390.533.447-05", "123.456.789-09"])
        self.assertEqual(self._de("rg"), [(0, "111111")])
        self.assertEqual(self._de("nascimento"), [(0, "01/01/1970"), (1, "02/02/1972"), (2, "03/03/1995"), (3, "04/04/1996")])

    def test_uniao_estavel_com_data_e_estado_civil_por_pessoa(self):
        self.assertEqual(self._de("uniao_estavel"), [(0, "SIM"), (1, "SIM")])
        self.assertEqual(self._de("data_uniao"), [(0, "05/03/2015")])
        self.assertEqual(self._de("estado_civil"), [(0, "solteiro(a)"), (1, "união estável"), (2, "solteiro(a)"), (3, "solteiro(a)")])

    def test_propostas_do_mo_29300_para_quatro_participantes(self):
        perfil = next(p for p in carregar_perfis() if p.nome == "MO 29300 (DAMP)")
        mo = {p["campo_id"]: p for p in ex.propor(ex.Leitura(paginas=[CONTRATO_UNIAO]), perfil, "participante")}
        self.assertEqual([x and x["valor"] for x in mo["nome_completo"]["por_pessoa"]], ["FULANO DE TAL", "BELTRANO DE TAL", "CICLANA DE TAL", "SICRANO DE TAL"])
        self.assertEqual([x and x["valor"] for x in mo["mantemUniaoEstavel"]["por_pessoa"]][:2], ["SIM", "SIM"])
        self.assertEqual(mo["dataCasamentoOuUniaoEstavel"]["por_pessoa"][0]["valor"], "05/03/2015")


class TestSoCompradoresUsamADenominacaoBranda(unittest.TestCase):
    """"NOME, nacionalidade..." só vale como nova pessoa dentro da cláusula dos compradores."""

    def _nomes(self, texto, grupo):
        return [c.valor for c in ex.candidatos_de_contrato([texto]) if c.tipo == "nome" and c.grupo == grupo]

    def test_representante_do_vendedor_e_gerente_da_caixa_nao_viram_participantes(self):
        texto = (
            "A1 - VENDEDOR(ES): VENDEDOR PESSOA FISICA, nacionalidade brasileira, nascido(a) em 01/01/1980, residente e domiciliado(a) em R X, 01. "
            "REPRESENTANTE DO VENDEDOR, nacionalidade brasileira, nascido(a) em 02/02/1981, procurador. "
            "A2 - COMPRADOR(ES) E DEVEDOR(ES) FIDUCIANTE(S), doravante denominado(s) DEVEDOR(ES): COMPRADOR UM, nacionalidade brasileira, solteiro(a). "
            "A3 - CREDORA FIDUCIÁRIA: CAIXA ECONÔMICA FEDERAL-CEF, neste ato representada por GERENTE DA CAIXA GERAL, nacionalidade brasileira, casado, nascido(a) em 01/01/1980.")
        self.assertEqual(self._nomes(texto, "vendedor"), ["VENDEDOR PESSOA FISICA"])  # o ponto final antes do representante não cria vendedor
        self.assertEqual(self._nomes(texto, "comprador"), ["COMPRADOR UM"])
        self.assertFalse([c for c in ex.candidatos_de_contrato([texto]) if "GERENTE" in c.valor.upper() or "REPRESENTANTE" in c.valor.upper()])

    def test_empresa_vendedora_representada_nao_ganha_segunda_pessoa(self):
        achados = self._nomes(CONTRATO_P1, "vendedor")
        self.assertEqual(achados, ["DONA DOS LOTES LTDA"])  # "representada por DONO DOS LOTES, nacionalidade..." fica de fora

    def test_e_da_filiacao_nao_cria_segundo_comprador_e_endereco_fica_com_o_unico(self):
        texto = ("A2 - COMPRADOR(ES): COMPRADOR UM, nacionalidade brasileira, solteiro(a), filho(a) de MARIA DA SILVA e JOSE DA SILVA, "
                 "CPF 529.982.247-25, residente e domiciliado(a) em R A, 01, Centro em Camocim/CE. A3 - CREDORA FIDUCIÁRIA: CAIXA.")
        cands = ex.candidatos_de_contrato([texto])
        self.assertEqual(self._nomes(texto, "comprador"), ["COMPRADOR UM"])
        self.assertEqual([(c.pessoa, c.valor) for c in cands if c.tipo == "endereco"], [(0, "R A, 01, Centro, Camocim-CE")])

    def test_clausula_a1_lida_como_al_pelo_ocr_ainda_vale(self):
        self.assertEqual(self._nomes("Al - VENDEDOR(ES): VENDEDOR UM, nacionalidade brasileira, solteiro(a).", "vendedor"), ["VENDEDOR UM"])

    def test_gerente_dentro_do_bloco_dos_compradores_e_ignorado(self):
        texto = ("A2 - COMPRADOR(ES): COMPRADOR UM, nacionalidade brasileira, solteiro(a). GERENTE DA CAIXA GERAL, nacionalidade brasileira, casado. "
                 "COMPRADOR DOIS, nacionalidade brasileira, solteiro(a).")
        self.assertEqual(self._nomes(texto, "comprador"), ["COMPRADOR UM", "COMPRADOR DOIS"])


class TestPadroesDoUsuario(unittest.TestCase):
    def test_normalizacao_descarta_invalidos_e_repetidos(self):
        from utils import config_manager as cm
        lista = [{"tipo": "nome", "antes": "  Outorgante   :", "ate": "virgula"}, {"tipo": "nome", "antes": "Outorgante :", "ate": "virgula"},
                 {"tipo": "cpf", "antes": "x", "ate": "virgula"}, {"tipo": "nome", "antes": "", "ate": "virgula"},
                 {"tipo": "nome", "antes": "x", "ate": "talvez"}, "texto", None]
        self.assertEqual(cm.normalizar_padroes_leitura(lista), [{"tipo": "nome", "antes": "Outorgante :", "ate": "virgula"}])
        self.assertEqual(cm.normalizar_padroes_leitura("x"), [])

    def test_tipos_e_terminos_do_config_valem_para_o_leitor(self):
        from utils import config_manager as cm
        self.assertEqual(set(cm.TIPOS_PADRAO_LEITURA), set(ex.TIPOS_REGRA))
        self.assertEqual(set(cm.ATE_PADRAO_LEITURA), set(ex._ATE))


class TestLeituraDePdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_propostas_por_papel_com_texto_do_pdf(self):
        pdf = _pdf_texto(self.root / "doc.pdf", ["Nome: JOAO DA SILVA", "CPF: 529.982.247-25", "Telefone (88) 98888-7777",
                                                "CNPJ do vendedor 11.222.333/0001-81", "Matrícula 9876"])
        perfil = next(p for p in carregar_perfis() if p.nome == "ITBI")
        leitura = ex.ler_pdf(pdf)
        pessoa = {p["campo_id"]: p["valor"] for p in ex.propor(leitura, perfil, "participante")}
        self.assertEqual(pessoa["nome_completo"], "JOAO DA SILVA")
        self.assertEqual(pessoa["cpf"], "529.982.247-25")
        self.assertEqual(pessoa["comprador_telefone"], "(88) 98888-7777")
        comum = {p["campo_id"]: p["valor"] for p in ex.propor(leitura, perfil, "compartilhado")}
        self.assertEqual(comum["cpf_cnpj_vendedor"], "11.222.333/0001-81")
        self.assertEqual(comum["matricula"], "9876")

    def test_pdf_gerado_pelo_contracto_volta_pelo_mapeamento_inverso(self):
        perfil = next(p for p in carregar_perfis() if p.nome == "ITBI")
        p = Participant(nome_completo="MARIA SOUZA", cpf="529.982.247-25", endereco="RUA B", data_assinatura="01/09/2026",
                        local_assinatura="X", campos_dinamicos={"nome_vendedor": "CONSTRUTORA X", "iptu": "01.02.003", "valor_compra": "190.000,00"})
        gerado = gerar_documentos(participantes=[p], perfil=perfil, pasta_saida=self.root, manter_editavel=True).arquivos_gerados[0]
        comum = {x["campo_id"]: x for x in ex.propor(ex.ler_pdf(gerado), perfil, "compartilhado")}
        self.assertEqual(comum["nome_vendedor"]["valor"], "CONSTRUTORA X")
        self.assertEqual(comum["nome_vendedor"]["metodo"], "acroform")
        self.assertEqual(comum["valor_compra"]["valor"], "190.000,00")

    def test_pdf_corrompido_e_grande_demais_viram_erro_seguro(self):
        ruim = self.root / "ruim.pdf"
        ruim.write_bytes(b"%PDF-1.4 lixo")
        with self.assertRaises(ex.ExtracaoErro):
            ex.ler_pdf(ruim)
        with patch.object(ex, "MAX_BYTES", 10):
            with self.assertRaises(ex.ExtracaoErro):
                ex.ler_pdf(_pdf_texto(self.root / "ok.pdf", ["x"]))


class TestOcr(Base):
    """PDF digitalizado: só imagem, sem camada de texto."""

    def _pdf_imagem(self, linhas):
        import pypdfium2
        from PIL import Image
        texto = pypdfium2.PdfDocument(str(_pdf_texto(self.root / "texto.pdf", linhas)))
        imagem = texto[0].render(scale=200 / 72).to_pil().convert("L")
        texto.close()
        destino = self.root / "scan.pdf"
        imagem.save(destino, "PDF", resolution=200)
        return destino

    @unittest.skipUnless(sys.platform == "win32", "OCR do Windows")
    def test_pagina_digitalizada_e_lida_pelo_ocr_do_windows(self):
        leitura = ex.ler_pdf(self._pdf_imagem(["Nome: ANA LIMA DE SOUZA", "CPF: 529.982.247-25"]))
        self.assertEqual(leitura.ocr, [1])
        perfil = Perfil(nome="QA", modo_fluxo="formulario_simples", campos_entrada=[CampoEntrada(id="cpf", rotulo="CPF", tipo="CPF")], formularios=[])
        cpf = next(p for p in ex.propor(leitura, perfil, "participante") if p["campo_id"] == "cpf")
        self.assertEqual((cpf["valor"], cpf["metodo"]), ("529.982.247-25", "ocr"))

    def test_sem_ocr_disponivel_o_pdf_digitalizado_vira_erro_claro(self):
        pdf = self._pdf_imagem(["Nome: ANA LIMA DE SOUZA"])
        with patch.object(ex.sys, "platform", "linux"), self.assertRaisesRegex(ex.ExtracaoErro, "digitalizado"):
            ex.ler_pdf(pdf)

    def test_ocr_pedido_pelo_usuario_le_todas_as_paginas_e_nao_falha_calado(self):
        texto = _pdf_texto(self.root / "com_texto.pdf", ["Nome: ANA LIMA DE SOUZA", "CPF: 529.982.247-25 e mais texto"])
        self.assertEqual(ex.ler_pdf(texto).ocr, [])
        with patch.object(ex, "_ocr_windows", return_value=["CPF 529.982.247-25"]) as ocr:
            self.assertEqual(ex.ler_pdf(texto, forcar_ocr=True).ocr, [1])
        self.assertEqual(len(ocr.call_args.args[0]), 1)
        with patch.object(ex.sys, "platform", "linux"), self.assertRaises(ex.ExtracaoErro):
            ex.ler_pdf(texto, forcar_ocr=True)


class TestApiExtract(Base):
    def test_endpoint_devolve_sugestoes_e_nao_ecoa_o_caminho(self):
        pdf = _pdf_texto(self.root / "cliente.pdf", ["Nome: ANA LIMA", "CPF: 529.982.247-25"])
        perfil = Perfil(nome="QA", modo_fluxo="formulario_simples", max_participantes=1, formato_saida="PDF",
                        campos_entrada=[CampoEntrada(id="email", rotulo="E-mail", tipo="EMAIL", obrigatorio=False)],
                        formularios=[FormularioModelo("D", "x.pdf")])
        self.server.jobs.profiles["a" * 32] = perfil
        entrada = self.server.jobs.selections.register(pdf, "convert")
        _, job = self.http("/api/v1/jobs/intake", {"file_ids": [entrada]})
        pronto = self.wait_job(job["job_id"])
        status, dados = self.http("/api/v1/extract", {"file_ids": [pronto["files"][0]["file_id"]], "profile_ids": ["a" * 32]})
        self.assertEqual(status, 200, dados)
        arquivo = dados["arquivos"][0]
        self.assertEqual({p["campo_id"]: p["valor"] for p in arquivo["participante"]}, {"nome_completo": "ANA LIMA", "cpf": "529.982.247-25"})
        self.assertNotIn(str(self.root), json.dumps(dados))


if __name__ == "__main__":
    unittest.main()
