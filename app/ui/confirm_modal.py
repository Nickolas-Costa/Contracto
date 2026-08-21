import customtkinter as ctk
from ui import theme


class ConfirmModal:
    """Modal de confirmação moderno com overlay escuro translúcido e cartão alinhado."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        titulo: str,
        subtitulo: str,
        on_confirm=None,
        on_cancel=None,
        texto_confirmar="Confirmar",
        texto_cancelar="Cancelar",
    ):
        if ConfirmModal._instancia_ativa is not None:
            try:
                ConfirmModal._instancia_ativa.dismiss()
            except Exception:
                pass
        ConfirmModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        w, h = 540, 250

        # 1. Overlay escuro translúcido
        self.overlay = ctk.CTkToplevel(root)
        # 2. Cartão de confirmação sólido
        self.card = ctk.CTkToplevel(root)

        theme.configurar_janela_modal(root, self.card, self.overlay, w, h)

        self.card.bind("<Escape>", lambda e: self._do_cancel())

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

        # Header (Ícone + Título)
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            header,
            width=42,
            height=42,
            corner_radius=10,
            fg_color=("#E0F2FE", "#082F49"),
            border_width=1,
            border_color=("#38BDF8", "#0284C7"),
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(
            icon_box,
            text="",
            image=theme.get_icon("alert_circle", (24, 24)),
        ).pack(expand=True)

        lbl_title = ctk.CTkLabel(
            header,
            text=titulo,
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            text_color=theme.COLOR_TEXT,
        )
        lbl_title.grid(row=0, column=1, sticky="w")

        # Conteúdo
        lbl_sub = ctk.CTkLabel(
            self.frame,
            text=subtitulo,
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=480,
            justify="left",
        )
        lbl_sub.grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 10))

        # Botões
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer,
            text=texto_cancelar,
            fg_color=theme.COLOR_SURFACE,
            text_color=theme.COLOR_TEXT,
            border_width=1,
            border_color=theme.COLOR_BORDER,
            hover_color=theme.COLOR_SURFACE_VARIANT,
            corner_radius=theme.RADIUS_BUTTON,
            height=38,
            command=self._do_cancel,
        ).grid(row=0, column=0, padx=(0, 12))

        ctk.CTkButton(
            footer,
            text=texto_confirmar,
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            corner_radius=theme.RADIUS_BUTTON,
            height=38,
            command=self._do_confirm,
        ).grid(row=0, column=1, sticky="ew")

    def _do_confirm(self):
        self.dismiss()
        if self.on_confirm:
            self.on_confirm()

    def _do_cancel(self):
        self.dismiss()
        if self.on_cancel:
            self.on_cancel()

    def dismiss(self):
        if ConfirmModal._instancia_ativa is self:
            ConfirmModal._instancia_ativa = None
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
