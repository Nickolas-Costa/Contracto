"""Classe base dos modais (Herança): overlay, cartão, foco e teclado num lugar só.

Todo modal do aplicativo herda daqui em vez de remontar o esqueleto:

- instância única por tipo (abrir de novo fecha o anterior);
- overlay + cartão via `theme.configurar_janela_modal`;
- `Esc` fecha (opcional), clique no overlay fecha (opcional);
- foco inicial no cartão, trava de teclado opcional (`grab`) e
  devolução do foco a quem abriu ao fechar.

O conteúdo (cabeçalho, corpo, rodapé) continua em cada subclasse.
"""

import customtkinter as ctk
from ui import theme


class BaseModal:
    """Esqueleto comum. `largura`/`altura` em pixels (altura pode ser calculada)."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        largura: int,
        altura: int,
        *,
        fechar_no_overlay: bool = True,
        tecla_escape: bool = True,
        usar_grab: bool = True,
        ocultar_ao_perder_foco: bool = True,
    ):
        tipo = type(self)
        anterior = getattr(tipo, "_instancia_ativa", None)
        if anterior is not None:
            try:
                anterior.dismiss()
            except Exception:
                pass
        tipo._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        try:
            self._foco_anterior = root.focus_get()
        except Exception:
            self._foco_anterior = None

        self.overlay = ctk.CTkToplevel(root)
        self.card = ctk.CTkToplevel(root)

        theme.configurar_janela_modal(root, self.card, self.overlay, largura, altura)
        self.card._contracto_fixo = not ocultar_ao_perder_foco
        self.overlay._contracto_fixo = not ocultar_ao_perder_foco

        if fechar_no_overlay:
            self.overlay.bind("<Button-1>", lambda e: self.dismiss())
        if tecla_escape:
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

        try:
            self.card.focus_set()
        except Exception:
            pass
        if usar_grab:
            try:
                self.card.grab_set()
            except Exception:
                pass

    def montar_cabecalho(
        self,
        titulo: str,
        subtitulo: str | None = None,
        icone: str = "alert_circle",
        cores_caixa: tuple = ("#E0F2FE", "#082F49"),
        cores_borda: tuple = ("#38BDF8", "#0284C7"),
    ):
        """Cabeçalho padrão: caixa de ícone + título (+ subtítulo)."""
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            header, width=42, height=42, corner_radius=10,
            fg_color=cores_caixa, border_width=1, border_color=cores_borda,
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, text="", image=theme.get_icon(icone, (24, 24))).pack(expand=True)

        info = ctk.CTkFrame(header, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            info, text=titulo,
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w")
        if subtitulo:
            ctk.CTkLabel(
                info, text=subtitulo,
                font=theme.get_font(theme.FONT_SIZE_BODY),
                text_color=theme.COLOR_TEXT_SECONDARY,
            ).pack(anchor="w")
        return header

    def botao_primario(self, pai, texto: str, comando, **kwargs) -> ctk.CTkButton:
        """Botão de ação principal (fundo na cor de destaque)."""
        kwargs.setdefault("height", 38)
        botao = ctk.CTkButton(
            pai, text=texto,
            fg_color=theme.get_color_primary(), text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            corner_radius=theme.RADIUS_BUTTON,
            command=comando, **kwargs,
        )
        return botao

    def botao_secundario(self, pai, texto: str, comando, **kwargs) -> ctk.CTkButton:
        """Botão de ação secundária (fundo neutro com borda)."""
        kwargs.setdefault("height", 38)
        botao = ctk.CTkButton(
            pai, text=texto,
            fg_color=theme.COLOR_SURFACE, text_color=theme.COLOR_TEXT,
            border_width=1, border_color=theme.COLOR_BORDER,
            hover_color=theme.COLOR_SURFACE_VARIANT,
            corner_radius=theme.RADIUS_BUTTON,
            command=comando, **kwargs,
        )
        return botao

    def focar(self, widget) -> None:
        """Move o teclado para o widget informado (após exibição)."""
        try:
            widget.focus_set()
        except Exception:
            pass

    def dismiss(self) -> None:
        """Fecha overlay e cartão, devolve o foco e libera a instância."""
        tipo = type(self)
        if getattr(tipo, "_instancia_ativa", None) is self:
            tipo._instancia_ativa = None
        try:
            if hasattr(self, "card") and self.card and self.card.winfo_exists():
                try:
                    self.card.grab_release()
                except Exception:
                    pass
                self.card.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, "overlay") and self.overlay and self.overlay.winfo_exists():
                self.overlay.destroy()
        except Exception:
            pass
        try:
            self.master.update_idletasks()
        except Exception:
            pass
        try:
            if self._foco_anterior is not None and self._foco_anterior.winfo_exists():
                self._foco_anterior.focus_set()
        except Exception:
            pass
