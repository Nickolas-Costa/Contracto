"""
Frame reutilizável que representa a seção "Documentos para PDF/A" na interface.
"""

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from ui.theme import *
from utils.profile_manager import DocumentoExtra


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

        self._documentos: dict[str, Path | None] = {}
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._icons: dict[str, ctk.CTkLabel] = {}
        self._widgets_linha = [] # To keep track and destroy old rows

    def carregar_documentos(self, lista_extras: list[DocumentoExtra]) -> None:
        """Limpa a interface e recria os campos baseados na lista de documentos."""
        # Limpar widgets antigos
        for w in self._widgets_linha:
            w.destroy()
        self._widgets_linha.clear()
        
        self._documentos = {doc.nome_padrao: None for doc in lista_extras}
        self._entries.clear()
        self._icons.clear()

        for linha, doc in enumerate(lista_extras):
            # Status icon
            icon_label = ctk.CTkLabel(self, text="○", font=get_font(FONT_SIZE_H3), text_color=COLOR_TEXT_DISABLED, width=20)
            icon_label.grid(row=linha, column=0, padx=(SPACING_LARGE, 0), pady=SPACING_SMALL, sticky="e")
            self._icons[doc.nome_padrao] = icon_label
            self._widgets_linha.append(icon_label)

            lbl = ctk.CTkLabel(self, text=f"{doc.rotulo}:", anchor="w", font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT)
            lbl.grid(row=linha, column=1, padx=(SPACING_SMALL, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
            self._widgets_linha.append(lbl)

            entry = ctk.CTkEntry(self, placeholder_text="Nenhum arquivo selecionado", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
            entry.grid(row=linha, column=2, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
            entry.configure(state="disabled")
            self._entries[doc.nome_padrao] = entry
            self._widgets_linha.append(entry)

            btn = ctk.CTkButton(
                self,
                text="Selecionar",
                width=80,
                corner_radius=RADIUS_BUTTON,
                fg_color=COLOR_SURFACE_VARIANT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                command=lambda tp=doc.nome_padrao, rt=doc.rotulo: self._selecionar_documento(tp, rt),
            )
            btn.grid(row=linha, column=3, padx=(SPACING_SMALL, SPACING_LARGE), pady=SPACING_SMALL)
            self._widgets_linha.append(btn)

        padding_lbl = ctk.CTkLabel(self, text="", height=2)
        padding_lbl.grid(row=len(lista_extras), column=0, pady=(0, SPACING_SMALL))
        self._widgets_linha.append(padding_lbl)

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

    def obter_total_documentos(self) -> int:
        return len(self._documentos)

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
