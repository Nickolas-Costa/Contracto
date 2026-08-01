import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal(ctk.CTkToplevel):
    """Modal de instrução e guia de uso do aplicativo.

    Centralizado com precisão na tela/janela principal do usuário.
    Possui suporte completo a Alt+Tab sem travar ou congelar a aplicação.
    """

    def __init__(self, master=None):
        super().__init__(master)

        self.overrideredirect(True)
        # Fix black square corners: make the window background transparent
        try:
            self.attributes("-transparentcolor", "#000001")
        except Exception:
            pass
        self.configure(fg_color="#000001")

        self._modal_width = 680
        self._modal_height = 560
        self._master_ref = master

        # Posicionar inicialmente fora da tela para evitar flicker
        self.geometry(f"{self._modal_width}x{self._modal_height}+{-2000}+{-2000}")

        if master:
            top_level = master.winfo_toplevel()
            self.transient(top_level)

        # Permitir arrastar o modal
        self.bind("<ButtonPress-1>", self._iniciar_arrasto)
        self.bind("<B1-Motion>", self._arrastar)
        
        self._drag_x = 0
        self._drag_y = 0

        # Garantir visibilidade e atalho para fechar (Esc)
        self.lift()
        self.focus_force()
        self.bind("<Escape>", lambda e: self._on_close())

        # Centralizar após a janela estar completamente renderizada
        self.after(50, self._centralizar_no_pai)

        # Sombra
        self.shadow = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color="#000000",
        )
        # Sombra real com luz do canto superior esquerdo (deslocamento apenas para direita e baixo)
        self.shadow.place(relx=0.01, rely=0.02, relwidth=0.98, relheight=0.97)

        # Frame Principal com visual de Card
        self.card = ctk.CTkFrame(
            self,
            corner_radius=16,
            border_width=1,
            border_color=theme.COLOR_BORDER,
            fg_color=theme.COLOR_SURFACE,
        )
        self.card.place(relx=0, rely=0, relwidth=0.98, relheight=0.97)
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

        # Linha Divisória
        divider = ctk.CTkFrame(self.card, height=1, fg_color=theme.COLOR_BORDER)
        divider.grid(row=1, column=0, sticky="ew", padx=24, pady=0)

        # 2. Lista de Passos / Instruções (Card de Guias Práticos)
        self.scroll_recursos = ctk.CTkScrollableFrame(
            self.card, fg_color="transparent", label_text=""
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
                text_color=theme.get_color_primary(),
            )
            lbl_tag.pack(padx=10, pady=4)

        # 3. Rodapé com Botão Principal
        footer_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer_frame.grid_columnconfigure(0, weight=1)

        btn_action = ctk.CTkButton(
            footer_frame,
            text="Entendi, Começar!",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_close,
        )
        btn_action.grid(row=0, column=0, sticky="ew")

    def _centralizar_no_pai(self):
        """Centraliza o modal sobre a janela principal após renderização completa."""
        try:
            w = self._modal_width
            h = self._modal_height

            if self._master_ref:
                top = self._master_ref.winfo_toplevel()
                top.update_idletasks()
                # Usar winfo_x/y para obter posição da janela (mais confiável com zoomed)
                px = top.winfo_x()
                py = top.winfo_y()
                pw = top.winfo_width()
                ph = top.winfo_height()

                # Se a janela está maximizada, winfo_x/y pode retornar valores negativos no Windows
                # Nesse caso, usar coordenadas da tela
                if px < 0 or py < 0:
                    sw = self.winfo_screenwidth()
                    sh = self.winfo_screenheight()
                    x = max((sw - w) // 2, 0)
                    y = max((sh - h) // 2, 0)
                else:
                    x = px + max((pw - w) // 2, 0)
                    y = py + max((ph - h) // 2, 0)
            else:
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = max((sw - w) // 2, 0)
                y = max((sh - h) // 2, 0)

            self.geometry(f"{w}x{h}+{x}+{y}")
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _iniciar_arrasto(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _arrastar(self, event):
        x = self.winfo_x() + (event.x - self._drag_x)
        y = self.winfo_y() + (event.y - self._drag_y)
        self.geometry(f"+{x}+{y}")

    def _on_close(self):
        config_manager.definir("primeira_execucao", False)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
