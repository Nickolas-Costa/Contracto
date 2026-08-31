"""
Modal de sucesso e conclusão de geração de formulários no Contracto.
Apresenta o status positivo, os arquivos gerados e botões diretos para abrir o PDF ou a pasta.
"""

import os
from pathlib import Path
import customtkinter as ctk
from ui import theme


class SuccessModal:
    """Modal de sucesso com overlay translúcido e ações rápidas (abrir arquivo / pasta)."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        titulo: str,
        subtitulo: str,
        arquivos_gerados: list[Path | str],
        pasta_destino: str | Path,
        on_close=None,
    ):
        if SuccessModal._instancia_ativa is not None:
            try:
                SuccessModal._instancia_ativa.dismiss()
            except Exception:
                pass
        SuccessModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        self.arquivos_gerados = [Path(a) for a in arquivos_gerados]
        self.pasta_destino = Path(pasta_destino)
        self.on_close_cb = on_close

        w = 580
        h = min(360 + len(self.arquivos_gerados) * 36, 560)

        # 1. Overlay escuro translúcido
        self.overlay = ctk.CTkToplevel(root)
        # 2. Cartão de sucesso
        self.card = ctk.CTkToplevel(root)

        theme.configurar_janela_modal(root, self.card, self.overlay, w, h)

        self.overlay.bind("<Button-1>", lambda e: self.dismiss())
        self.card.bind("<Escape>", lambda e: self.dismiss())

        self.frame = ctk.CTkFrame(
            self.card,
            fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # Header (Ícone verde de Sucesso + Títulos)
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            header,
            width=42,
            height=42,
            corner_radius=10,
            fg_color=("#DCFCE7", "#064E3B"),
            border_width=1,
            border_color=("#22C55E", "#16A34A"),
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(
            icon_box,
            text="",
            image=theme.get_icon("success", (24, 24)),
        ).pack(expand=True)

        info = ctk.CTkFrame(header, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            info,
            text=titulo,
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=subtitulo,
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # Lista de arquivos gerados
        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent", label_text="")
        scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(5, 10))
        scroll.grid_columnconfigure(0, weight=1)

        for i, arq in enumerate(self.arquivos_gerados):
            ef = ctk.CTkFrame(scroll, fg_color=theme.COLOR_SURFACE_VARIANT, corner_radius=8)
            ef.grid(row=i, column=0, sticky="ew", pady=4)
            ef.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                ef,
                text="",
                image=theme.get_icon("document", (18, 18)),
            ).grid(row=0, column=0, padx=(10, 8), pady=8)

            ctk.CTkLabel(
                ef,
                text=arq.name,
                font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.COLOR_TEXT,
                wraplength=380,
                justify="left",
            ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=8)

            if arq.exists():
                ctk.CTkButton(
                    ef,
                    text="Abrir PDF",
                    width=85,
                    height=28,
                    corner_radius=theme.RADIUS_BUTTON,
                    fg_color=theme.get_color_primary(),
                    text_color="#FFFFFF",
                    hover_color=theme.get_color_primary_hover(),
                    font=theme.get_font(theme.FONT_SIZE_CAPTION, "bold"),
                    command=lambda p=arq: self._abrir_arquivo(p),
                ).grid(row=0, column=2, padx=(0, 10), pady=8)

        # Footer (Ações: Abrir Pasta e Fechar)
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer,
            text=" 📁 Abrir Pasta de Destino",
            font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.COLOR_SURFACE_VARIANT,
            text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_BORDER,
            border_width=1,
            border_color=theme.COLOR_BORDER,
            height=42,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._abrir_pasta_destino,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            footer,
            text=" Concluir",
            font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=42,
            corner_radius=theme.RADIUS_BUTTON,
            command=self.dismiss,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _abrir_arquivo(self, caminho: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(str(caminho))
            else:
                import subprocess
                subprocess.run(["xdg-open", str(caminho)], check=False)
        except Exception:
            pass

    def _abrir_pasta_destino(self) -> None:
        try:
            pasta = self.pasta_destino
            if os.name == "nt":
                os.startfile(str(pasta))
            else:
                import subprocess
                subprocess.run(["xdg-open", str(pasta)], check=False)
        except Exception:
            pass

    def dismiss(self) -> None:
        if SuccessModal._instancia_ativa is self:
            SuccessModal._instancia_ativa = None
        try:
            self.overlay.destroy()
        except Exception:
            pass
        try:
            self.card.destroy()
        except Exception:
            pass
        if self.on_close_cb:
            try:
                self.on_close_cb()
            except Exception:
                pass
