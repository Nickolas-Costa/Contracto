import customtkinter as ctk
from ui import theme


class AlertModal(ctk.CTkFrame):
    """Modal moderno para exibição de erros e campos pendentes.

    Renderizado como um frame flutuante perfeitamente centralizado na janela principal.
    """

    def __init__(self, master, titulo: str, subtitulo: str, erros: list[str]):
        super().__init__(
            master,
            corner_radius=16,
            fg_color=theme.COLOR_SURFACE,
            bg_color="transparent",
        )

        width = 580
        height = min(420 + len(erros) * 24, 620)
        
        import tkinter as tk
        # Fundo sólido preto
        bg_color = "#000000"
        self.overlay = tk.Frame(master, bg=bg_color)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.overlay.lift()
        
        # Centralizar na janela
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.configure(width=width, height=height)
        self.grid_propagate(False) # Força o tamanho do frame

        self.lift()
        
        # Opcional: Permitir fechar com ESC no master (necessita bind no master)
        master.bind("<Escape>", lambda e: self._on_close(), add="+")

        # Para fechar o modal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Cabeçalho (Alerta Vermelho/Amarelo + Título)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
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
        divider = ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_BORDER)
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=8)

        # 2. Lista de Erros (Condicionalmente Scrollable)
        if len(erros) > 4:
            self.scroll_erros = ctk.CTkScrollableFrame(
                self,
                fg_color="transparent",
                height=200,
            )
        else:
            self.scroll_erros = ctk.CTkFrame(self, fg_color="transparent")
        
        self.scroll_erros.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.scroll_erros.grid_columnconfigure(0, weight=1)

        for idx, erro in enumerate(erros):
            row_item = ctk.CTkFrame(
                self.scroll_erros,
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

        if isinstance(self.scroll_erros, ctk.CTkScrollableFrame):
            theme.configurar_autoscroll(self.scroll_erros)

        # Dica / Observação no Rodapé
        lbl_dica = ctk.CTkLabel(
            self,
            text="Os campos que precisam de atenção foram destacados com borda vermelha.",
            font=theme.get_font(theme.FONT_SIZE_CAPTION, "bold"),
            text_color=theme.COLOR_TEXT_SECONDARY,
        )
        lbl_dica.grid(row=3, column=0, padx=24, pady=(4, 8), sticky="w")

        # 3. Rodapé com Ações
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=4, column=0, sticky="ew", pady=(0, 24), padx=24)
        self.footer_frame.grid_columnconfigure(0, weight=1)

        btn_action = ctk.CTkButton(
            self.footer_frame,
            text="ENTENDI, VOU CORRIGIR",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_close,
        )
        btn_action.grid(row=0, column=0, sticky="ew")

    def _on_close(self) -> None:
        self.destroy()
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
