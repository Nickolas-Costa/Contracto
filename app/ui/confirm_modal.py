import customtkinter as ctk
from ui import theme


class ConfirmModal:
    """Modal de confirmação moderno com overlay escuro translúcido e cartão alinhado."""

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
        self.master = master
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        try:
            master.update_idletasks()
        except Exception:
            pass

        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()

        w, h = 540, 250

        offset_x = 110
        offset_y = 35

        x = (sw - w) // 2 + offset_x
        y = (sh - h) // 2 + offset_y

        # 1. Overlay escuro translúcido (60% opacidade / vidro escuro)
        self.overlay = ctk.CTkToplevel(master)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.configure(fg_color="#000000")
        try:
            self.overlay.attributes("-alpha", 0.60)
        except Exception:
            pass
        self.overlay.geometry(f"{sw}x{sh}+0+0")
        self.overlay.deiconify()
        self.overlay.lift()

        # 2. Cartão de confirmação sólido no topo (alinhado sobre o conteúdo)
        self.card = ctk.CTkToplevel(master)
        self.card.withdraw()
        self.card.overrideredirect(True)
        self.card.configure(fg_color=theme.COLOR_SURFACE)
        try:
            self.card.attributes("-topmost", True)
        except Exception:
            pass
        self.card.geometry(f"{w}x{h}+{x}+{y}")

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

        lbl_icon = ctk.CTkLabel(header, text="❓", font=theme.get_font(24))
        lbl_icon.grid(row=0, column=0, padx=(0, 12))

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

        self.card.deiconify()
        self.card.lift()

    def _do_confirm(self):
        self.dismiss()
        if self.on_confirm:
            self.on_confirm()

    def _do_cancel(self):
        self.dismiss()
        if self.on_cancel:
            self.on_cancel()

    def dismiss(self):
        try:
            if hasattr(self, "card") and self.card.winfo_exists():
                self.card.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, "overlay") and self.overlay.winfo_exists():
                self.overlay.destroy()
        except Exception:
            pass
