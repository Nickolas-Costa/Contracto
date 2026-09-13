"""
Modelo de dados que representa um participante do processo.

Desenho (POO aplicada):
- **Encapsulamento:** fonte única de verdade é `campos_dinamicos`;
  `endereco`, `data_assinatura` e `local_assinatura` são conveniências
  (propriedades) sobre o dicionário, não campos duplicados. Nenhum nome
  de campo aparece em `if/elif` aqui: o perfil define o esquema.
- **Herança:** especializações futuras herdam desta classe e do seu
  contrato (`obter_campo`/`definir_campo`), sem tocar os fluxos.
- **Polimorfismo:** validação e normalização variam por *tipo de campo*
  (ver `services/form_validation.py`), nunca por ramificação de nomes
  neste modelo.

Compatibilidade: construtor aceita as chaves legadas (`endereco`,
`data_assinatura`, `local_assinatura` e extras), absorvidas no dicionário.
"""

from dataclasses import dataclass, field
from typing import Any

# Aliases históricos resolvidos para o campo canônico.
_ALIASES = {"nome": "nome_completo"}

# Campos que todo perfil assume existir (identidade do participante).
_CAMPOS_NUCLEO = ("nome_completo", "cpf")

# Valor assumido quando o perfil não define local (preserva comportamento).
_LOCAL_PADRAO = "CAMOCIM-CE"


@dataclass(init=False)
class Participant:
    """Participante: identidade fixa (nome, CPF) + demais dados por perfil."""

    nome_completo: str = ""
    cpf: str = ""
    campos_dinamicos: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        nome_completo: str = "",
        cpf: str = "",
        campos_dinamicos: dict[str, Any] | None = None,
        **legado: Any,
    ) -> None:
        self.nome_completo = nome_completo
        self.cpf = cpf
        self.campos_dinamicos = dict(campos_dinamicos or {})
        for chave, valor in legado.items():
            self.definir_campo(chave, valor)
        if "local_assinatura" not in self.campos_dinamicos:
            self.campos_dinamicos["local_assinatura"] = _LOCAL_PADRAO

    @staticmethod
    def _canonico(campo_id: str) -> str:
        """Resolve aliases históricos para o identificador canônico."""
        return _ALIASES.get(campo_id, campo_id)

    def obter_campo(self, campo_id: str, padrao: Any = "") -> Any:
        """Obtém qualquer campo: núcleo por atributo, resto pelo dicionário."""
        campo_id = self._canonico(campo_id)
        if campo_id == "nome_completo":
            return self.nome_completo
        if campo_id == "cpf":
            return self.cpf
        return self.campos_dinamicos.get(campo_id, padrao)

    def definir_campo(self, campo_id: str, valor: Any) -> None:
        """Define qualquer campo, sem ramificação por nome."""
        campo_id = self._canonico(campo_id)
        if campo_id == "nome_completo":
            self.nome_completo = str(valor)
        elif campo_id == "cpf":
            self.cpf = str(valor)
        else:
            self.campos_dinamicos[campo_id] = valor

    @property
    def endereco(self) -> str:
        """Conveniência sobre o dicionário (perfil define se existe)."""
        return str(self.campos_dinamicos.get("endereco", ""))

    @endereco.setter
    def endereco(self, valor: Any) -> None:
        self.campos_dinamicos["endereco"] = str(valor)

    @property
    def data_assinatura(self) -> str:
        """Conveniência sobre o dicionário (perfil define se existe)."""
        return str(self.campos_dinamicos.get("data_assinatura", ""))

    @data_assinatura.setter
    def data_assinatura(self, valor: Any) -> None:
        self.campos_dinamicos["data_assinatura"] = str(valor)

    @property
    def local_assinatura(self) -> str:
        """Conveniência sobre o dicionário (perfil define se existe)."""
        return str(self.campos_dinamicos.get("local_assinatura", _LOCAL_PADRAO))

    @local_assinatura.setter
    def local_assinatura(self, valor: Any) -> None:
        self.campos_dinamicos["local_assinatura"] = str(valor)

    def copiar_dados_compartilhados(
        self, principal: "Participant", campos: list | None = None
    ) -> None:
        """Herda do principal só o que o perfil marca como compartilhado.

        Com `campos` (lista de `CampoEntrada` do perfil): copia os ids de
        escopo `"global"`. Sem `campos`: comportamento legado (endereço,
        data, local + todos os dinâmicos), para chamadas antigas.
        """
        if campos is None:
            for chave in ("endereco", "data_assinatura", "local_assinatura"):
                if chave in principal.campos_dinamicos:
                    self.campos_dinamicos[chave] = principal.campos_dinamicos[chave]
            for chave, valor in principal.campos_dinamicos.items():
                self.campos_dinamicos[chave] = valor
            return
        for campo in campos:
            escopo = getattr(campo, "escopo", "participante")
            cid = getattr(campo, "id", "")
            if escopo == "global" and cid in principal.campos_dinamicos:
                self.campos_dinamicos[cid] = principal.campos_dinamicos[cid]
