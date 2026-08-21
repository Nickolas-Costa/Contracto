import customtkinter as ctk
from ui import theme


class AlertModal:
    """Modal moderno de alerta/erro com overlay escuro translúcido e cartão alinhado."""

    _instancia_ativa = None

    def __init__(self, master, titulo: str, subtitulo: str, erros: list[str], on_close=None):
        if AlertModal._instancia_ativa is not None:
            try:
                AlertModal._instancia_ativa.dismiss()
            except Exception:
                pass
        AlertModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        self.on_close_cb = on_close

        w = 580
        h = min(360 + len(erros) * 32, 600)

        # 1. Overlay escuro translúcido
        self.overlay = ctk.CTkToplevel(root)
        # 2. Cartão de alerta sólido
        self.card = ctk.CTkToplevel(root)

        theme.configurar_janela_modal(root, self.card, self.overlay, w, h)

        # Fechar ao clicar no overlay escuro ou pressionar Escape
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

        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            header,
            width=42,
            height=42,
            corner_radius=10,
            fg_color=("#FEF3C7", "#3B2703"),
            border_width=1,
            border_color=("#F59E0B", "#D97706"),
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(
            icon_box,
            text="",
            image=theme.get_icon("warning", (24, 24)),
        ).pack(expand=True)

        info = ctk.CTkFrame(header, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(info, text=titulo, font=theme.get_font(theme.FONT_SIZE_H3, "bold"), text_color=theme.COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(info, text=subtitulo, font=theme.get_font(theme.FONT_SIZE_BODY), text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w")

        # Conteúdo de erros
        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent", label_text="")
        scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        scroll.grid_columnconfigure(0, weight=1)

        for i, erro in enumerate(erros):
            ef = ctk.CTkFrame(scroll, fg_color=theme.COLOR_SURFACE_VARIANT, corner_radius=8)
            ef.grid(row=i, column=0, sticky="ew", pady=4)
            ctk.CTkLabel(ef, text="• " + erro, font=theme.get_font(theme.FONT_SIZE_BODY), text_color=theme.COLOR_TEXT, wraplength=480, justify="left").pack(anchor="w", padx=12, pady=8)

        # Footer
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="ENTENDI, VOU CORRIGIR",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self.dismiss,
        ).grid(row=0, column=0, sticky="ew")

    def dismiss(self):
        if AlertModal._instancia_ativa is self:
            AlertModal._instancia_ativa = None
        try:
            if hasattr(self, "card") and self.card and self.card.winfo_exists():
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
        if self.on_close_cb:
            self.on_close_cb()
