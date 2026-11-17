"""Leitura de PDFs do cliente para sugerir valores dos campos do formulário (ADR 0027, Fase 1).

Só lê e propõe: nada é aplicado sem a revisão do usuário. Trabalha com a camada de texto e com os campos
AcroForm do PDF (sem OCR); valores que falham no validador do tipo nunca viram sugestão. O PDF é entrada não
confiável: limites de tamanho/páginas, sem executar nada do arquivo e nenhum valor lido vai para log.

shortcut: leitura no próprio processo (pypdfium2/pypdf); isolar em processo filho com limite de tempo quando
a Fase 2 (OCR) ou PDFs hostis entrarem no escopo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pypdfium2
from pypdf import PdfReader

from utils.cnpj_validator import formatar_cnpj, validar_cnpj
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.date_formatter import validar_data
from utils.document_validator import formatar_telefone_progressivo, validar_email
from utils.filename_utils import remover_acentos
from services.generator_service import obter_mapeamento_formulario
from utils.pis_pasep_validator import formatar_pis_pasep, validar_pis_pasep

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGINAS = 50
LIMITE_ALTERNATIVAS = 3


class ExtracaoErro(Exception):
    """Falha ao ler o PDF (criptografado, corrompido, grande demais); a mensagem é segura para a tela."""


@dataclass
class Leitura:
    paginas: list[str] = field(default_factory=list)
    campos: dict[str, str] = field(default_factory=dict)  # AcroForm: nome do campo → valor


@dataclass
class Candidato:
    tipo: str          # cpf, cnpj, pis, nascimento, email, telefone, cep, nome, razao, mae, pai, endereco, matricula
    valor: str
    pagina: int
    trecho: str
    confianca: float
    metodo: str = "texto"
    posicao: int = 0  # ordem de leitura no documento (quem aparece primeiro é o primeiro participante)
    aviso: str = ""   # leitura duvidosa (dígitos que não conferem): vem desmarcada na revisão
    grupo: str = ""   # contratos: "comprador" ou "vendedor" (cláusula de onde veio); vazio = documento sem cláusulas
    pessoa: int = -1   # índice da pessoa na cláusula; -2 = vale para todas (endereço, estado civil do casal)


def ler_pdf(caminho: Path) -> Leitura:
    if caminho.stat().st_size > MAX_BYTES:
        raise ExtracaoErro("O arquivo passa de 20 MB.")
    try:
        leitor = PdfReader(str(caminho))
        if leitor.is_encrypted:
            raise ExtracaoErro("O PDF tem senha e não pode ser lido.")
        campos = {}
        for nome, dados in (leitor.get_fields() or {}).items():
            valor = dados.get("/V")
            if valor is not None and str(valor).strip() and str(valor) != "/Off":
                campos[str(nome)] = str(valor).strip()
        documento = pypdfium2.PdfDocument(str(caminho))
        try:
            if len(documento) > MAX_PAGINAS:
                raise ExtracaoErro(f"O PDF tem mais de {MAX_PAGINAS} páginas.")
            paginas = [documento[i].get_textpage().get_text_range() for i in range(len(documento))]
        finally:
            documento.close()
    except ExtracaoErro:
        raise
    except Exception as exc:  # parser de terceiros: qualquer falha vira mensagem genérica
        raise ExtracaoErro("Não foi possível ler este PDF (arquivo corrompido ou protegido).") from exc
    return Leitura(paginas=paginas, campos=campos)


# --- candidatos do texto -------------------------------------------------------------------------

_CPF = re.compile(r"(?<!\d)(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)")
_CNPJ = re.compile(r"(?<![0-9A-Z])([0-9A-Z]{2}\.?[0-9A-Z]{3}\.?[0-9A-Z]{3}/?[0-9A-Z]{4}-?\d{2})(?![0-9A-Z])")
_PIS = re.compile(r"(?<!\d)(\d{3}\.?\d{5}\.?\d{2}-?\d)(?!\d)")
_DATA = re.compile(r"(?<!\d)(\d{2}/\d{2}/\d{4})(?!\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_TELEFONE = re.compile(r"(?<!\d)(\(\d{2}\)\s?9?\d{4}[-\s]?\d{4}|\d{2}\s9?\d{4}[-\s]?\d{4})(?!\d)")
_CEP = re.compile(r"(?<!\d)(\d{5}-\d{3})(?!\d)")
_NOME_DE = r"(?:\s+d[oae]\s+(?:cliente|titular|proponente|comprador|vendedor|participante|interessado|requerente|outorgante|devedor))?"
_DATA_RE = r"(\d{2}/\d{2}/\d{4})"
# (tipo, "rótulo: valor" na linha, "rótulo" sozinho com o valor na linha de baixo ou None)
_ROTULOS = (
    ("nome", re.compile(r"(?i)^\W*nome(?:\s+completo)?" + _NOME_DE + r"\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*nome(?:\s+completo)?" + _NOME_DE + r"\W*$")),
    ("razao", re.compile(r"(?i)^\W*(?:raz[ãa]o social|nome empresarial)\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*(?:raz[ãa]o social|nome empresarial)\W*$")),
    ("mae", re.compile(r"(?i)^\W*(?:nome da )?m[ãa]e\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*(?:nome da )?m[ãa]e\W*$")),
    ("pai", re.compile(r"(?i)^\W*(?:nome do )?pai\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*(?:nome do )?pai\W*$")),
    ("endereco", re.compile(r"(?i)^\W*endere[çc]o\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*endere[çc]o\W*$")),
    ("endereco_imovel", re.compile(r"(?i)^\W*endere[çc]o do im[óo]vel\s*[:\-]\s*(.+)$"), re.compile(r"(?i)^\W*endere[çc]o do im[óo]vel\W*$")),
    ("matricula", re.compile(r"(?i)matr[ií]cula\s*(?:n[ºo°.]*\s*)?[:\-]?\s*([\d][\d.\-]{2,})"), None),
    # cadastro de clientes (rótulo: valor)
    ("cpf", re.compile(r"(?i)^\W*cpf(?:\s+d[oae]\s+\w+)?\s*:\s*([\d.\-/ ]{8,})"), None),
    ("pis", re.compile(r"(?i)^\W*(?:pis(?:/(?:nis|pasep))?|nis|nit|pasep)\s*:\s*([\d.\-]{6,})"), None),
    ("nascimento", re.compile(r"(?i)^\W*data de nascimento\s*:\s*" + _DATA_RE), None),
    ("sexo", re.compile(r"(?i)\bsexo\s*:?\s*(masculino|feminino)\b"), None),
    ("naturalidade", re.compile(r"(?i)^\W*naturalidade\s*:\s*(.+)$"), None),
    ("nacionalidade", re.compile(r"(?i)^\W*nacionalidade\s*:\s*(.+)$"), None),
    ("escolaridade", re.compile(r"(?i)^\W*grau de instru[çc][ãa]o\s*:\s*(.+)$"), None),
    ("estado_civil", re.compile(r"(?i)^\W*estado civil\s*:\s*(.+)$"), None),
    ("rg", re.compile(r"(?i)^\W*n[úu]mero do documento\s*:\s*([\w.\-/]+)"), None),
    ("rg_orgao", re.compile(r"(?i)^\W*[óo]rg[ãa]o emissor\s*:\s*(.+)$"), None),
    ("rg_emissao", re.compile(r"(?i)^\W*data de emiss[ãa]o\s*:\s*" + _DATA_RE), None),
    ("ocupacao", re.compile(r"(?i)^\W*(?:tipo de )?ocupa[çc][ãa]o\s*:\s*(.+)$"), None),
    ("telefone", re.compile(r"(?i)^\W*(?:telefone(?:\s+celular)?|celular|fone)\s*:\s*(.+)$"), None),
    ("tipo_imovel", re.compile(r"(?i)^\W*tipo de im[óo]vel\s*:\s*(.+)$"), None),
    ("ocupacao_imovel", re.compile(r"(?i)^\W*ocupa[çc][ãa]o do im[óo]vel\s*:\s*(.+)$"), None),
    # rendas
    ("fonte_pagadora", re.compile(r"(?i)^\W*nome da fonte pagadora\s*:\s*(.+)$"), None),
    ("admissao", re.compile(r"(?i)^\W*admiss[ãa]o\s*:\s*" + _DATA_RE), None),
    ("renda_bruta", re.compile(r"(?i)\b(?:renda\s+)?bruta\s*:\s*([\d.,]+)"), None),
    ("renda_liquida", re.compile(r"(?i)\b(?:renda\s+)?l[íi]quida\s*:\s*([\d.,]+)"), None),
    ("atividade", re.compile(r"(?i)^\W*nome da atividade\s*:\s*(.+)$"), None),
    ("inicio_atividade", re.compile(r"(?i)^\W*data in[íi]cio\s*:\s*" + _DATA_RE), None),
)
_DATAS = {"nascimento", "rg_emissao", "admissao", "inicio_atividade"}
_CONTEXTO_PIS = re.compile(r"(?i)(pis|pasep|nit|nis)\W{0,12}$")
_CONTEXTO_NASC = re.compile(r"(?i)nasc")
_ROTULO_ESCRITO = re.compile(r"^[^\d@]{3,90}$")


# --- padrões por frase: "o que vem depois de X, até Y" (contratos e textos corridos) -------------------------

_ATE = {"virgula": ",", "ponto_e_virgula": ";", "ponto": ".", "fim_da_linha": "\n"}
TIPOS_REGRA = ("nome", "vendedor", "razao", "endereco", "endereco_imovel", "mae", "pai", "matricula")
# Padrões que acompanham o app; o usuário acrescenta os dele em Configurações (`padroes_leitura`).
# `segunda`: depois do primeiro nome, nomes em MAIÚSCULAS ligados por " e " e terminados em vírgula também valem.
REGRAS_PADRAO = (
    {"tipo": "nome", "antes": "doravante denominado(s) DEVEDOR(ES):", "ate": "virgula", "segunda": True},
    {"tipo": "nome", "antes": "COMPRADOR(ES):", "ate": "virgula", "segunda": True},
    {"tipo": "nome", "antes": "DEVEDOR(ES):", "ate": "virgula", "segunda": True},
    {"tipo": "vendedor", "antes": "VENDEDOR(ES):", "ate": "virgula", "segunda": True},
    {"tipo": "endereco", "antes": "residente e domiciliado(a) em", "ate": "ponto"},
    {"tipo": "endereco", "antes": "domiciliado(a) em", "ate": "ponto"},
    {"tipo": "endereco", "antes": "residente em", "ate": "ponto"},
    {"tipo": "endereco_imovel", "antes": "imóvel situado na", "ate": "ponto"},
    {"tipo": "endereco_imovel", "antes": "imóvel situado à", "ate": "ponto"},
    {"tipo": "endereco_imovel", "antes": "imóvel situado em", "ate": "ponto"},
)
_ABREVIATURAS = {"n", "no", "nº", "n°", "av", "r", "sr", "sra", "dr", "dra", "apto", "ap", "apt", "bl", "qd", "lt", "km", "cj", "sl", "trav", "al", "jd", "prof", "pres", "cel", "est", "rod"}
_NOME_MAIUSCULO = re.compile(r"\be\s+((?:[A-ZÀ-Ý][A-ZÀ-Ý'\-]*\s+){1,7}[A-ZÀ-Ý][A-ZÀ-Ý'\-]*)\s*,")


def _plano(texto: str) -> str:
    """Minúsculas e sem acento, mantendo o tamanho (o índice vale no texto original)."""
    return "".join(unicodedata.normalize("NFD", c)[0].lower() for c in texto)


def _fim_do_trecho(texto: str, inicio: int, ate: str) -> int:
    """Posição onde o valor termina; o ponto ignora abreviações (nº., Av.) e milhares (1.234)."""
    alvo = _ATE.get(ate, ",")
    i = inicio
    while True:
        i = texto.find(alvo, i)
        if i < 0 or alvo != ".":
            return i
        anterior = texto[max(0, i - 6):i].split()[-1].lower().rstrip(".") if texto[max(0, i - 6):i].split() else ""
        if (anterior in _ABREVIATURAS) or (texto[i - 1:i].isdigit() and texto[i + 1:i + 2].isdigit()):
            i += 1
            continue
        return i


def _cortar_rotulo(valor: str) -> str:
    """Remove o próximo rótulo de uma linha com dois campos ("ANA LIMA CPF: 123" → "ANA LIMA")."""
    return re.split(r"\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ/]{1,20}:", valor)[0].strip()


def candidatos_por_regras(paginas: list[str], regras) -> list[Candidato]:
    achados: list[Candidato] = []
    for numero, texto in enumerate(paginas, 1):
        corrido = re.sub(r"\s+", " ", texto)
        linhas = re.sub(r"[ \t]+", " ", texto)
        for regra in regras:
            tipo, antes, ate = regra.get("tipo"), str(regra.get("antes", "")).strip(), regra.get("ate", "virgula")
            if tipo not in TIPOS_REGRA or not antes or ate not in _ATE:
                continue
            base = linhas if ate == "fim_da_linha" else corrido
            # Espaços e acentos não importam: "Outorgante :" casa com "outorgante:".
            padrao = re.compile(r"\s*".join(re.escape(c) for c in _plano(antes) if not c.isspace()))
            plano = _plano(base)
            achou = padrao.search(plano)
            while achou:
                inicio = achou.end()
                fim = _fim_do_trecho(base, inicio, ate)
                valor = base[inicio:fim if fim >= 0 else inicio].strip(" :;-")
                if 3 <= len(valor) <= 150:
                    achados.append(Candidato(tipo, valor, numero, (antes + " " + valor)[:120], 0.85))
                    if regra.get("segunda") and fim >= 0:
                        for m in _NOME_MAIUSCULO.finditer(base[fim:fim + 900]):
                            achados.append(Candidato(tipo, m.group(1).strip(), numero, m.group(0)[:120], 0.8))
                achou = padrao.search(plano, inicio)
    return achados


_PARTE_ENDERECO = re.compile(r"(?i)\b(logradouro|complemento|n[úu]mero|n[º°]|munic[íi]pio|cidade|bairro|uf|estado(?!\s+civil)|cep)\s*:")
_PARTES_CHAVE = {"logradouro": "via", "complemento": "complemento", "número": "numero", "numero": "numero", "nº": "numero", "n°": "numero",
                 "município": "cidade", "municipio": "cidade", "cidade": "cidade", "bairro": "bairro", "uf": "uf", "estado": "uf", "cep": "cep"}


def _compor_endereco(partes: dict[str, str]) -> str:
    cep = re.sub(r"\D", "", partes.get("cep", ""))
    cidade = "-".join(x for x in (partes.get("cidade", ""), partes.get("uf", "")) if x)
    campos = (partes.get("via", ""), partes.get("numero", ""), partes.get("complemento", ""), partes.get("bairro", ""), cidade, f"{cep[:5]}-{cep[5:]}" if len(cep) == 8 else cep)
    return ", ".join(c for c in campos if c)


def candidatos_endereco_em_partes(linhas: list[str], numero: int) -> list[Candidato]:
    """Cadastro com "Logradouro:", "Número:", "Bairro:"... separados: junta as partes num endereço só."""
    achados, bloco = [], {}

    def fechar():
        if bloco.get("via") and len(bloco) >= 2:
            achados.append(Candidato("endereco", _compor_endereco(bloco), numero, "Endereço em partes", 0.85))
            if bloco.get("cidade"):
                achados.append(Candidato("municipio_uf", "-".join(x for x in (bloco["cidade"], bloco.get("uf", "")) if x), numero, "Endereço em partes", 0.85))
        bloco.clear()

    for i, linha in enumerate(linhas):
        partes = list(_PARTE_ENDERECO.finditer(linha))
        for k, m in enumerate(partes):
            fim = partes[k + 1].start() if k + 1 < len(partes) else len(linha)
            valor = linha[m.end():fim].strip()
            if not valor:  # valor na linha de baixo
                proxima = next((l for l in linhas[i + 1:i + 2] if l), "")
                valor = proxima if proxima and not _PARTE_ENDERECO.search(proxima) and ":" not in proxima else ""
            chave = _PARTES_CHAVE[m.group(1).lower()]
            if chave in bloco and valor:
                fechar()
            if valor:
                bloco[chave] = valor
    fechar()
    return achados


# --- contratos: cláusulas A1/A2... com uma ou mais pessoas por parte ----------------------------------------------

_CLAUSULA = re.compile(r"\bA(\d{1,2})\s*-\s+")
# Início de pessoa: NOME EM MAIÚSCULAS seguido de vírgula e da qualificação ("nacionalidade...", "brasileiro", "nascido(a)"...),
# depois de ponto final, " e ", "e seu cônjuge", "e sua companheira", vírgula... O que importa é a assinatura "NOME, qualificação".
_INICIO_PESSOA = re.compile(
    r"(?:(?<=[.;,]\s)|(?<=\be\s)|(?<=\bcônjuge\s)|(?<=\bconjuge\s)|(?<=\bcompanheira\s)|(?<=\bcompanheiro\s)|^)"
    r"((?:[A-ZÀ-Ý][A-ZÀ-Ý'\-]*\s+){1,7}[A-ZÀ-Ý][A-ZÀ-Ý'\-]*)\s*,\s*"
    r"(?=(?i:nacionalidade|brasileir|estrangeir|nascid|casad|solteir|divorciad|vi[úu]v|maior|capaz|filh[oa]))")
# Quem representa alguém (empresa, procuração) não é uma das partes da cláusula.
_REPRESENTANTE = re.compile(r"(?i)(?:representante|procurador|gerente|diretor|s[óo]cio|administrador|mandat[áa]rio)\b")
_OUTRA_PESSOA = re.compile(r"\be\s+(?:(?:seu|sua)\s+(?:c[ôo]njuge|companheir[oa]|espos[ao]|marido)\s+)?((?:[A-ZÀ-Ý][A-ZÀ-Ý'\-]*\s+){1,7}[A-ZÀ-Ý][A-ZÀ-Ý'\-]*)\s*,")
_MORADA = re.compile(r"(?i)resident[ea]s?(?:\(s\))?\s+e\s+domiciliad[oa]s?(?:\(a\))?(?:\(s\))?\s+(?:em|na|no|à)\s+")
_ESTADO_CIVIL = re.compile(r"(?i)\b(casad[oa]|solteir[oa]|divorciad[oa]|vi[úu]v[oa]|separad[oa]\s+judicialmente|uni[ãa]o\s+est[áa]vel)(?:\(a\))?")
_MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def _grupo_da_clausula(inicio: str) -> str:
    t = _plano(inicio[:90])
    if "vendedor" in t:
        return "vendedor"
    return "comprador" if any(k in t for k in ("comprador", "devedor", "proponente", "outorgado")) else ""


def _pessoas_da_clausula(texto: str, grupo: str) -> list[tuple[str, int, int]]:
    """(nome, início, fim) de cada pessoa da cláusula: o 1º nome vem depois de ":".

    Compradores: os demais começam em "NOME, qualificação" (ponto final, " e ", "e seu cônjuge", vírgula): união estável e
    parentes não têm um conector fixo. Vendedor: só " e NOME," (a leitura branda aqui pegaria o representante legal da empresa).
    A cláusula da credora (gerente da Caixa) nem chega aqui.
    """
    dois = texto.find(":")
    primeiro = re.match(r"\s*([^,]{3,120}),", texto[dois + 1:]) if dois >= 0 else None
    if not primeiro:
        return []
    inicio0 = dois + 1 + primeiro.start(1)
    achados = [(primeiro.group(1).strip(), inicio0)]
    padroes = (_INICIO_PESSOA, _OUTRA_PESSOA) if grupo == "comprador" else (_OUTRA_PESSOA,)
    candidatos = sorted((m.start(1), m.group(1).strip()) for padrao in padroes for m in padrao.finditer(texto, inicio0 + len(primeiro.group(1))))
    for pos, nome in candidatos:
        if nome.casefold() not in {n.casefold() for n, _ in achados} and not _REPRESENTANTE.match(nome):
            achados.append((nome, pos))
    return [(nome, ini, achados[k + 1][1] if k + 1 < len(achados) else len(texto)) for k, (nome, ini) in enumerate(achados)]


def _data_por_extenso(dia: str, mes: str, ano: str) -> str | None:
    numero = _MESES.get(_plano(mes))
    texto = f"{int(dia):02d}/{numero:02d}/{ano}" if numero else ""
    return texto if texto and validar_data(texto) else None


def candidatos_de_contrato(paginas: list[str]) -> list[Candidato]:
    """Dados de cada comprador/vendedor lidos das cláusulas "A1 - VENDEDOR(ES): ...", "A2 - COMPRADOR(ES)...",
    mais CPF da página de assinaturas, data e local do contrato."""
    achados: list[Candidato] = []
    corrido = " ".join(re.sub(r"\s+", " ", t) for t in paginas)
    limites, soma = [], 0
    for numero, t in enumerate(paginas, 1):
        soma += len(re.sub(r"\s+", " ", t)) + 1
        limites.append((soma, numero))
    pagina_de = lambda pos: next((n for fim, n in limites if pos < fim), len(paginas) or 1)  # noqa: E731
    marcas = list(_CLAUSULA.finditer(corrido))
    conhecidas: dict[str, tuple[str, int]] = {}
    for k, marca in enumerate(marcas):
        fim = marcas[k + 1].start() if k + 1 < len(marcas) else len(corrido)
        clausula = corrido[marca.end():fim]
        grupo = _grupo_da_clausula(clausula)
        pessoas = _pessoas_da_clausula(clausula, grupo) if grupo else []
        pg = pagina_de(marca.start())

        def novo(tipo, valor, pessoa, confianca=0.88, aviso="", trecho=""):
            achados.append(Candidato(tipo, valor, pg, (trecho or valor)[:120], confianca, aviso=aviso, grupo=grupo, pessoa=pessoa))

        proprios: dict[int, dict] = {}
        for i, (nome, ini, fim_p) in enumerate(pessoas):
            conhecidas[nome.casefold()] = (grupo, i)
            novo("nome", nome, i, 0.9)
            bloco = clausula[ini:fim_p]
            empresa = bool(re.search(r"(?i)\bCNPJ\b", bloco))  # CPF, CNH e nascimento do bloco são do representante, não da empresa
            if not empresa and (m := re.search(r"(?i)nascid[oa](?:\(a\))?\s+em\s+" + _DATA_RE + r"(?:\s*,\s*([^,]{3,60}),)?", bloco)):
                if validar_data(m.group(1)):
                    novo("nascimento", m.group(1), i, 0.92)
                if m.group(2):
                    novo("ocupacao", m.group(2).strip(), i)
            bloco_pessoal = "" if empresa else bloco
            if m := re.search(r"(?i)e-?mail:?\s*([\w.+-]+@[\w-]+(?:\.[\w-]+)+)", bloco):
                if validar_email(m.group(1)):
                    novo("email", m.group(1).lower(), i, 0.92)
            if m := re.search(r"(?i)\bCPF\s*(?:n[ºo°.]*\s*)?[:\-]?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", bloco_pessoal):
                if c := _moldar("cpf", m.group(1), pg, m.group(0)):
                    c.grupo, c.pessoa = grupo, i
                    achados.append(c)
            if m := re.search(r"(?i)\bCNPJ\s*(?:n[ºo°.]*\s*)?[:\-]?\s*([0-9A-Z./-]{14,18})", bloco):
                if c := _moldar("cnpj", m.group(1), pg, m.group(0)):
                    c.grupo, c.pessoa = grupo, i
                    achados.append(c)
            if m := re.search(r"(?i)\bCNH\s*(?:n[ºo°.]*\s*)?([\d.\-]{5,})", bloco_pessoal):
                novo("cnh", m.group(1).strip(".-"), i, 0.7, "É o número da CNH, não de um RG.", m.group(0))
            if m := re.search(r"(?i)(?:carteira de identidade|\bRG\b)\s*(?:n[ºo°.]*\s*)?([\w.\-/]{5,})(?:\s*,?\s*expedid[ao]\s+por\s+([^,]+?)\s+em\s+" + _DATA_RE + ")?", bloco_pessoal):
                novo("rg", m.group(1), i, 0.9, trecho=m.group(0))
                if m.group(2):
                    novo("rg_orgao", m.group(2).strip(), i)
                if m.group(3) and validar_data(m.group(3)):
                    novo("rg_emissao", m.group(3), i)
            # Estado civil, regime, união estável e endereço: cada pessoa pode ter os seus.
            proprios[i] = {}
            if not empresa:
                if m := _ESTADO_CIVIL.search(bloco):
                    proprios[i]["estado_civil"] = (re.sub(r"(?i)([oa])$", "", m.group(1).lower()) + "o(a)" if m.group(1)[-1].lower() in "oa" else m.group(1).lower(), m.group(0))
                if m := re.search(r"(?i)regime\s+(?:de|da)\s+([^,.;]+?)(?:\s+na\s+vig[êe]ncia|,|\.|;|$)", bloco):
                    proprios[i]["regime_casamento"] = (m.group(1).strip(), m.group(0))
                if re.search(r"(?i)uni[ãa]o\s+est[áa]vel", bloco):
                    proprios[i]["uniao_estavel"] = ("SIM", "união estável")
                    if m := re.search(r"(?i)uni[ãa]o\s+est[áa]vel[^.;]{0,140}?(?:desde|em|a\s+partir\s+de)\s+" + _DATA_RE, bloco):
                        if validar_data(m.group(1)):
                            proprios[i]["data_uniao"] = (m.group(1), m.group(0))
                if m := re.search(r"(?i)casad[oa](?:\(a\))?[^.;]{0,160}?(?:desde|em|na\s+data\s+de)\s+" + _DATA_RE, bloco):
                    if validar_data(m.group(1)):
                        proprios[i]["data_casamento"] = (m.group(1), m.group(0))
            if m := _MORADA.search(bloco):
                fim_end = _fim_do_trecho(bloco, m.end(), "ponto")
                # Sem ponto final no bloco (a próxima pessoa vem depois de vírgula e " e "): vai até o fim do bloco.
                valor = re.sub(r"[\s,;.]+(?:e\s*)?$", "", bloco[m.end():fim_end if fim_end >= 0 else len(bloco)]).strip()
                valor = re.sub(r"\s+em\s+([^,/]+)/([A-Z]{2})$", r", \1-\2", valor)  # "Centro em Camocim/CE" → "Centro, Camocim-CE"
                if 5 <= len(valor) <= 200:
                    # "residentes e domiciliados em" (plural) vale para todos; no singular, só para quem o disse.
                    proprios[i]["endereco"] = (valor, valor, bool(re.match(r"(?i)resident(?:es|e\(s\))", m.group(0))) or "domiciliados" in m.group(0).lower())
        if grupo and pessoas:
            conjuge = "conjuge" in _plano(clausula) or "companheir" in _plano(clausula)
            for i, dados in proprios.items():
                for tipo, valor_trecho in dados.items():
                    valor, trecho = valor_trecho[0], valor_trecho[1]
                    if tipo == "endereco" and valor_trecho[2]:
                        novo(tipo, valor, -2, 0.9, trecho=trecho)
                    else:
                        novo(tipo, valor, i, 0.9 if tipo == "endereco" else 0.88, trecho=trecho)
            # "e seu cônjuge FULANA": o que só a primeira pessoa declarou (estado civil, regime) vale para as ligadas por cônjuge/companheiro(a).
            if conjuge and 0 in proprios:
                for i in range(1, len(pessoas)):
                    for tipo in ("estado_civil", "regime_casamento", "uniao_estavel", "data_uniao", "data_casamento"):
                        if tipo in proprios[0] and tipo not in proprios.get(i, {}):
                            novo(tipo, proprios[0][tipo][0], i, 0.8, trecho=proprios[0][tipo][1])
    # Página de assinaturas: "NOME- CPF/CNPJ: número" liga o documento (válido) à pessoa já conhecida pelo nome.
    for m in re.finditer(r"([A-ZÀ-Ý][A-ZÀ-Ý .'\-]{4,}?)\s*-\s*CPF/CNPJ\s*:\s*([0-9A-Z./-]{11,18})", corrido):
        grupo, pessoa = conhecidas.get(m.group(1).strip().casefold(), ("", -1))
        digitos = re.sub(r"\D", "", m.group(2))
        if grupo and len(digitos) == 11 and (c := _moldar("cpf", digitos, pagina_de(m.start()), m.group(0))):
            c.grupo, c.pessoa = grupo, pessoa
            achados.append(c)
    # Data e local do contrato: "CAMOCIM, CE 08 de Novembro de 2026".
    if m := re.search(r"([A-ZÀ-Ý][A-ZÀ-Ý ]{2,40}),\s*([A-Z]{2})\s+(\d{1,2})\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})", corrido):
        pg = pagina_de(m.start())
        if data := _data_por_extenso(m.group(3), m.group(4), m.group(5)):
            achados.append(Candidato("data_assinatura", data, pg, m.group(0)[:120], 0.9))
            achados.append(Candidato("local_assinatura", f"{m.group(1).strip()}-{m.group(2)}", pg, m.group(0)[:120], 0.9))
    return achados


def _bom_texto(valor: str) -> bool:
    letras = sum(c.isalpha() for c in valor)
    return letras >= 3 and bool(_ROTULO_ESCRITO.match(valor))


def _mascara_digitos(digitos: str, cortes: tuple[int, ...], sinais: str) -> str:
    partes, ini = [], 0
    for corte, sinal in zip(cortes, sinais + " "):
        partes.append(digitos[ini:corte] + sinal)
        ini = corte
    return "".join(partes) + digitos[ini:]


def _moldar(tipo: str, valor: str, numero: int, linha: str) -> Candidato | None:
    """Valor lido depois de um rótulo: validado quando há regra; número que não confere vira leitura com aviso."""
    base = dict(pagina=numero, trecho=linha[:120])
    digitos = re.sub(r"\D", "", valor)
    if tipo == "cpf":
        if len(digitos) != 11:
            return None
        ok = validar_cpf(digitos)
        return Candidato("cpf", formatar_cpf(digitos) if ok else _mascara_digitos(digitos, (3, 6, 9), "..-"), confianca=0.95 if ok else 0.6,
                         aviso="" if ok else "Os dígitos do CPF não conferem.", **base)
    if tipo == "cnpj":
        limpo = re.sub(r"[^0-9A-Za-z]", "", valor).upper()
        if len(limpo) != 14:
            return None
        ok = validar_cnpj(limpo)
        return Candidato("cnpj", formatar_cnpj(limpo) if ok else valor.strip(), confianca=0.92 if ok else 0.6, aviso="" if ok else "Os dígitos do CNPJ não conferem.", **base)
    if tipo == "pis":
        ok = validar_pis_pasep(digitos)
        return Candidato("pis", formatar_pis_pasep(digitos) if ok else valor.strip(), confianca=0.9 if ok else 0.6, aviso="" if ok else "Confira o número do PIS/NIS.", **base)
    if tipo == "telefone":
        ok = len(digitos) in (10, 11)
        return Candidato("telefone", formatar_telefone_progressivo(digitos) if ok else valor.strip(), confianca=0.9 if ok else 0.6, aviso="" if ok else "Confira o número de telefone.", **base)
    if tipo in _DATAS:
        return Candidato(tipo, valor, confianca=0.9, **base) if validar_data(valor) else None
    valor = valor.strip(" .;,-")
    return Candidato(tipo, valor, confianca=0.85, **base) if 1 <= len(valor) <= 120 else None


def _derivados(achados: list[Candidato]) -> list[Candidato]:
    """Valores que o documento só sugere: situação ocupacional pelo tipo de ocupação."""
    saida = []
    for c in achados:
        if c.tipo == "ocupacao":
            texto = _plano(c.valor)
            situacao = "APOSENTADO_OU_PENSIONISTA" if ("aposent" in texto or "pension" in texto) else "DESEMPREGADO" if "desempreg" in texto else "ATIVO"
            saida.append(Candidato("situacao_ocupacional", situacao, c.pagina, c.trecho, 0.8))
    return saida


def candidatos_do_texto(paginas: list[str], regras_usuario=None) -> list[Candidato]:
    achados: list[Candidato] = []
    for numero, texto in enumerate(paginas, 1):
        linhas = [" ".join(l.split()) for l in texto.splitlines()]
        for i, linha in enumerate(linhas):
            if not linha:
                continue
            for m in _CPF.finditer(linha):
                antes = linha[:m.start()]
                if _CONTEXTO_PIS.search(antes) and validar_pis_pasep(m.group(1)):
                    achados.append(Candidato("pis", formatar_pis_pasep(m.group(1)), numero, linha[:120], 0.9))
                elif validar_cpf(m.group(1)):
                    rotulado = "cpf" in antes[-14:].lower()
                    achados.append(Candidato("cpf", formatar_cpf(m.group(1)), numero, linha[:120], 0.95 if rotulado else 0.85))
            for m in _PIS.finditer(linha):
                if _CONTEXTO_PIS.search(linha[:m.start()]) and validar_pis_pasep(m.group(1)):
                    achados.append(Candidato("pis", formatar_pis_pasep(m.group(1)), numero, linha[:120], 0.9))
            for m in _CNPJ.finditer(linha.upper()):
                if validar_cnpj(m.group(1)):
                    achados.append(Candidato("cnpj", formatar_cnpj(m.group(1)), numero, linha[:120], 0.9))
            for m in _DATA.finditer(linha):
                if validar_data(m.group(1)) and _CONTEXTO_NASC.search(linha[max(0, m.start() - 40):m.start()] + (linhas[i - 1] if i else "")[-30:]):
                    achados.append(Candidato("nascimento", m.group(1), numero, linha[:120], 0.9))
            for m in _EMAIL.finditer(linha):
                if validar_email(m.group(0)):
                    achados.append(Candidato("email", m.group(0).lower(), numero, linha[:120], 0.9))
            for m in _TELEFONE.finditer(linha):
                achados.append(Candidato("telefone", formatar_telefone_progressivo(m.group(1)), numero, linha[:120], 0.8))
            for m in _CEP.finditer(linha):
                achados.append(Candidato("cep", m.group(1), numero, linha[:120], 0.85))
            for tipo, com_valor, so_rotulo in _ROTULOS:
                m = com_valor.search(linha)
                if m:
                    candidato = _moldar(tipo, _cortar_rotulo(m.group(1)).strip(" .;,-"), numero, linha)
                    if candidato:
                        candidato.confianca = min(candidato.confianca, 0.8) if tipo in ("nome", "razao", "mae", "pai", "endereco") else candidato.confianca
                        achados.append(candidato)
                elif so_rotulo and so_rotulo.match(linha):
                    # Layout "ROTULO" numa linha e o valor na seguinte (RG, CNH, cartão CNPJ).
                    proxima = next((l for l in linhas[i + 1:i + 3] if l), "")
                    if proxima and _bom_texto(proxima):
                        achados.append(Candidato(tipo, proxima.strip(), numero, proxima[:120], 0.7))
    for numero, texto in enumerate(paginas, 1):
        achados += candidatos_endereco_em_partes([" ".join(l.split()) for l in texto.splitlines()], numero)
    achados += candidatos_por_regras(paginas, [*REGRAS_PADRAO, *(regras_usuario or [])])
    achados += candidatos_de_contrato(paginas)
    achados += _derivados(achados)
    for ordem, c in enumerate(achados):
        c.posicao = ordem
    vistos: dict[tuple, Candidato] = {}
    for c in achados:
        chave = (c.tipo, c.valor.casefold(), c.grupo, c.pessoa)
        if chave not in vistos:
            vistos[chave] = c
        elif c.confianca > vistos[chave].confianca:
            c.posicao = vistos[chave].posicao
            vistos[chave] = c
    return list(vistos.values())


# --- ligação com os campos do perfil --------------------------------------------------------------

# semântica do campo → tipos de candidato que o preenchem (em ordem de preferência)
SEMANTICA_TIPOS = {
    "pessoa.nome": ("nome",), "pessoa.cpf": ("cpf",), "pessoa.pis": ("pis",), "pessoa.nascimento": ("nascimento",),
    "pessoa.email": ("email",), "pessoa.telefone": ("telefone",), "pessoa.cep": ("cep",), "pessoa.endereco": ("endereco",),
    "pessoa.mae": ("mae",), "pessoa.pai": ("pai",),
    "vendedor.nome": ("vendedor", "razao", "nome"), "vendedor.documento": ("cnpj", "cpf"),
    "imovel.matricula": ("matricula",), "imovel.endereco": ("endereco_imovel",),
    "pessoa.sexo": ("sexo",), "pessoa.nacionalidade": ("nacionalidade",), "pessoa.naturalidade": ("naturalidade",),
    "pessoa.escolaridade": ("escolaridade",), "pessoa.estado_civil": ("estado_civil",), "pessoa.rg": ("rg", "cnh"),
    "pessoa.rg_orgao": ("rg_orgao",), "pessoa.rg_emissao": ("rg_emissao",), "pessoa.ocupacao": ("ocupacao", "atividade"),
    "pessoa.situacao_ocupacional": ("situacao_ocupacional",), "pessoa.municipio_uf": ("municipio_uf",),
    "pessoa.tipo_imovel": ("tipo_imovel",), "pessoa.ocupacao_imovel": ("ocupacao_imovel",),
    "renda.fonte_pagadora": ("fonte_pagadora",), "renda.cnpj": ("cnpj",), "renda.admissao": ("admissao", "inicio_atividade"),
    "renda.bruta": ("renda_bruta",), "renda.liquida": ("renda_liquida",),
    "pessoa.regime_casamento": ("regime_casamento",), "pessoa.uniao_estavel": ("uniao_estavel",),
    "pessoa.data_casamento_uniao": ("data_casamento", "data_uniao"), "contrato.data": ("data_assinatura",), "contrato.local": ("local_assinatura",),
}
# Palavras do id/rótulo do campo (sem acento nem separadores) → semântica, quando o perfil não declara `semantica`.
PALAVRAS_SEMANTICA = (
    (("casamento", "uniao"), "pessoa.data_casamento_uniao"), (("uniaoestavel",), "pessoa.uniao_estavel"),
    (("regimecasamento",), "pessoa.regime_casamento"), (("regime", "bens"), "pessoa.regime_casamento"),
    (("estadocivil",), "pessoa.estado_civil"), (("situacaoocupacional",), "pessoa.situacao_ocupacional"),
    (("municipiouf", "ocupacao"), "ignorar"),  # município da ocupação não está no cadastro
    (("municipiouf", "residencia"), "pessoa.municipio_uf"), (("profissao",), "pessoa.ocupacao"), (("ocupacao",), "pessoa.ocupacao"),
    (("sexo",), "pessoa.sexo"), (("nacionalidade",), "pessoa.nacionalidade"), (("naturalidade",), "pessoa.naturalidade"),
    (("escolaridade",), "pessoa.escolaridade"), (("instrucao",), "pessoa.escolaridade"),
    (("orgaoemissor",), "pessoa.rg_orgao"), (("rg",), "pessoa.rg"), (("identidade",), "pessoa.rg"),
    (("fontepagadora",), "renda.fonte_pagadora"), (("empregador",), "renda.fonte_pagadora"), (("admissao",), "renda.admissao"),
    (("renda", "bruta"), "renda.bruta"), (("renda", "liquida"), "renda.liquida"),
    (("tipoimovel",), "pessoa.tipo_imovel"),
)


def semantica_do_campo(campo) -> str:
    """Semântica explícita do perfil ou deduzida do id/tipo (o perfil pode sobrescrever com `semantica`)."""
    if getattr(campo, "semantica", ""):
        return campo.semantica
    i, tipo = remover_acentos(campo.id).lower(), campo.tipo
    chave = re.sub(r"[^a-z0-9]", "", remover_acentos(f"{campo.id} {campo.rotulo}").lower())
    if tipo not in ("CPF", "EMAIL", "TELEFONE", "PIS_PASEP", "ENDERECO") and "vendedor" not in i and "endereco" not in i:
        for palavras, semantica in PALAVRAS_SEMANTICA:
            if all(p in chave for p in palavras):
                return semantica
    if "vendedor" in i:
        return "vendedor.documento" if any(k in i for k in ("cpf", "cnpj", "documento")) else "vendedor.nome"
    if "matricula" in i:
        return "imovel.matricula"
    if "endereco" in i or tipo == "ENDERECO":
        return "imovel.endereco" if any(k in i for k in ("imovel", "obra")) else "pessoa.endereco"
    return {"CPF": "pessoa.cpf", "EMAIL": "pessoa.email", "TELEFONE": "pessoa.telefone", "PIS_PASEP": "pessoa.pis"}.get(tipo) or (
        "pessoa.nascimento" if tipo == "DATA" and "nasc" in i else
        "pessoa.cep" if "cep" in i else
        "pessoa.mae" if i.endswith("mae") or "nome_mae" in i else
        "pessoa.pai" if i.endswith("pai") or "nome_pai" in i else
        "pessoa.nome" if i in ("nome", "nome_completo") else "")


def _campos_do_papel(campos, papel: str):
    """`participante`: identidade + campos por participante; `compartilhado`: campos globais."""
    if papel == "participante":
        sinteticos = [("nome_completo", "Nome completo", "TEXTO", "pessoa.nome"), ("cpf", "CPF", "CPF", "pessoa.cpf")]
        yield from ((i, r, t, "participante", s, []) for i, r, t, s in sinteticos)
        yield "data_assinatura", "Data da assinatura", "DATA", "global", "contrato.data", []
        yield "local_assinatura", "Local da assinatura", "TEXTO", "global", "contrato.local", []
    for c in campos:
        if c.id in ("nome_completo", "cpf", "data_assinatura", "local_assinatura"):
            continue
        if (c.escopo == "global") == (papel == "compartilhado"):
            yield c.id, c.rotulo, c.tipo, c.escopo, semantica_do_campo(c), c.opcoes


def _diretos(leitura: Leitura, perfil, papel: str) -> dict[str, dict]:
    """Mapeamento inverso: PDF que o próprio Contracto gerou traz o valor no campo AcroForm de cada origem."""
    escopo = "participante" if papel == "participante" else "global"
    resultado = {}
    for formulario in perfil.formularios:
        for nome_pdf, regra in obter_mapeamento_formulario(formulario).items():
            origem = regra.get("origem") if isinstance(regra, dict) else regra
            formato = (regra.get("formato", "TEXTO") if isinstance(regra, dict) else "TEXTO")
            if not isinstance(origem, str) or "." not in origem or formato.upper() not in {"TEXTO", "MOEDA_SEM_SIMBOLO"}:
                continue
            prefixo, campo_id = origem.split(".", 1)
            if prefixo == escopo and nome_pdf in leitura.campos and campo_id not in resultado:
                resultado[campo_id] = {"valor": leitura.campos[nome_pdf], "pagina": 0, "trecho": nome_pdf, "confianca": 0.95, "metodo": "acroform"}
    return resultado


def _chave_opcao(texto: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _plano(str(texto)))


def propor(leitura: Leitura, perfil, papel: str, regras_usuario=None) -> list[dict]:
    """Sugestões por campo para um papel (participante ou compartilhado), sem repetir campo.

    Em contratos (cláusulas A1/A2) o participante usa os dados dos compradores e o compartilhado os do vendedor;
    com mais de um comprador, `por_pessoa` traz o valor de cada um (None quando a pessoa não tem aquele dado).
    """
    candidatos = candidatos_do_texto(leitura.paginas, regras_usuario)
    diretos = _diretos(leitura, perfil, papel)
    grupo = "comprador" if papel == "participante" else "vendedor"
    pessoas = 1 + max((c.pessoa for c in candidatos if c.grupo == grupo and c.pessoa >= 0), default=-1)
    propostas = []
    for campo_id, rotulo, tipo, escopo, semantica, opcoes_campo in _campos_do_papel(perfil.campos_entrada, papel):
        opcoes = []
        if campo_id in diretos:
            opcoes.append(diretos[campo_id])
        for rank, kind in enumerate(SEMANTICA_TIPOS.get(semantica, ())):
            todos = [c for c in candidatos if c.tipo == kind]
            da_clausula = [c for c in todos if c.grupo == grupo]
            # Com cláusulas no documento, só vale o que veio da parte certa; sem elas, o texto solto.
            pool = da_clausula or [c for c in todos if not c.grupo]
            opcoes.extend({"valor": c.valor, "pagina": c.pagina, "trecho": c.trecho, "confianca": round(c.confianca - 0.02 * rank, 2), "metodo": c.metodo,
                           "posicao": c.posicao, "aviso": c.aviso, "pessoa": c.pessoa if da_clausula else None}
                          for c in sorted(pool, key=lambda c: -c.confianca))
        if tipo in ("SELECAO", "CHECKBOX"):  # só vale o que casa com uma opção do campo ("DIVORCIADO (A)" → "DIVORCIADO(A)")
            casar = {_chave_opcao(o): o for o in (opcoes_campo or ["SIM", "NÃO"])}
            opcoes = [{**o, "valor": casar[_chave_opcao(o["valor"])]} for o in opcoes if _chave_opcao(o["valor"]) in casar]
        if not opcoes:
            continue
        marcadas = [o for o in opcoes if o.get("pessoa") is not None]
        por_pessoa = None
        if marcadas:
            por_pessoa = []
            for k in range(pessoas if papel == "participante" else 1):
                dela = [o for o in marcadas if o["pessoa"] in (k, -2)]
                melhor_dela = max(dela, key=lambda o: o["confianca"]) if dela else None
                por_pessoa.append({"valor": melhor_dela["valor"], "aviso": melhor_dela.get("aviso", ""), "pagina": melhor_dela["pagina"]} if melhor_dela else None)
            primeiros = [o for o in marcadas if o["pessoa"] in (0, -2)] or marcadas
            opcoes = [max(primeiros, key=lambda o: o["confianca"]), *[o for o in opcoes]]
        melhor, *resto = opcoes
        # Em ordem de leitura: com dois proponentes no documento, o 2º valor é do 2º participante.
        ordenadas = list(dict.fromkeys(o["valor"] for o in sorted(opcoes, key=lambda o: o.get("posicao", 0))))[:LIMITE_ALTERNATIVAS + 2]
        melhor = {k: v for k, v in melhor.items() if k != "pessoa"}
        melhor.setdefault("aviso", "")
        propostas.append({"campo_id": campo_id, "rotulo": rotulo, "tipo": tipo, "escopo": escopo, **melhor, "ordenadas": ordenadas, "por_pessoa": por_pessoa,
                          "alternativas": list(dict.fromkeys(o["valor"] for o in resto if o["valor"] != melhor["valor"]))[:LIMITE_ALTERNATIVAS]})
    return propostas
