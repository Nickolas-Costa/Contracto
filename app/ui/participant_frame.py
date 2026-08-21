"""
Frame reutilizável que representa os campos de um único participante na interface.
"""

from typing import Callable, Optional
import customtkinter as ctk

from models.participant import Participant
from ui.theme import *
from utils.cpf_validator import validar_cpf

class ParticipantFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        indice: int,
        principal: bool = False,
        on_remover: Optional[Callable[["ParticipantFrame"], None]] = None,
        local_padrao: str = "CAMOCIM-CE",
        **kwargs,
    ):
        # Remove local_padrao from kwargs if passed through
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
        self._local_padrao = local_padrao

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
                width=28,
                height=28,
                fg_color="transparent",
                text_color=COLOR_TEXT_SECONDARY,
                hover_color=COLOR_SURFACE_VARIANT,
                corner_radius=RADIUS_BUTTON,
                command=lambda: self.on_remover(self),
            )
            botao_remover.grid(row=0, column=2, padx=SPACING_MEDIUM, pady=(SPACING_SMALL, 0), sticky="e")

        linha = 1
        self.entry_nome = self._criar_campo("Nome Completo", linha, tipo="nome")
        linha += 1
        self.entry_cpf = self._criar_campo("CPF", linha, tipo="cpf")
        linha += 1

        self.entry_endereco: ctk.CTkEntry | None = None
        
        if principal:
            self.entry_endereco = self._criar_campo("Endereço Completo", linha, tipo="endereco")
            linha += 1

        # Pequeno respiro na última linha do frame
        ctk.CTkLabel(self, text="", height=2).grid(row=linha, column=0, pady=(0, SPACING_SMALL))

    def _titulo(self, indice: int) -> str:
        return f"Participante {indice}" + ("  (Principal)" if self.principal else "")

    def _criar_campo(self, rotulo: str, linha: int, tipo: str) -> ctk.CTkEntry:
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
        
        # Real-time binding on edit and focus out
        entry.bind("<KeyRelease>", lambda e: self._validar_campo_especifico(entry, tipo))
        entry.bind("<FocusOut>", lambda e: self._validar_campo_especifico(entry, tipo))
            
        return entry

    def _validar_campo_especifico(self, entry: ctk.CTkEntry, tipo: str) -> bool:
        val = entry.get().strip()
        is_valid = True

        if tipo == "nome":
            is_valid = bool(val)
        elif tipo == "cpf":
            is_valid = bool(val) and validar_cpf(val)
        elif tipo == "endereco":
            is_valid = bool(val)

        if is_valid:
            entry.configure(border_color=COLOR_BORDER)
        else:
            entry.configure(border_color=COLOR_BORDER_ERROR)

        return is_valid

    def validar_campos(self) -> list[str]:
        """Valida todos os campos deste frame, atualiza as bordas visualmente e retorna lista de erros."""
        erros = []
        
        nome_val = self.entry_nome.get().strip()
        if not nome_val:
            self.entry_nome.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"Participante {self.indice}: Nome Completo é obrigatório.")
        else:
            self.entry_nome.configure(border_color=COLOR_BORDER)

        cpf_val = self.entry_cpf.get().strip()
        if not cpf_val:
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"Participante {self.indice}: CPF é obrigatório.")
        elif not validar_cpf(cpf_val):
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"Participante {self.indice}: O CPF informado é inválido.")
        else:
            self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            end_val = self.entry_endereco.get().strip()
            if not end_val:
                self.entry_endereco.configure(border_color=COLOR_BORDER_ERROR)
                erros.append(f"Participante {self.indice} (Principal): Endereço Completo é obrigatório.")
            else:
                self.entry_endereco.configure(border_color=COLOR_BORDER)

        return erros

    def limpar_campos(self) -> None:
        """Limpa todos os campos deste quadro e redefine as bordas para o estilo padrão neutro."""
        self.entry_nome.delete(0, "end")
        self.entry_nome.configure(border_color=COLOR_BORDER)

        self.entry_cpf.delete(0, "end")
        self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            self.entry_endereco.delete(0, "end")
            self.entry_endereco.configure(border_color=COLOR_BORDER)

    def atualizar_indice(self, indice: int) -> None:
        self.indice = indice
        self.label_titulo.configure(text=self._titulo(indice))

    def atualizar_cores(self) -> None:
        """Atualiza as cores dinâmicas deste frame."""
        self.label_titulo.configure(text_color=get_color_primary_text())

    def piscar_destaque(self) -> None:
        """Faz o quadro 'piscar' visualmente ao ser adicionado para chamar atenção do usuário."""
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
        return Participant(
            nome_completo=self.entry_nome.get().strip(),
            cpf=self.entry_cpf.get().strip(),
            endereco=self.entry_endereco.get().strip() if self.entry_endereco else "",
            data_assinatura="",
            local_assinatura="",
        )
