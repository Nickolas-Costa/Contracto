"""
Frame reutilizável que representa a seção "Documentos para PDF/A" na interface.
"""

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from ui.theme import *

TIPOS_DOCUMENTOS = [
    ("Contrato", "CONTRATO"),
    ("Planilha de Evolução", "PLANILHA DE EVOLUCAO"),
    ("Protocolo da Planilha", "PROTOCOLO DA PLANILHA"),
    ("Aviso de Crédito", "AVISO DE CREDITO"),
    ("Origem de Recursos", "ORIGEM DE RECURSOS"),
]

class DocumentFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, 
            corner_radius=RADIUS_CARD, 
            fg_color=COLOR_SURFACE, 
            border_width=1, 
            border_color=COLOR_BORDER,
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)

        self._documentos: dict[str, Path | None] = {
            tipo_padrao: None for _, tipo_padrao in TIPOS_DOCUMENTOS
        }
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._icons: dict[str, ctk.CTkLabel] = {}

        self._construir_campos()

    def _construir_campos(self) -> None:
        for linha, (rotulo, tipo_padrao) in enumerate(TIPOS_DOCUMENTOS):
            # Status icon
            icon_label = ctk.CTkLabel(self, text="○", font=get_font(FONT_SIZE_H3), text_color=COLOR_TEXT_DISABLED, width=20)
            icon_label.grid(row=linha, column=0, padx=(SPACING_LARGE, 0), pady=SPACING_SMALL, sticky="e")
            self._icons[tipo_padrao] = icon_label

            ctk.CTkLabel(self, text=f"{rotulo}:", anchor="w", font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT).grid(
                row=linha, column=1, padx=(SPACING_SMALL, SPACING_SMALL), pady=SPACING_SMALL, sticky="w"
            )

            entry = ctk.CTkEntry(self, placeholder_text="Nenhum arquivo selecionado", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
            entry.grid(row=linha, column=2, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
            entry.configure(state="disabled")
            self._entries[tipo_padrao] = entry

            btn = ctk.CTkButton(
                self,
                text="Selecionar",
                width=80,
                corner_radius=RADIUS_BUTTON,
                fg_color=COLOR_SURFACE_VARIANT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                command=lambda tp=tipo_padrao, rt=rotulo: self._selecionar_documento(tp, rt),
            )
            btn.grid(row=linha, column=3, padx=(SPACING_SMALL, SPACING_LARGE), pady=SPACING_SMALL)

        ctk.CTkLabel(self, text="", height=2).grid(row=len(TIPOS_DOCUMENTOS), column=0, pady=(0, SPACING_SMALL))

    def _selecionar_documento(self, tipo_padrao: str, rotulo: str) -> None:
        caminho_str = filedialog.askopenfilename(
            title=f"Selecionar {rotulo}",
            filetypes=[("Arquivos PDF e RTF", "*.pdf;*.rtf"), ("Todos os arquivos", "*.*")],
        )
        if caminho_str:
            caminho = Path(caminho_str)
            self._documentos[tipo_padrao] = caminho
            self._atualizar_entry(self._entries[tipo_padrao], caminho.name)
            self._atualizar_icone(tipo_padrao, True)

    def _atualizar_icone(self, tipo_padrao: str, selecionado: bool):
        icon = self._icons[tipo_padrao]
        if selecionado:
            icon.configure(text="●", text_color=COLOR_PRIMARY)
        else:
            icon.configure(text="○", text_color=COLOR_TEXT_DISABLED)

    @staticmethod
    def _atualizar_entry(entry: ctk.CTkEntry, texto: str) -> None:
        entry.configure(state="normal", text_color=COLOR_TEXT)
        entry.delete(0, "end")
        entry.insert(0, texto)
        entry.configure(state="disabled")

    def obter_documentos_selecionados(self) -> dict[str, Path]:
        return {
            tipo: caminho
            for tipo, caminho in self._documentos.items()
            if caminho is not None
        }

    def tem_documentos(self) -> bool:
        return any(caminho is not None for caminho in self._documentos.values())

    def limpar(self) -> None:
        for tipo_padrao in self._documentos:
            self._documentos[tipo_padrao] = None
            entry = self._entries[tipo_padrao]
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.configure(state="disabled")
            self._atualizar_icone(tipo_padrao, False)
