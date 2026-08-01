import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal(ctk.CTkFrame):
    """Modal de instrução e guia de uso do aplicativo.

    Centralizado com precisão na tela/janela principal do usuário.
    Possui suporte completo a Alt+Tab sem travar ou congelar a aplicação.
    """

    def __init__(self, master=None):
        super().__init__(
            master,
            corner_radius=16,
            border_width=1,
            border_color=theme.COLOR_BORDER,
            fg_color=theme.COLOR_SURFACE,
        )

        self._modal_width = 680
        self._modal_height = 560
        self._master_ref = master

        # Centralizar na tela
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.configure(width=self._modal_width, height=self._modal_height)
        self.grid_propagate(False)

        # Garantir visibilidade e atalho para fechar (Esc)
        self.lift()
        
        if master:
            master.bind("<Escape>", lambda e: self._on_close(), add="+")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Cabeçalho (Header com Título + Subtítulo + Botão Fechar X)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        self.header_frame.grid_columnconfigure(0, weight=1)

        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            info_box,
            text="Guia Rápido do Contracto",
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.COLOR_TEXT,
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            info_box,
            text="Aprenda como preencher e gerar seus documentos em poucos passos",
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
        btn_close.grid(row=0, column=1, sticky="e")

        # Divisor
        divider = ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_BORDER)
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=8)

        # 2. Corpo do Modal (Passo a Passo)
        self.scroll_recursos = ctk.CTkScrollableFrame(
            self, fg_color="transparent", label_text=""
        )
        self.scroll_recursos.grid(row=2, column=0, sticky="nsew", padx=24, pady=16)
        self.scroll_recursos.grid_columnconfigure(0, weight=1)

        passos = [
            {
                "icone": "👤",
                "titulo": "1. Preencha os Dados dos Participantes",
                "descricao": "Informe Nome Completo e CPF. O primeiro participante inclui o endereço. O sistema valida os dígitos do CPF em tempo real.",
                "tag": "Passo 1",
            },
            {
                "icone": "📅",
                "titulo": "2. Informe a Data e Local da Assinatura",
                "descricao": "Selecione a data no calendário ancorado e informe a cidade de assinatura. Todos os formulários usam esse padrão.",
                "tag": "Passo 2",
            },
            {
                "icone": "⚡",
                "titulo": "3. Gere os Documentos com Um Clique",
                "descricao": "Clique em 'GERAR DOCUMENTOS E AVANÇAR'. O aplicativo preenche os formulários PDF e organiza a estrutura de pastas.",
                "tag": "Passo 3",
            },
            {
                "icone": "⚙️",
                "titulo": "4. Personalize Cores e Perfis de Modelos",
                "descricao": "Alterne cores nas Configurações e crie perfis na aba Perfis para ajustar modelos para Imóveis Novos, Usados ou FGTS.",
                "tag": "Dica",
            },
        ]

        for idx, item in enumerate(passos):
            row_card = ctk.CTkFrame(
                self.scroll_recursos,
                fg_color=theme.COLOR_SURFACE_VARIANT,
                corner_radius=10,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=6)
            row_card.grid_columnconfigure(1, weight=1)

            # Ícone
            icon_box = ctk.CTkFrame(
                row_card,
                width=42,
                height=42,
                corner_radius=8,
                fg_color=theme.COLOR_SURFACE,
            )
            icon_box.grid(row=0, column=0, padx=12, pady=12)
            icon_box.grid_propagate(False)
            lbl_icon = ctk.CTkLabel(
                icon_box, text=item["icone"], font=theme.get_font(20)
            )
            lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

            # Texto (Título + Descrição)
            text_box = ctk.CTkFrame(row_card, fg_color="transparent")
            text_box.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=10)

            lbl_rec_title = ctk.CTkLabel(
                text_box,
                text=item["titulo"],
                font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
            )
            lbl_rec_title.pack(anchor="w")

            lbl_rec_desc = ctk.CTkLabel(
                text_box,
                text=item["descricao"],
                font=theme.get_font(theme.FONT_SIZE_CAPTION),
                text_color=theme.COLOR_TEXT_SECONDARY,
                justify="left",
                wraplength=380,
                anchor="w",
            )
            lbl_rec_desc.pack(anchor="w", pady=(2, 0))

            # Tag do Passo
            tag_box = ctk.CTkFrame(
                row_card,
                fg_color=theme.COLOR_SURFACE,
                corner_radius=12,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            tag_box.grid(row=0, column=2, padx=12, pady=12, sticky="e")

            lbl_tag = ctk.CTkLabel(
                tag_box,
                text=item["tag"],
                font=theme.get_font(11, "bold"),
                text_color=theme.get_color_primary_text(),
            )
            lbl_tag.pack(padx=10, pady=4)

        # 3. Rodapé com Ação
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer_frame.grid_columnconfigure(0, weight=1)

        btn_action = ctk.CTkButton(
            footer_frame,
            text="Entendi, Começar!",
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
        config_manager.definir("primeira_execucao", False)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
