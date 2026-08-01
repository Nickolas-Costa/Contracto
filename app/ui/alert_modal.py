import customtkinter as ctk
from ui import theme


class AlertModal(ctk.CTkToplevel):
    """Modal moderno para exibição de erros e campos pendentes.

    Substitui a caixa de diálogo nativa do SO por um card SaaS elegante,
    idêntico ao estilo da tela de Boas-Vindas/Ajuda, perfeitamente centralizado.
    """

    def __init__(self, master, titulo: str, subtitulo: str, erros: list[str]):
        super().__init__(master)

        self.overrideredirect(True)
        try:
            self.attributes("-transparentcolor", "#000001")
        except Exception:
            pass
        self.configure(fg_color="#000001")

        width = 580
        height = min(420 + len(erros) * 24, 620)

        # Centralizar com base na resolução real da tela (monitor do usuário)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max((sw - width) // 2, 0)
        y = max((sh - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

        if master:
            top_level = master.winfo_toplevel()
            self.transient(top_level)
            
        # Permitir arrastar o modal
        self.bind("<ButtonPress-1>", self._iniciar_arrasto)
        self.bind("<B1-Motion>", self._arrastar)
        
        self._drag_x = 0
        self._drag_y = 0

        self.lift()
        self.focus_force()
        self.bind("<Escape>", lambda e: self._on_close())

        # Sombra
        self.shadow = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color="#000000",
        )
        self.shadow.place(relx=0.01, rely=0.02, relwidth=0.98, relheight=0.97)

        # Card Principal com borda de destaque
        self.card = ctk.CTkFrame(
            self,
            corner_radius=16,
            border_width=2,
            border_color=theme.COLOR_BORDER_ERROR,
            fg_color=theme.COLOR_SURFACE,
        )
        self.card.place(relx=0, rely=0, relwidth=0.98, relheight=0.97)
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(2, weight=1)

        # 1. Cabeçalho (Alerta Vermelho/Amarelo + Título)
        self.header_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            self.header_frame,
            width=42,
            height=42,
            corner_radius=10,
            fg_color="#FFF3CD",
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)

        lbl_icon = ctk.CTkLabel(
            icon_box, text="⚠️", font=theme.get_font(22)
        )
        lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.grid(row=0, column=1, sticky="w")

        title_label = ctk.CTkLabel(
            info_box,
            text=titulo,
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.COLOR_TEXT,
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            info_box,
            text=subtitulo,
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        btn_close = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            text_color=theme.COLOR_TEXT_SECONDARY,
            hover_color=theme.COLOR_SURFACE_VARIANT,
            font=theme.get_font(16, "bold"),
            command=self._on_close,
        )
        btn_close.grid(row=0, column=2, sticky="e")

        # Divisor
        divider = ctk.CTkFrame(self.card, height=1, fg_color=theme.COLOR_BORDER)
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=8)

        # 2. Corpo / Lista de Erros
        scroll_erros = ctk.CTkScrollableFrame(
            self.card, fg_color="transparent", label_text=""
        )
        scroll_erros.grid(row=2, column=0, sticky="nsew", padx=24, pady=8)
        scroll_erros.grid_columnconfigure(0, weight=1)

        for idx, erro in enumerate(erros):
            row_item = ctk.CTkFrame(
                scroll_erros,
                fg_color=theme.COLOR_SURFACE_VARIANT,
                corner_radius=8,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            row_item.grid(row=idx, column=0, sticky="ew", pady=4)
            row_item.grid_columnconfigure(1, weight=1)

            lbl_bullet = ctk.CTkLabel(
                row_item,
                text="•",
                font=theme.get_font(16, "bold"),
                text_color=theme.COLOR_BORDER_ERROR,
            )
            lbl_bullet.grid(row=0, column=0, padx=(12, 6), pady=8, sticky="n")

            lbl_text = ctk.CTkLabel(
                row_item,
                text=erro,
                font=theme.get_font(theme.FONT_SIZE_BODY),
                text_color=theme.COLOR_TEXT,
                justify="left",
                wraplength=440,
                anchor="w",
            )
            lbl_text.grid(row=0, column=1, padx=(0, 12), pady=8, sticky="w")

        # Dica / Observação no Rodapé
        lbl_dica = ctk.CTkLabel(
            self.card,
            text="Os campos que precisam de atenção foram destacados com borda vermelha.",
            font=theme.get_font(theme.FONT_SIZE_CAPTION, "bold"),
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        lbl_dica.grid(row=3, column=0, padx=24, pady=(4, 8), sticky="w")

        # 3. Botão de Ação
        footer_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        footer_frame.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer_frame.grid_columnconfigure(0, weight=1)

        btn_action = ctk.CTkButton(
            footer_frame,
            text="ENTENDI, VOU CORRIGIR",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_close,
        )
        btn_action.grid(row=0, column=0, sticky="ew")

    def _iniciar_arrasto(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _arrastar(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def _on_close(self):
        self.destroy()
