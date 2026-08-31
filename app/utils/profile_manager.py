"""
Gerenciador de perfis da aplicação.

Cada perfil armazena configurações de modelos e formato de saída,
similar ao sistema de perfis do PDFCreator.

Os perfis são salvos em %APPDATA%/Contracto/contracto_profiles.json.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


_PROFILES_FILE_NAME = "contracto_profiles.json"

PERFIL_PADRAO_NOME = "MCMV"

# Cache em memória de perfis para eliminar I/O em disco
_perfis_cache: list[Perfil] | None = None


@dataclass
class FormularioModelo:
    """Configuração de um formulário PDF associado ao perfil."""
    nome: str
    caminho: str
    geracao: str = "por_participante"  # "por_participante" ou "unico"
    mapeamento: dict[str, str] = field(default_factory=dict)


@dataclass
class DocumentoExtra:
    rotulo: str
    nome_padrao: str


TIPOS_CAMPO_ENTRADA = ["TEXTO", "CPF", "CNPJ", "CPF_CNPJ", "DATA", "MOEDA", "AREA", "TELEFONE", "EMAIL", "SELECAO", "CHECKBOX"]


@dataclass
class CampoEntrada:
    """Especificação de um campo de formulário dinâmico da Etapa 1."""
    id: str                      # Identificador único (ex: 'cpf', 'renda_bruta', 'cnpj')
    rotulo: str                  # Texto exibido no Label (ex: 'CPF', 'CNPJ', 'Renda Bruta')
    tipo: str = "TEXTO"          # "TEXTO", "CPF", "CNPJ", "DATA", "MOEDA", "SELECAO", "CHECKBOX"
    obrigatorio: bool = True
    placeholder: str = ""
    escopo: str = "participante" # "participante" ou "global"
    opcoes: list[str] = field(default_factory=list) # Para tipo "SELECAO"
    valor_padrao: str = ""
    icone: str = "form"
    aba: str = "Geral"           # Para sub-seções/paginação

    def __post_init__(self) -> None:
        if self.tipo:
            self.tipo = self.tipo.upper()


@dataclass
class Perfil:
    """Um perfil de configuração de modelos, campos de entrada e formato de saída."""
    nome: str = PERFIL_PADRAO_NOME
    formularios: list[FormularioModelo] = field(default_factory=list)
    documentos_extras: list[DocumentoExtra] = field(default_factory=list)
    campos_entrada: list[CampoEntrada] = field(default_factory=list)
    formato_saida: str = "PDF/A-2b"     # "PDF/A-2b" ou "PDF"
    modo_fluxo: str = "contrato"        # "contrato" (completo) ou "formulario_simples" (avulso)
    max_participantes: int = 4          # 1 a 4 participantes permitidos

    def usa_modelos_embutidos(self) -> bool:
        """Retorna True se usar os formulários embutidos (PPE e 1º Imóvel sem caminhos)."""
        if not self.formularios:
            return True
        for f in self.formularios:
            if f.caminho:
                return False
        return True

    def obter_campos_participante(self) -> list[CampoEntrada]:
        """Retorna os campos configurados no escopo de cada participante."""
        return [c for c in self.campos_entrada if c.escopo == "participante"]

    def obter_campos_globais(self) -> list[CampoEntrada]:
        """Retorna os campos configurados no escopo global (compartilhado)."""
        return [c for c in self.campos_entrada if c.escopo == "global"]

    def obter_abas_disponiveis(self) -> list[str]:
        """Retorna a lista ordenada de abas/páginas definidas para este perfil."""
        abas = []
        for c in self.campos_entrada:
            if c.aba and c.aba not in abas:
                abas.append(c.aba)
        return abas if abas else ["Geral"]


def _diretorio_perfis() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        config_dir = Path(appdata) / "Contracto"
    else:
        config_dir = Path(__file__).resolve().parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _caminho_perfis() -> Path:
    return _diretorio_perfis() / _PROFILES_FILE_NAME


def invalidar_cache() -> None:
    """Invalida o cache em memória de perfis."""
    global _perfis_cache
    _perfis_cache = None


def carregar_perfis(forcar_disco: bool = False) -> list[Perfil]:
    """Carrega todos os perfis do disco (ou do cache em memória). Sempre inclui os perfis padrão."""
    global _perfis_cache

    if _perfis_cache is not None and not forcar_disco:
        return [
            Perfil(
                nome=p.nome,
                formularios=[FormularioModelo(f.nome, f.caminho, f.geracao, dict(f.mapeamento)) for f in p.formularios],
                documentos_extras=[DocumentoExtra(d.rotulo, d.nome_padrao) for d in p.documentos_extras],
                campos_entrada=[
                    CampoEntrada(
                        id=c.id, rotulo=c.rotulo, tipo=c.tipo, obrigatorio=c.obrigatorio,
                        placeholder=c.placeholder, escopo=c.escopo, opcoes=list(c.opcoes),
                        valor_padrao=c.valor_padrao, icone=c.icone, aba=c.aba
                    )
                    for c in p.campos_entrada
                ],
                formato_saida=p.formato_saida,
                modo_fluxo=p.modo_fluxo,
                max_participantes=p.max_participantes,
            )
            for p in _perfis_cache
        ]

    caminho = _caminho_perfis()
    perfis: list[Perfil] = []

    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for item in dados:
                if "formularios" in item:
                    item["formularios"] = [
                        FormularioModelo(
                            nome=fm["nome"],
                            caminho=fm.get("caminho", ""),
                            geracao=fm.get("geracao", "por_participante"),
                            mapeamento=fm.get("mapeamento", {}),
                        )
                        for fm in item["formularios"]
                    ]
                else:
                    item["formularios"] = []

                if "documentos_extras" in item:
                    if item.get("nome") == "SBPE":
                        item["documentos_extras"] = [DocumentoExtra(**d) for d in item["documentos_extras"]]
                    else:
                        item["documentos_extras"] = [DocumentoExtra(**d) for d in item["documentos_extras"]]
                else:
                    if item.get("nome") == "SBPE":
                        item["documentos_extras"] = _documentos_extras_sbpe()
                    elif item.get("modo_fluxo") == "formulario_simples":
                        item["documentos_extras"] = []
                    else:
                        item["documentos_extras"] = _documentos_extras_padrao()

                if "campos_entrada" in item:
                    item["campos_entrada"] = [CampoEntrada(**c) for c in item["campos_entrada"]]
                else:
                    item["campos_entrada"] = _campos_entrada_padrao()

                if "max_participantes" not in item:
                    item["max_participantes"] = 1 if item.get("nome") in ("ITBI", "Isenção de Tributos", "Isenção de Tributos Municipais") else 4
                        
                perfis.append(Perfil(**item))
        except (json.JSONDecodeError, OSError, TypeError):
            perfis = []

    # Migração e normalização de nomes e campos dos perfis
    for p in perfis:
        if p.nome == "Padrão":
            p.nome = PERFIL_PADRAO_NOME  # "MCMV"
        elif p.nome in ("Formulário CAIXA", "MO 30.844"):
            p.nome = "Form Cliente"
            p.modo_fluxo = "formulario_simples"
            if p.formularios:
                p.formularios[0].nome = "Form Cliente"

        # Garantir limites oficiais de participantes
        if p.nome in ("MCMV", "SBPE", "Form Cliente"):
            if not getattr(p, "max_participantes", None) or p.max_participantes < 1:
                p.max_participantes = 4
        elif p.nome in ("ITBI", "Isenção de Tributos", "Isenção de Tributos Municipais"):
            p.max_participantes = 1

        # Sincronização dos campos do Form Cliente
        if p.nome == "Form Cliente":
            p.campos_entrada = _campos_entrada_form_cliente()

        # Sincronização dos campos do ITBI
        if p.nome == "ITBI":
            p.campos_entrada = _campos_entrada_itbi()

        # Sincronização dos campos da Isenção
        if p.nome in ("Isenção de Tributos", "Isenção de Tributos Municipais"):
            p.campos_entrada = _campos_entrada_isencao_tributos()

        # Garantir placeholder nos perfis de contrato
        if p.nome in ("MCMV", "SBPE"):
            for c in p.campos_entrada:
                if c.id == "endereco" and not c.placeholder:
                    c.placeholder = "Ex: Rua das Flores, 123 - Centro, Camocim - CE"

    _formularios_builtin = [
        FormularioModelo(nome="PPE", caminho="", geracao="por_participante", mapeamento={}),
        FormularioModelo(nome="1º Imóvel", caminho="", geracao="por_participante", mapeamento={}),
    ]

    # Garantir que o perfil MCMV sempre existe
    if not any(p.nome == PERFIL_PADRAO_NOME for p in perfis):
        perfis.insert(0, Perfil(
            nome=PERFIL_PADRAO_NOME,
            formularios=list(_formularios_builtin),
            documentos_extras=_documentos_extras_padrao(),
            campos_entrada=_campos_entrada_padrao(),
            modo_fluxo="contrato",
            max_participantes=4,
        ))

    # Garantir que o perfil SBPE sempre existe
    if not any(p.nome == "SBPE" for p in perfis):
        perfis.append(Perfil(
            nome="SBPE",
            formularios=list(_formularios_builtin),
            documentos_extras=_documentos_extras_sbpe(),
            campos_entrada=_campos_entrada_padrao(),
            modo_fluxo="contrato",
            max_participantes=4,
        ))

    # Garantir que o perfil Form Cliente sempre existe
    if not any(p.nome == "Form Cliente" for p in perfis):
        perfis.append(Perfil(
            nome="Form Cliente",
            formularios=[
                FormularioModelo(
                    nome="Form Cliente",
                    caminho="",
                    geracao="por_processo",
                    mapeamento={},
                )
            ],
            documentos_extras=[],
            campos_entrada=_campos_entrada_form_cliente(),
            modo_fluxo="formulario_simples",
            formato_saida="PDF",
            max_participantes=4,
        ))

    # Garantir que o perfil ITBI sempre existe
    if not any(p.nome == "ITBI" for p in perfis):
        perfis.append(Perfil(
            nome="ITBI",
            formularios=[
                FormularioModelo(
                    nome="Declaração ITBI",
                    caminho="",
                    geracao="por_processo",
                    mapeamento={},
                )
            ],
            documentos_extras=[],
            campos_entrada=_campos_entrada_itbi(),
            modo_fluxo="formulario_simples",
            formato_saida="PDF",
            max_participantes=1,
        ))

    # Garantir que o perfil Isenção de Tributos sempre existe
    if not any(p.nome == "Isenção de Tributos" for p in perfis):
        perfis.append(Perfil(
            nome="Isenção de Tributos",
            formularios=[
                FormularioModelo(
                    nome="Requerimento de Isenção",
                    caminho="",
                    geracao="por_participante",
                    mapeamento={},
                )
            ],
            documentos_extras=[],
            campos_entrada=_campos_entrada_isencao_tributos(),
            modo_fluxo="formulario_simples",
            formato_saida="PDF",
            max_participantes=1,
        ))

    _perfis_cache = perfis
    return perfis


def listar_perfis_por_modo(modo: str = "contrato") -> list[Perfil]:
    """Retorna os perfis filtrados pelo modo de operação ('contrato' ou 'formulario_simples')."""
    perfis = carregar_perfis()
    modo_norm = "formulario_simples" if modo.lower() in ("simples", "formulario_simples") else "contrato"
    return [p for p in perfis if getattr(p, "modo_fluxo", "contrato") == modo_norm]


def listar_nomes_perfis_por_modo(modo: str = "contrato") -> list[str]:
    """Retorna apenas os nomes dos perfis para o modo informado."""
    perfis_modo = listar_perfis_por_modo(modo)
    return [p.nome for p in perfis_modo]

def _campos_entrada_form_cliente() -> list[CampoEntrada]:
    """Retorna a lista de campos de entrada padrão para o Form Cliente (FORM CLIENTE.pdf)."""
    return [
        CampoEntrada(
            id="agencia",
            rotulo="Agência",
            tipo="TEXTO",
            obrigatorio=False,
            placeholder="Ex: 1234",
            escopo="participante",
            icone="briefcase",
            aba="Conta CAIXA",
        ),
        CampoEntrada(
            id="conta_caixa",
            rotulo="Conta CAIXA",
            tipo="TEXTO",
            obrigatorio=False,
            placeholder="Ex: 00012345-6",
            escopo="participante",
            icone="briefcase",
            aba="Conta CAIXA",
        ),
        CampoEntrada(
            id="autorizo_debito_parcela",
            rotulo="Débito de parcelas",
            tipo="CHECKBOX",
            obrigatorio=False,
            valor_padrao="Sim",
            escopo="global",
            icone="check",
            aba="Autorizações e Débitos em Conta",
        ),
        CampoEntrada(
            id="autorizo_tarifa_avaliacao",
            rotulo="Tarifa de avaliação",
            tipo="CHECKBOX",
            obrigatorio=False,
            valor_padrao="Sim",
            escopo="global",
            icone="check",
            aba="Autorizações e Débitos em Conta",
        ),
        CampoEntrada(
            id="data_assinatura",
            rotulo="Data da assinatura",
            tipo="DATA",
            obrigatorio=True,
            placeholder="DD/MM/AAAA",
            escopo="global",
            icone="calendar",
            aba="Local e Data",
        ),
        CampoEntrada(
            id="local_assinatura",
            rotulo="Local da assinatura",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: CAMOCIM-CE",
            escopo="global",
            icone="location",
            aba="Local e Data",
        ),
    ]


def _campos_entrada_mo30844() -> list[CampoEntrada]:
    """Alias para _campos_entrada_form_cliente."""
    return _campos_entrada_form_cliente()


def _campos_entrada_itbi() -> list[CampoEntrada]:
    """Retorna os campos de entrada para a Declaração de Pagamento de ITBI."""
    return [
        CampoEntrada(
            id="endereco",
            rotulo="Endereço",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: Rua das Flores, 123 - Centro",
            escopo="participante",
            icone="location",
            aba="Dados do Comprador",
        ),
        CampoEntrada(
            id="comprador_telefone",
            rotulo="Telefone",
            tipo="TELEFONE",
            obrigatorio=False,
            placeholder="Ex: (88) 99999-9999",
            escopo="participante",
            icone="help",
            aba="Dados do Comprador",
        ),
        CampoEntrada(
            id="comprador_email",
            rotulo="E-mail",
            tipo="EMAIL",
            obrigatorio=False,
            placeholder="Ex: comprador@email.com",
            escopo="participante",
            icone="globe",
            aba="Dados do Comprador",
        ),
        CampoEntrada(
            id="nome_vendedor",
            rotulo="Nome Vendedor",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: CONSTRUTORA EXEMPLO LTDA",
            escopo="global",
            icone="person",
            aba="Dados do Vendedor",
        ),
        CampoEntrada(
            id="cpf_cnpj_vendedor",
            rotulo="CPF/CNPJ Vendedor",
            tipo="CPF_CNPJ",
            obrigatorio=True,
            placeholder="Ex: 00.000.000/0001-00",
            escopo="global",
            icone="document",
            aba="Dados do Vendedor",
        ),
        CampoEntrada(
            id="matricula",
            rotulo="Matrícula",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: 12.345",
            escopo="global",
            icone="document",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="cartorio_oficio",
            rotulo="Ofício Cartório",
            tipo="TEXTO",
            obrigatorio=True,
            valor_padrao="2",
            placeholder="Ex: 2",
            escopo="global",
            icone="briefcase",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="cartorio_local",
            rotulo="Comarca Cartório",
            tipo="TEXTO",
            obrigatorio=True,
            valor_padrao="CAMOCIM-CE",
            placeholder="Ex: CAMOCIM-CE",
            escopo="global",
            icone="location",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="iptu",
            rotulo="Inscrição IPTU",
            tipo="TEXTO",
            obrigatorio=False,
            placeholder="Ex: 01.02.003.0004.001",
            escopo="global",
            icone="document",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="area_terreno",
            rotulo="Área Terreno (m²)",
            tipo="AREA",
            obrigatorio=True,
            placeholder="Ex: 200,00",
            escopo="global",
            icone="ratio",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="area_construida",
            rotulo="Área Constr. (m²)",
            tipo="AREA",
            obrigatorio=False,
            placeholder="Ex: 65,50",
            escopo="global",
            icone="ratio",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="fracao_ideal",
            rotulo="Fração Ideal (%)",
            tipo="TEXTO",
            obrigatorio=True,
            valor_padrao="100",
            placeholder="Ex: 100",
            escopo="global",
            icone="ratio",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="enquadramento_isencao",
            rotulo="Enquadramento na Isenção (Lei 1648/2023)",
            tipo="CHECKBOX",
            valor_padrao="Sim",
            obrigatorio=False,
            escopo="global",
            icone="check",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="endereco_imovel",
            rotulo="Endereço Imóvel",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: Rua das Flores, 123 - Centro, Camocim-CE",
            escopo="global",
            icone="location",
            aba="Dados do Imóvel e Cartório",
        ),
        CampoEntrada(
            id="valor_compra",
            rotulo="Compra e Venda",
            tipo="MOEDA",
            obrigatorio=True,
            placeholder="Ex: 180.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="valor_avaliacao",
            rotulo="Avaliação CAIXA",
            tipo="MOEDA",
            obrigatorio=True,
            placeholder="Ex: 185.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="valor_financiado",
            rotulo="Financiamento",
            tipo="MOEDA",
            obrigatorio=True,
            placeholder="Ex: 140.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="valor_subsidio",
            rotulo="Subsídio",
            tipo="MOEDA",
            obrigatorio=False,
            placeholder="Ex: 20.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="valor_fgts",
            rotulo="FGTS",
            tipo="MOEDA",
            obrigatorio=False,
            placeholder="Ex: 10.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="valor_recursos",
            rotulo="Recursos Próprios",
            tipo="MOEDA",
            obrigatorio=False,
            placeholder="Ex: 10.000,00",
            escopo="global",
            icone="calculator",
            aba="Valores da Operação",
        ),
        CampoEntrada(
            id="data_assinatura",
            rotulo="Data da assinatura",
            tipo="DATA",
            obrigatorio=True,
            placeholder="DD/MM/AAAA",
            escopo="global",
            icone="calendar",
            aba="Local e Data",
        ),
        CampoEntrada(
            id="local_assinatura",
            rotulo="Local da assinatura",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: CAMOCIM-CE",
            escopo="global",
            icone="location",
            aba="Local e Data",
        ),
    ]


def _campos_entrada_isencao_tributos() -> list[CampoEntrada]:
    """Retorna os campos de entrada para o Requerimento de Isenção de Tributos Municipais."""
    return [
        CampoEntrada(
            id="rg",
            rotulo="RG do Requerente",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: 2008123456-7 SSP/CE",
            escopo="participante",
            icone="document",
            aba="Qualificação do Requerente",
        ),
        CampoEntrada(
            id="estado_civil",
            rotulo="Estado Civil",
            tipo="SELECAO",
            obrigatorio=True,
            opcoes=["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"],
            valor_padrao="Solteiro(a)",
            escopo="participante",
            icone="person",
            aba="Qualificação do Requerente",
        ),
        CampoEntrada(
            id="endereco",
            rotulo="Endereço",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: Rua das Flores, 123 - Centro, Camocim - CE",
            escopo="participante",
            icone="location",
            aba="Qualificação do Requerente",
        ),
        CampoEntrada(
            id="matricula",
            rotulo="Matrícula do Imóvel",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: 12.345",
            escopo="global",
            icone="document",
            aba="Dados do Imóvel",
        ),
        CampoEntrada(
            id="data_assinatura",
            rotulo="Data da assinatura",
            tipo="DATA",
            obrigatorio=True,
            placeholder="DD/MM/AAAA",
            escopo="global",
            icone="calendar",
            aba="Local e Data",
        ),
        CampoEntrada(
            id="local_assinatura",
            rotulo="Local da assinatura",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: CAMOCIM-CE",
            escopo="global",
            icone="location",
            aba="Local e Data",
        ),
    ]


def _campos_entrada_padrao() -> list[CampoEntrada]:
    """Retorna a lista de campos de entrada padrão da Etapa 1."""
    return [
        CampoEntrada(
            id="endereco",
            rotulo="Endereço",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: Rua das Flores, 123 - Centro, Camocim - CE",
            escopo="participante",
            icone="location",
            aba="Geral",
        ),
        CampoEntrada(
            id="data_assinatura",
            rotulo="Data da assinatura",
            tipo="DATA",
            obrigatorio=True,
            placeholder="DD/MM/AAAA",
            escopo="global",
            icone="calendar",
            aba="Geral",
        ),
        CampoEntrada(
            id="local_assinatura",
            rotulo="Local da assinatura",
            tipo="TEXTO",
            obrigatorio=True,
            placeholder="Ex: CAMOCIM-CE",
            escopo="global",
            icone="location",
            aba="Geral",
        ),
    ]


def _documentos_extras_padrao() -> list[DocumentoExtra]:
    """Retorna a lista de documentos extras (Etapa 2) padrão para o perfil MCMV."""
    return [
        DocumentoExtra("Contrato", "CONTRATO"),
        DocumentoExtra("Planilha de Evolução", "PLANILHA DE EVOLUCAO"),
        DocumentoExtra("Protocolo da Planilha", "PROTOCOLO DA PLANILHA"),
        DocumentoExtra("Aviso de Crédito", "AVISO DE CREDITO"),
        DocumentoExtra("Origem de Recursos", "ORIGEM DE RECURSOS"),
    ]


def _documentos_extras_sbpe() -> list[DocumentoExtra]:
    """Retorna a lista de documentos extras para o perfil SBPE (MCMV + Cédula de Crédito)."""
    return _documentos_extras_padrao() + [
        DocumentoExtra("Cédula de Crédito", "CEDULA DE CREDITO"),
    ]


def salvar_perfis(perfis: list[Perfil]) -> None:
    """Salva todos os perfis no disco e atualiza o cache imediatamente."""
    global _perfis_cache

    caminho = _caminho_perfis()
    dados = [asdict(p) for p in perfis]
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    _perfis_cache = perfis


def obter_perfil(nome: str) -> Optional[Perfil]:
    """Retorna um perfil pelo nome a partir da memória, ou None se não existir."""
    global _perfis_cache
    if _perfis_cache is None:
        carregar_perfis()
    for p in _perfis_cache:
        if p.nome == nome:
            return p
    return None


def listar_nomes_perfis() -> list[str]:
    """Retorna a lista de nomes de todos os perfis diretamente da memória."""
    global _perfis_cache
    if _perfis_cache is None:
        carregar_perfis()
    return [p.nome for p in _perfis_cache]


def adicionar_perfil(perfil: Perfil) -> None:
    """Adiciona um novo perfil. Erro se já existir um com o mesmo nome."""
    perfis = carregar_perfis()
    if any(p.nome == perfil.nome for p in perfis):
        raise ValueError(f"Já existe um perfil com o nome '{perfil.nome}'.")
    perfis.append(perfil)
    salvar_perfis(perfis)


def atualizar_perfil(nome_antigo: str, perfil_novo: Perfil) -> None:
    """Atualiza um perfil existente usando o seu nome antigo."""
    perfis = carregar_perfis()
    for i, p in enumerate(perfis):
        if p.nome == nome_antigo:
            perfis[i] = perfil_novo
            salvar_perfis(perfis)
            return
    raise ValueError(f"Perfil '{nome_antigo}' não encontrado.")


def excluir_perfil(nome: str) -> None:
    """Exclui um perfil. O perfil Padrão não pode ser excluído."""
    if nome == PERFIL_PADRAO_NOME:
        raise ValueError("O perfil Padrão não pode ser excluído.")
    perfis = carregar_perfis()
    perfis = [p for p in perfis if p.nome != nome]
    salvar_perfis(perfis)


def duplicar_perfil(nome_origem: str, novo_nome: str | None = None) -> Perfil:
    """Duplica um perfil existente, criando uma cópia independente com nome único.
    
    Args:
        nome_origem: Nome do perfil a ser duplicado.
        novo_nome: Nome opcional para o novo perfil. Se não fornecido, gera "Nome (Cópia)".

    Returns:
        O novo Perfil criado e salvo no disco.

    Raises:
        ValueError: Se o perfil de origem não for encontrado ou se o novo_nome já existir.
    """
    perfis = carregar_perfis()
    origem = next((p for p in perfis if p.nome == nome_origem), None)
    if not origem:
        raise ValueError(f"Perfil de origem '{nome_origem}' não encontrado.")

    nomes_existentes = {p.nome for p in perfis}

    if not novo_nome:
        candidato = f"{nome_origem} (Cópia)"
        contador = 2
        while candidato in nomes_existentes:
            candidato = f"{nome_origem} (Cópia {contador})"
            contador += 1
        novo_nome = candidato
    elif novo_nome in nomes_existentes:
        raise ValueError(f"Já existe um perfil com o nome '{novo_nome}'.")

    # Clona formulários e documentos extras de forma independente
    novos_formularios = [
        FormularioModelo(
            nome=f.nome,
            caminho=f.caminho,
            geracao=f.geracao,
            mapeamento=dict(f.mapeamento),
        )
        for f in origem.formularios
    ]
    novos_campos = [
        CampoEntrada(
            id=c.id,
            rotulo=c.rotulo,
            tipo=c.tipo,
            obrigatorio=c.obrigatorio,
            placeholder=c.placeholder,
            escopo=c.escopo,
            opcoes=list(c.opcoes),
            valor_padrao=c.valor_padrao,
            icone=c.icone,
            aba=c.aba,
        )
        for c in origem.campos_entrada
    ]

    novos_extras = [
        DocumentoExtra(rotulo=d.rotulo, nome_padrao=d.nome_padrao)
        for d in origem.documentos_extras
    ]

    novo_perfil = Perfil(
        nome=novo_nome,
        formularios=novos_formularios,
        documentos_extras=novos_extras,
        campos_entrada=novos_campos,
        formato_saida=origem.formato_saida,
    )
    perfis.append(novo_perfil)
    salvar_perfis(perfis)
    return novo_perfil

