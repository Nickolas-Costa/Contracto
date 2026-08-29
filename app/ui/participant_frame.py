"""
Frame reutilizável que representa os campos de um único participante na interface,
com suporte a campos dinâmicos e modulares configurados por perfil.
"""

from typing import Callable, Optional
import customtkinter as ctk

from models.participant import Participant
from ui.campo_dinamico_widget import CampoDinamicoWidget
from ui.theme import *
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.profile_manager import CampoEntrada


class ParticipantFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        indice: int,
        principal: bool = False,
        on_remover: Optional[Callable[["ParticipantFrame"], None]] = None,
        campos_customizados: Optional[list[CampoEntrada]] = None,
        on_open_datepicker: Optional[Callable[[ctk.CTkEntry], None]] = None,
        local_padrao: str = "CAMOCIM-CE",
        **kwargs,
    ):
        kwargs.pop("local_padrao", None)
        super().__init__(
            master, 
            corner_radius=RADIUS_CARD, 
            fg_color=COLOR_SURFACE, 
            border_width=1, 
            border_color=COLOR_BORDER,
            **kwargs
        )

        self.indice = indice
        self.principal = principal
        self.on_remover = on_remover
        self.campos_customizados = campos_customizados or []
        self.on_open_datepicker = on_open_datepicker
        self._local_padrao = local_padrao
        self.widgets_dinamicos: dict[str, CampoDinamicoWidget] = {}

        self.grid_columnconfigure(1, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self,
            text=f" {self._titulo(indice)}",
            image=get_icon("person", (18, 18)),
            compound="left",
            font=get_font(FONT_SIZE_H3, "bold"),
            text_color=get_color_primary_text(),
        )
        self.label_titulo.grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        if on_remover is not None:
            botao_remover = ctk.CTkButton(
                self,
                text="",
                image=get_icon("trash", (16, 16)),
                width=36,
                height=28,
                fg_color=COLOR_BORDER,
                text_color=COLOR_TEXT,
                hover_color=COLOR_TEXT_DISABLED,
                corner_radius=RADIUS_BUTTON,
                command=lambda: self.on_remover(self),
            )
            botao_remover.grid(row=0, column=2, padx=SPACING_MEDIUM, pady=(SPACING_SMALL, 0), sticky="e")

        linha = 1
        self.entry_nome = self._criar_campo_padrao("Nome Completo", linha, tipo="nome")
        linha += 1
        self.entry_cpf = self._criar_campo_padrao("CPF", linha, tipo="cpf")
        linha += 1

        self.entry_endereco: ctk.CTkEntry | None = None

        # Renderização modular de campos adicionais
        if self.campos_customizados:
            for campo in self.campos_customizados:
                if campo.id in ("nome_completo", "nome", "cpf"):
                    continue
                # Se não for o principal e for campo de endereço padrão, só exibe se configurado
                if campo.id == "endereco" and not principal:
                    continue

                widget_campo = CampoDinamicoWidget(
                    self,
                    campo=campo,
                    on_open_datepicker=self.on_open_datepicker,
                )
                widget_campo.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
                self.widgets_dinamicos[campo.id] = widget_campo
                if campo.id == "endereco" and hasattr(widget_campo, "entry"):
                    self.entry_endereco = widget_campo.entry
                linha += 1
        elif principal:
            # Fallback padrão: Endereço para o principal
            self.entry_endereco = self._criar_campo_padrao("Endereço", linha, tipo="endereco")
            linha += 1

        # Pequeno respiro na última linha do frame
        ctk.CTkLabel(self, text="", height=2).grid(row=linha, column=0, pady=(0, SPACING_SMALL))

    def _titulo(self, indice: int) -> str:
        return f"Participante {indice}" + ("  (Principal)" if self.principal else "")

    def _criar_campo_padrao(self, rotulo: str, linha: int, tipo: str) -> ctk.CTkEntry:
        icone_nome = "attribution" if tipo == "nome" else ("document" if tipo == "cpf" else "location")
        placeholder = (
            "Ex: João da Silva" if tipo == "nome"
            else ("123.456.789-10" if tipo == "cpf"
                  else "Ex: Rua das Flores, 123 - Centro, Camocim - CE")
        )
        ctk.CTkLabel(
            self,
            text=f" {rotulo}",
            image=get_icon(icone_nome, (16, 16)),
            compound="left",
            anchor="w",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT,
        ).grid(
            row=linha, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w"
        )
        entry = ctk.CTkEntry(self, placeholder_text=placeholder, corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        entry.grid(row=linha, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        
        entry.bind("<KeyRelease>", lambda e: self._validar_campo_especifico(entry, tipo))
        entry.bind("<FocusOut>", lambda e: self._validar_campo_especifico(entry, tipo))
            
        return entry

    def _validar_campo_especifico(self, entry: ctk.CTkEntry, tipo: str) -> bool:
        val = entry.get().strip()
        is_valid = True

        if tipo == "nome":
            is_valid = bool(val)
        elif tipo == "cpf":
            # Auto-formatação ao digitar
            apenas_nums = "".join(c for c in val if c.isdigit())
            if len(apenas_nums) == 11 and ("." not in val or "-" not in val):
                fmt = formatar_cpf(apenas_nums)
                if fmt != val:
                    entry.delete(0, "end")
                    entry.insert(0, fmt)
                    val = fmt
            is_valid = bool(val) and validar_cpf(val)
        elif tipo == "endereco":
            is_valid = bool(val)

        if is_valid:
            entry.configure(border_color=COLOR_BORDER)
        else:
            entry.configure(border_color=COLOR_BORDER_ERROR)

        return is_valid

    def validar_campos(self) -> list[str]:
        """Valida todos os campos deste frame e retorna lista de erros."""
        erros = []
        prefixo = f"Participante {self.indice}" + (" (Principal)" if self.principal else "")
        
        nome_val = self.entry_nome.get().strip()
        if not nome_val:
            self.entry_nome.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: Nome Completo é obrigatório.")
        else:
            self.entry_nome.configure(border_color=COLOR_BORDER)

        cpf_val = self.entry_cpf.get().strip()
        if not cpf_val:
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: CPF é obrigatório.")
        elif not validar_cpf(cpf_val):
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: O CPF informado é inválido.")
        else:
            self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            end_val = self.entry_endereco.get().strip()
            if not end_val:
                self.entry_endereco.configure(border_color=COLOR_BORDER_ERROR)
                erros.append(f"{prefixo}: Endereço Completo é obrigatório.")
            else:
                self.entry_endereco.configure(border_color=COLOR_BORDER)

        # Validação dos campos modulares adicionais
        for campo_id, widget in self.widgets_dinamicos.items():
            erros_widget = widget.validar(prefixo=prefixo)
            erros.extend(erros_widget)

        return erros

    def limpar_campos(self) -> None:
        """Limpa todos os campos deste quadro."""
        self.entry_nome.delete(0, "end")
        self.entry_nome.configure(border_color=COLOR_BORDER)

        self.entry_cpf.delete(0, "end")
        self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            self.entry_endereco.delete(0, "end")
            self.entry_endereco.configure(border_color=COLOR_BORDER)

        for widget in self.widgets_dinamicos.values():
            widget.limpar()

    def atualizar_indice(self, indice: int) -> None:
        self.indice = indice
        self.label_titulo.configure(text=self._titulo(indice))

    def atualizar_cores(self) -> None:
        """Atualiza as cores dinâmicas deste frame."""
        self.label_titulo.configure(text_color=get_color_primary_text())

    def piscar_destaque(self) -> None:
        """Faz o quadro 'piscar' visualmente ao ser adicionado."""
        try:
            self.configure(
                border_color=get_color_primary(),
                border_width=2,
                fg_color=get_color_primary_light()
            )
            def _restaurar_fg():
                try:
                    self.configure(fg_color=COLOR_SURFACE)
                    self.after(250, _restaurar_border)
                except Exception:
                    pass

            def _restaurar_border():
                try:
                    self.configure(border_color=COLOR_BORDER, border_width=1)
                except Exception:
                    pass

            self.after(200, _restaurar_fg)
        except Exception:
            pass

    def obter_participante(self) -> Participant:
        p = Participant(
            nome_completo=self.entry_nome.get().strip(),
            cpf=self.entry_cpf.get().strip(),
        )
        if self.entry_endereco is not None:
            p.endereco = self.entry_endereco.get().strip()

        for campo_id, widget in self.widgets_dinamicos.items():
            val = widget.obter_valor()
            p.definir_campo(campo_id, val)

        return p
