"""
Gerenciador de perfis da aplicação.

Cada perfil armazena configurações de modelos e formato de saída,
similar ao sistema de perfis do PDFCreator.

Os perfis são salvos em %APPDATA%/Contracto/contracto_profiles.json.
"""

from __future__ import annotations

import copy
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from utils.caminhos import diretorio_dados_local, guardar_copia_corrompida
from utils.resource_path import carregar_configuracao_inicial
from utils.json_storage import salvar_json


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
    mapeamento: dict[str, str | dict] = field(default_factory=dict)
    identificador: str = ""
    recurso: str = ""


@dataclass
class DocumentoExtra:
    rotulo: str
    nome_padrao: str


TIPOS_CAMPO_ENTRADA = [
    "TEXTO", "TEXTO_LONGO", "CPF", "CNPJ", "CPF_CNPJ", "PIS_PASEP",
    "DATA", "MOEDA", "AREA", "INTEIRO", "ANO", "TELEFONE", "EMAIL",
    "SELECAO", "CHECKBOX",
]


def ordenar_campos_para_exibicao(campos: list["CampoEntrada"]) -> list["CampoEntrada"]:
    """Mantém a ordem do perfil, colocando controles antes dos campos dependentes."""
    pendentes = list(campos)
    resultado: list[CampoEntrada] = []
    ids_incluidos: set[str] = set()
    while pendentes:
        avancou = False
        for campo in list(pendentes):
            dependencias = {
                chave
                for alternativa in (campo.visivel_quando or [])
                for chave in alternativa
            }
            if not dependencias or dependencias.issubset(ids_incluidos):
                resultado.append(campo)
                ids_incluidos.add(campo.id)
                pendentes.remove(campo)
                avancou = True
        if not avancou:
            resultado.extend(pendentes)
            break
    return resultado


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
    ajuda: str = ""
    minimo: int | None = None
    maximo: int | None = None
    # Lista de alternativas (OR); cada alternativa é um mapa campo -> valores aceitos (AND).
    visivel_quando: list[dict[str, list[str]]] = field(default_factory=list)
    limpar_quando_oculto: bool = True
    calculo: str = ""
    ate_participante: int | None = None

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
    identificador: str = ""
    ordem: int = 100
    usar_paginacao: bool = False
    correcoes_aplicadas: list[str] = field(default_factory=list)
    # Mapeia subtítulos para uma mesma página sem perder a separação visual.
    agrupamento_paginas: dict[str, str] = field(default_factory=dict)

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
        return ordenar_campos_para_exibicao([c for c in self.campos_entrada if c.escopo == "participante"])

    def obter_campos_globais(self) -> list[CampoEntrada]:
        """Retorna os campos configurados no escopo global (compartilhado)."""
        return ordenar_campos_para_exibicao([c for c in self.campos_entrada if c.escopo == "global"])

    def obter_abas_disponiveis(self) -> list[str]:
        """Retorna a lista ordenada de abas/páginas definidas para este perfil."""
        abas = []
        for c in self.campos_entrada:
            if c.id in ("data_assinatura", "local_assinatura"):
                continue
            pagina = self.obter_pagina_do_campo(c)
            if pagina and pagina not in abas:
                abas.append(pagina)
        return abas if abas else ["Geral"]

    def obter_pagina_do_campo(self, campo: CampoEntrada) -> str:
        """Resolve a página do campo mantendo `aba` como subtítulo visual."""
        aba = campo.aba or "Geral"
        return self.agrupamento_paginas.get(aba, aba)


def _diretorio_perfis() -> Path:
    """Retorna o diretório de perfis (primeiro local gravável)."""
    return diretorio_dados_local("Contracto")


def _caminho_perfis() -> Path:
    return _diretorio_perfis() / _PROFILES_FILE_NAME


def invalidar_cache() -> None:
    """Invalida o cache em memória de perfis."""
    global _perfis_cache
    _perfis_cache = None


def _perfil_de_dict(dados: dict) -> Perfil:
    """Monta um perfil salvo em JSON."""
    item = copy.deepcopy(dados)
    item.pop("schema", None)
    item["formularios"] = [FormularioModelo(**formulario) for formulario in item.get("formularios", [])]
    item["documentos_extras"] = [DocumentoExtra(**documento) for documento in item.get("documentos_extras", [])]
    item["campos_entrada"] = [CampoEntrada(**campo) for campo in item.get("campos_entrada", [])]
    return Perfil(**item)


