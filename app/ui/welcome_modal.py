import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal:
    """Modal de instrução e guia de uso do aplicativo com overlay escuro translúcido e cartão alinhado."""

    def __init__(self, master):
        self.master = master

        try:
            master.update_idletasks()
        except Exception:
            pass

        # Dimensões da tela do monitor
        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()

        w, h = 680, 560
        # Ajuste Fino para alinhar sobre a área principal de conteúdo
        offset_x = 110
        offset_y = 35

        x = (sw - w) // 2 + offset_x
        y = (sh - h) // 2 + offset_y

        # 1. Overlay escuro translúcido (60% opacidade / vidro escuro) cobrindo a tela inteira (0,0)
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

        # 2. Cartão de instrução sólido no topo (alinhado sobre o conteúdo)
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
            corner_radius=16,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        header.grid_columnconfigure(0, weight=1)

        info_box = ctk.CTkFrame(header, fg_color="transparent")
        info_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(info_box, text="Guia Rápido do Contracto", font=theme.get_font(theme.FONT_SIZE_H2, "bold"), text_color=theme.COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(info_box, text="Aprenda como preencher e gerar seus documentos em poucos passos", font=theme.get_font(theme.FONT_SIZE_BODY), text_color=theme.COLOR_TEXT_SECONDARY).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(header, text="✕", width=32, height=32, corner_radius=8, fg_color="transparent", text_color=theme.COLOR_TEXT_SECONDARY, hover_color=theme.COLOR_SURFACE_VARIANT, font=theme.get_font(16, "bold"), command=self.dismiss).grid(row=0, column=1, sticky="e")

        # Conteúdo do guia
        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent", label_text="")
        scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))
        scroll.grid_columnconfigure(0, weight=1)

        passos = [
            ("1. Preencha os Dados dos Participantes", "Informe Nome Completo e CPF. O primeiro participante inclui o endereço. O sistema valida os dígitos do CPF em tempo real.", "Passo 1", "👤"),
            ("2. Informe a Data e Local da Assinatura", "Selecione a data no calendário ancorado e informe a cidade de assinatura. Todos os formulários usam esse padrão.", "Passo 2", "📅"),
            ("3. Gere os Documentos com Um Clique", "Clique em 'GERAR DOCUMENTOS E AVANÇAR'. O aplicativo preenche os formulários PDF e organiza a estrutura de pastas.", "Passo 3", "⚡"),
            ("4. Personalize Cores e Perfis de Modelos", "Alterne cores nas Configurações e crie perfis na aba Perfis para ajustar modelos para Imóveis Novos, Usados ou FGTS.", "Dica", "⚙️"),
        ]

        for i, (titulo_p, desc_p, tag_p, icone_p) in enumerate(passos):
            card_p = ctk.CTkFrame(scroll, fg_color=theme.COLOR_SURFACE_VARIANT, corner_radius=theme.RADIUS_CARD)
            card_p.grid(row=i, column=0, sticky="ew", pady=6)
            card_p.grid_columnconfigure(1, weight=1)

            ibox = ctk.CTkFrame(card_p, width=40, height=40, corner_radius=10, fg_color=theme.COLOR_SURFACE)
            ibox.grid(row=0, column=0, padx=12, pady=12)
            ibox.grid_propagate(False)
            ctk.CTkLabel(ibox, text=icone_p, font=theme.get_font(18)).pack(expand=True)

            tbox = ctk.CTkFrame(card_p, fg_color="transparent")
            tbox.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=12)
            ctk.CTkLabel(tbox, text=titulo_p, font=theme.get_font(theme.FONT_SIZE_BODY, "bold"), text_color=theme.COLOR_TEXT).pack(anchor="w")
            ctk.CTkLabel(tbox, text=desc_p, font=theme.get_font(theme.FONT_SIZE_CAPTION), text_color=theme.COLOR_TEXT_SECONDARY, wraplength=420, justify="left").pack(anchor="w", pady=(2, 0))

            tag_frame = ctk.CTkFrame(card_p, fg_color=theme.COLOR_SURFACE, corner_radius=6)
            tag_frame.grid(row=0, column=2, padx=12, pady=12)
            ctk.CTkLabel(tag_frame, text=tag_p, font=theme.get_font(theme.FONT_SIZE_CAPTION, "bold"), text_color=theme.get_color_primary_text()).pack(padx=8, pady=4)

        # Footer
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="Entendi, Começar!",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self.dismiss,
        ).grid(row=0, column=0, sticky="ew")

        self.card.deiconify()
        self.card.lift()

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
        config_manager.definir("primeira_execucao", False)
