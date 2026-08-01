import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal(ctk.CTkToplevel):
    """Modal de boas-vindas redesenhado no estilo do painel de recursos SaaS (Foto 2).

    Exibido como popup sem bordas do sistema (frameless card), centralizado
    sobre a janela principal com sombra/borda elevada.
    """

    def __init__(self, master=None):
        super().__init__(master)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=theme.COLOR_SURFACE)

        width = 620
        height = 540

        # Centralizar na janela principal
        if master:
            master.update_idletasks()
            px = master.winfo_rootx()
            py = master.winfo_rooty()
            pw = master.winfo_width()
            ph = master.winfo_height()
            x = px + max((pw - width) // 2, 10)
            y = py + max((ph - height) // 2, 10)
            self.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.geometry(f"{width}x{height}")

        self.grab_set()

        # Frame Principal com visual de Card / Sombra
        self.card = ctk.CTkFrame(
            self,
            corner_radius=16,
            border_width=1,
            border_color=theme.COLOR_BORDER,
            fg_color=theme.COLOR_SURFACE,
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(2, weight=1)

        # 1. Cabeçalho (Header com Título + Subtítulo + Botão Fechar X)
        self.header_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        self.header_frame.grid_columnconfigure(0, weight=1)

        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            info_box,
            text="Recursos e Funcionalidades",
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.COLOR_TEXT,
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            info_box,
            text="Tudo o que você precisa para automatizar seu processo documental",
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

        # Linha Divisória
        divider = ctk.CTkFrame(self.card, height=1, fg_color=theme.COLOR_BORDER)
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=0)

        # 2. Lista de Recursos (Cards no formato da Foto 2)
        self.scroll_recursos = ctk.CTkScrollableFrame(
            self.card, fg_color="transparent", label_text=""
        )
        self.scroll_recursos.grid(row=2, column=0, sticky="nsew", padx=24, pady=16)
        self.scroll_recursos.grid_columnconfigure(0, weight=1)

        recursos = [
            {
                "icone": "✨",
                "titulo": "Tudo em Conformidade (PDF/A-2b)",
                "descricao": "Converte formulários e planilhas externas para PDF/A-2b no padrão exigido pelo dossiê digital.",
                "badge": "● Incluído",
            },
            {
                "icone": "⚡",
                "titulo": "Preenchimento Automático Inteligente",
                "descricao": "Preenche dados de múltiplos participantes com validação matemática de CPF e réplica automática.",
                "badge": "● Incluído",
            },
            {
                "icone": "📋",
                "titulo": "Sistema de Perfis Personalizáveis",
                "descricao": "Crie e troque rapidamente entre perfis de documentação para Imóveis Novos, Usados e Financiamentos.",
                "badge": "● Incluído",
            },
            {
                "icone": "📁",
                "titulo": "Organização do Dossiê Digital",
                "descricao": "Gera e organiza automaticamente a estrutura das pastas ASSINADOS e REGISTRADOS.",
                "badge": "● Incluído",
            },
        ]

        for idx, rec in enumerate(recursos):
            row_card = ctk.CTkFrame(
                self.scroll_recursos,
                fg_color=theme.COLOR_SURFACE_VARIANT,
                corner_radius=10,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            row_card.grid(row=idx, column=0, sticky="ew", pady=6)
            row_card.grid_columnconfigure(1, weight=1)

            # Ícone dentro de um pequeno quadrado destacado
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
                icon_box, text=rec["icone"], font=theme.get_font(20)
            )
            lbl_icon.place(relx=0.5, rely=0.5, anchor="center")

            # Texto (Título + Descrição)
            text_box = ctk.CTkFrame(row_card, fg_color="transparent")
            text_box.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=10)

            lbl_rec_title = ctk.CTkLabel(
                text_box,
                text=rec["titulo"],
                font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.COLOR_TEXT,
                anchor="w",
            )
            lbl_rec_title.pack(anchor="w")

            lbl_rec_desc = ctk.CTkLabel(
                text_box,
                text=rec["descricao"],
                font=theme.get_font(theme.FONT_SIZE_CAPTION),
                text_color=theme.COLOR_TEXT_SECONDARY,
                justify="left",
                wraplength=360,
                anchor="w",
            )
            lbl_rec_desc.pack(anchor="w", pady=(2, 0))

            # Badge na direita (ex: ● Incluído)
            badge_box = ctk.CTkFrame(
                row_card,
                fg_color=theme.COLOR_SURFACE,
                corner_radius=12,
                border_width=1,
                border_color=theme.COLOR_BORDER,
            )
            badge_box.grid(row=0, column=2, padx=12, pady=12, sticky="e")

            lbl_badge = ctk.CTkLabel(
                badge_box,
                text=rec["badge"],
                font=theme.get_font(11, "bold"),
                text_color=theme.COLOR_SUCCESS,
            )
            lbl_badge.pack(padx=10, pady=4)

        # 3. Rodapé com Botão Principal
        footer_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer_frame.grid_columnconfigure(0, weight=1)

        btn_action = ctk.CTkButton(
            footer_frame,
            text="Começar a usar o Contracto",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_close,
        )
        btn_action.grid(row=0, column=0, sticky="ew")

    def _on_close(self):
        config_manager.definir("primeira_execucao", False)
        self.grab_release()
        self.destroy()