def _carregar_perfis_iniciais() -> list[dict]:
    """Lê os perfis que acompanham o aplicativo."""
    configuracao = carregar_configuracao_inicial()

    resultado = []
    for entrada in configuracao.get("perfis", []):
        try:
            perfil = _perfil_de_dict(entrada["perfil"])
            recursos = entrada.get("modelos") or [entrada.get("modelo", "")]
            for indice, recurso in enumerate(recursos):
                if recurso and indice < len(perfil.formularios):
                    perfil.formularios[indice].recurso = recurso
            resultado.append({
                "perfil": perfil,
                "identificadores_anteriores": entrada.get("identificadores_anteriores", []),
                "nomes_anteriores": entrada.get("nomes_anteriores", []),
                "substituir_sem_identificador": bool(entrada.get("identificadores_anteriores")),
                "correcoes": entrada.get("correcoes", []),
            })
        except (KeyError, TypeError):
            continue
    return resultado


def carregar_perfis(forcar_disco: bool = False) -> list[Perfil]:
    """Carrega todos os perfis do disco (ou do cache em memória). Sempre inclui os perfis padrão."""
    global _perfis_cache

    if _perfis_cache is not None and not forcar_disco:
        return [
            Perfil(
                nome=p.nome,
                formularios=[FormularioModelo(f.nome, f.caminho, f.geracao, copy.deepcopy(f.mapeamento), f.identificador, f.recurso) for f in p.formularios],
                documentos_extras=[DocumentoExtra(d.rotulo, d.nome_padrao) for d in p.documentos_extras],
                campos_entrada=[
                    CampoEntrada(
                        id=c.id, rotulo=c.rotulo, tipo=c.tipo, obrigatorio=c.obrigatorio,
                        placeholder=c.placeholder, escopo=c.escopo, opcoes=list(c.opcoes),
                        valor_padrao=c.valor_padrao, icone=c.icone, aba=c.aba,
                        ajuda=c.ajuda, minimo=c.minimo, maximo=c.maximo,
                        visivel_quando=[dict(condicao) for condicao in c.visivel_quando],
                        limpar_quando_oculto=c.limpar_quando_oculto,
                        calculo=c.calculo,
                        ate_participante=c.ate_participante,
                    )
                    for c in p.campos_entrada
                ],
                formato_saida=p.formato_saida,
                modo_fluxo=p.modo_fluxo,
                max_participantes=p.max_participantes,
                identificador=p.identificador,
                ordem=p.ordem,
                usar_paginacao=p.usar_paginacao,
                correcoes_aplicadas=list(p.correcoes_aplicadas),
                agrupamento_paginas=dict(p.agrupamento_paginas),
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
                # Campo antigo, mantido apenas para aceitar configurações já salvas.
                item.pop("schema", None)
                campos_definidos = "campos_entrada" in item
                documentos_definidos = "documentos_extras" in item
                maximo_definido = "max_participantes" in item
                if "formularios" in item:
                    item["formularios"] = [
                        FormularioModelo(
                            nome=fm["nome"],
                            caminho=fm.get("caminho", ""),
                            geracao=fm.get("geracao", "por_participante"),
                            mapeamento=fm.get("mapeamento", {}),
                            identificador=fm.get("identificador", ""),
                            recurso=fm.get("recurso", ""),
                        )
                        for fm in item["formularios"]
                    ]
                else:
                    item["formularios"] = []

                item["documentos_extras"] = [
                    DocumentoExtra(**documento) for documento in item.get("documentos_extras", [])
                ]

                if "campos_entrada" in item:
                    item["campos_entrada"] = [CampoEntrada(**c) for c in item["campos_entrada"]]
                else:
                    item["campos_entrada"] = []

                if "max_participantes" not in item:
                    item["max_participantes"] = 4
                        
                paginacao_definida = "usar_paginacao" in item
                perfil_carregado = Perfil(**item)
                setattr(perfil_carregado, "_paginacao_definida", paginacao_definida)
                setattr(perfil_carregado, "_campos_definidos", campos_definidos)
                setattr(perfil_carregado, "_documentos_definidos", documentos_definidos)
                setattr(perfil_carregado, "_maximo_definido", maximo_definido)
                perfis.append(perfil_carregado)
        except json.JSONDecodeError:
            guardar_copia_corrompida(caminho)
            perfis = []
        except (OSError, TypeError):
            perfis = []

    # Inclui os perfis entregues com o aplicativo sem apagar alterações do usuário.
    for entrada in _carregar_perfis_iniciais():
        inicial = entrada["perfil"]
        ids_anteriores = set(entrada["identificadores_anteriores"])
        nomes_aceitos = {inicial.nome, *entrada["nomes_anteriores"]}
        existente = next(
            (
                perfil for perfil in perfis
                if perfil.identificador == inicial.identificador
                or perfil.identificador in ids_anteriores
                or perfil.nome in nomes_aceitos
            ),
            None,
        )
        if existente is None:
            perfis.append(inicial)
            continue
        if not existente.identificador and entrada["substituir_sem_identificador"]:
            indice = perfis.index(existente)
            perfis[indice] = inicial
            continue
        existente.identificador = inicial.identificador
        if existente.nome in entrada["nomes_anteriores"]:
            existente.nome = inicial.nome
        existente.ordem = inicial.ordem
        if not getattr(existente, "_campos_definidos", True):
            existente.campos_entrada = copy.deepcopy(inicial.campos_entrada)
        if not getattr(existente, "_documentos_definidos", True):
            existente.documentos_extras = copy.deepcopy(inicial.documentos_extras)
        if not getattr(existente, "_maximo_definido", True):
            existente.max_participantes = inicial.max_participantes
        if not getattr(existente, "_paginacao_definida", True):
            existente.usar_paginacao = inicial.usar_paginacao
        if inicial.agrupamento_paginas and not existente.agrupamento_paginas:
            existente.agrupamento_paginas = copy.deepcopy(inicial.agrupamento_paginas)
        if not existente.formularios:
            existente.formularios = copy.deepcopy(inicial.formularios)
        for indice, formulario_inicial in enumerate(inicial.formularios):
            if indice < len(existente.formularios):
                formulario_existente = existente.formularios[indice]
                formulario_existente.identificador = formulario_inicial.identificador
                if not formulario_existente.recurso:
                    formulario_existente.recurso = formulario_inicial.recurso

                # Migra somente a regra oficial antiga do DAMP. Mapeamentos
                # personalizados pelo usuário permanecem intactos.
                regra_data_legada = {
                    "origem": "participante.data_assinatura",
                    "formato": "DATA_EXTENSO",
                }
                if (
                    inicial.identificador == "inicial_01"
                    and formulario_existente.mapeamento.get("data_assinatura_titular") == regra_data_legada
                ):
                    formulario_existente.mapeamento.pop("data_assinatura_titular", None)
                    for campo_data in (
                        "data_assinatura_dia",
                        "data_assinatura_mes",
                        "data_assinatura_ano",
                    ):
                        formulario_existente.mapeamento[campo_data] = copy.deepcopy(
                            formulario_inicial.mapeamento[campo_data]
                        )

        for correcao in entrada.get("correcoes", []):
            chave = str(correcao.get("chave", "")).strip()
            if not chave or chave in existente.correcoes_aplicadas:
                continue
            ajustes = correcao.get("campos", {}) or {}
            for campo in existente.campos_entrada:
                for atributo, valor in (ajustes.get(campo.id, {}) or {}).items():
                    if hasattr(campo, atributo):
                        setattr(campo, atributo, copy.deepcopy(valor))
            existente.correcoes_aplicadas.append(chave)

    perfis.sort(key=lambda perfil: (getattr(perfil, "ordem", 100), perfil.nome.casefold()))
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


def salvar_perfis(perfis: list[Perfil]) -> None:
    """Salva todos os perfis no disco e atualiza o cache imediatamente."""
    global _perfis_cache

    validar_perfis(perfis)
    caminho = _caminho_perfis()
    dados = [asdict(p) for p in perfis]
    salvar_json(caminho, dados)

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


def validar_perfis(perfis: list[Perfil]) -> None:
    """Impede que uma configuração incompleta seja gravada e usada na geração."""
    nomes: set[str] = set()
    identificadores: set[str] = set()
    for perfil in perfis:
        nome = perfil.nome.strip()
        if not nome or nome in nomes:
            raise ValueError("Cada perfil precisa ter um nome único.")
        nomes.add(nome)
        if perfil.identificador:
            if perfil.identificador in identificadores:
                raise ValueError("Cada perfil precisa ter um identificador único.")
            identificadores.add(perfil.identificador)
        campos: set[str] = set()
        for campo in perfil.campos_entrada:
            if not campo.id or campo.id in campos:
                raise ValueError(f"Os campos do perfil '{perfil.nome}' precisam ter identificadores únicos.")
            campos.add(campo.id)
            if campo.tipo not in TIPOS_CAMPO_ENTRADA:
                raise ValueError(f"O tipo do campo '{campo.rotulo}' não é suportado.")
            if campo.tipo == "SELECAO" and not campo.opcoes:
                raise ValueError(f"O campo de seleção '{campo.rotulo}' precisa de opções.")
        for formulario in perfil.formularios:
            if formulario.geracao not in ("por_participante", "por_processo", "unico"):
                raise ValueError(f"A forma de geração de '{formulario.nome}' não é suportada.")
            if not isinstance(formulario.mapeamento, dict):
                raise ValueError(f"O mapeamento de '{formulario.nome}' precisa ser uma lista de campos válida.")


def problemas_estruturais(
    perfil: Perfil, nomes_existentes: tuple[str, ...] = ()
) -> list[str]:
    """Lista todos os problemas estruturais de uma vez, com contexto por campo.

    `nomes_existentes` traz os nomes dos demais perfis (para apontar
    duplicidade sem precisar salvar antes).
    """
    problemas: list[str] = []
    nome = (perfil.nome or "").strip()
    if not nome:
        problemas.append("O perfil está sem nome.")
    elif nome in nomes_existentes:
        problemas.append(f"Já existe outro perfil chamado '{nome}'.")
    vistos_id: set[str] = set()
    for campo in perfil.campos_entrada:
        rotulo = campo.rotulo or campo.id or "(sem nome)"
        if not campo.id:
            problemas.append(f"Campo '{rotulo}' está sem identificador interno.")
            continue
        if campo.id in vistos_id:
            problemas.append(f"Identificador '{campo.id}' repetido ('{rotulo}').")
        vistos_id.add(campo.id)
        if campo.tipo not in TIPOS_CAMPO_ENTRADA:
            problemas.append(
                f"Campo '{rotulo}': tipo '{campo.tipo}' não suportado "
                f"(use: {', '.join(TIPOS_CAMPO_ENTRADA)})."
            )
        if campo.tipo == "SELECAO" and not campo.opcoes:
            problemas.append(f"Campo '{rotulo}': lista de opções vazia.")
    for formulario in perfil.formularios:
        if formulario.geracao not in ("por_participante", "por_processo", "unico"):
            problemas.append(
                f"Formulário '{formulario.nome}': forma de geração inválida."
            )
        if not isinstance(formulario.mapeamento, dict):
            problemas.append(
                f"Formulário '{formulario.nome}': mapeamento inválido."
            )
    return problemas


def adicionar_perfil(perfil: Perfil) -> None:
    """Adiciona um novo perfil. Erro se já existir um com o mesmo nome."""
    perfis = carregar_perfis()
    if any(p.nome == perfil.nome for p in perfis):
        raise ValueError(f"Já existe um perfil com o nome '{perfil.nome}'.")
    if not perfil.identificador:
        perfil.identificador = uuid.uuid4().hex
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
            mapeamento=copy.deepcopy(f.mapeamento),
            identificador=f.identificador,
            recurso=f.recurso,
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
            ajuda=c.ajuda,
            minimo=c.minimo,
            maximo=c.maximo,
            visivel_quando=[dict(condicao) for condicao in c.visivel_quando],
            limpar_quando_oculto=c.limpar_quando_oculto,
            calculo=c.calculo,
            ate_participante=c.ate_participante,
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
        modo_fluxo=origem.modo_fluxo,
        max_participantes=origem.max_participantes,
        identificador=uuid.uuid4().hex,
        ordem=100,
        usar_paginacao=origem.usar_paginacao,
        correcoes_aplicadas=list(origem.correcoes_aplicadas),
        agrupamento_paginas=dict(origem.agrupamento_paginas),
    )
    perfis.append(novo_perfil)
    salvar_perfis(perfis)
    return novo_perfil

