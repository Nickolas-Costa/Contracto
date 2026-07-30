"""
Frame reutilizável que representa os campos de um único participante na interface.
"""

from typing import Callable, Optional
import customtkinter as ctk

from models.participant import Participant
from ui.theme import *

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

        self.principal = principal
        self.on_remover = on_remover
        self._local_padrao = local_padrao

        self.grid_columnconfigure(1, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self, text=self._titulo(indice), font=get_font(FONT_SIZE_H3, "bold"), text_color=get_color_primary()
        )
        self.label_titulo.grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        if on_remover is not None:
            botao_remover = ctk.CTkButton(
                self,
                text="✕",
                width=24,
                height=24,
                fg_color="transparent",
                text_color=COLOR_TEXT_SECONDARY,
                hover_color=COLOR_SURFACE_VARIANT,
                font=get_font(FONT_SIZE_BODY, "bold"),
                command=lambda: self.on_remover(self),
            )
            botao_remover.grid(row=0, column=2, padx=SPACING_MEDIUM, pady=(SPACING_SMALL, 0), sticky="e")

        linha = 1
        self.entry_nome = self._criar_campo("Nome Completo", linha, required=True)
        linha += 1
        self.entry_cpf = self._criar_campo("CPF", linha, required=True)
        linha += 1

        self.entry_endereco: ctk.CTkEntry | None = None
        self.entry_data: ctk.CTkEntry | None = None
        self.entry_local: ctk.CTkEntry | None = None
        
        if principal:
            self.entry_endereco = self._criar_campo("Endereço Completo", linha, required=True)
            linha += 1
            self.entry_data = self._criar_campo("Data da assinatura (DD/MM/AAAA)", linha, required=True)
            linha += 1
            self.entry_local = self._criar_campo("Local da assinatura", linha, required=True)
            self.entry_local.insert(0, self._local_padrao)
            linha += 1

        # Pequeno respiro na última linha do frame
        ctk.CTkLabel(self, text="", height=2).grid(row=linha, column=0, pady=(0, SPACING_SMALL))

    def _titulo(self, indice: int) -> str:
        return f"Participante {indice}" + ("  (Principal)" if self.principal else "")

    def _criar_campo(self, rotulo: str, linha: int, required: bool = False) -> ctk.CTkEntry:
        ctk.CTkLabel(self, text=rotulo, anchor="w", font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT).grid(
            row=linha, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w"
        )
        entry = ctk.CTkEntry(self, corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        entry.grid(row=linha, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        
        if required:
            entry.bind("<FocusOut>", lambda e: self._validar_campo(entry))
            
        return entry

    def _validar_campo(self, entry: ctk.CTkEntry):
        if not entry.get().strip():
            entry.configure(border_color=COLOR_BORDER_ERROR)
        else:
            entry.configure(border_color=COLOR_BORDER)

    def atualizar_indice(self, indice: int) -> None:
        self.label_titulo.configure(text=self._titulo(indice))

    def obter_participante(self) -> Participant:
        return Participant(
            nome_completo=self.entry_nome.get().strip(),
            cpf=self.entry_cpf.get().strip(),
            endereco=self.entry_endereco.get().strip() if self.entry_endereco else "",
            data_assinatura=self.entry_data.get().strip() if self.entry_data else "",
            local_assinatura=self.entry_local.get().strip() if self.entry_local else self._local_padrao,
        )
