"""
Modal de instrução e guia rápido de uso do aplicativo.
Apresenta os 4 passos essenciais de forma limpa, sem barra de rolagem desnecessária.
"""

import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal:
    """Modal de instrução e guia de uso do aplicativo com overlay escuro translúcido e cartão alinhado."""

    _instancia_ativa = None

    def __init__(self, master):
        # Fechar qualquer modal de boas-vindas anterior para evitar acúmulo
        if WelcomeModal._instancia_ativa is not None:
            try:
                WelcomeModal._instancia_ativa.dismiss()
            except Exception:
                pass
        WelcomeModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root

        w, h = 680, 560

        # 1. Overlay escuro translúcido
        self.overlay = ctk.CTkToplevel(root)
        # 2. Cartão de instrução sólido
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
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 10))
        header.grid_columnconfigure(0, weight=1)

        info_box = ctk.CTkFrame(header, fg_color="transparent")
        info_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            info_box,
            text="Guia Rápido do Contracto",
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_box,
            text="Aprenda como preencher e gerar seus documentos em poucos passos",
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkButton(
            header,
            text="✕",
            width=32,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            text_color=theme.COLOR_TEXT_SECONDARY,
            hover_color=theme.COLOR_SURFACE_VARIANT,
            font=theme.get_font(16, "bold"),
            command=self.dismiss,
        ).grid(row=0, column=1, sticky="e")

        # Conteúdo do guia (quadro limpo sem barra de rolagem)
        conteudo = ctk.CTkFrame(self.frame, fg_color="transparent")
        conteudo.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 10))
        conteudo.grid_columnconfigure(0, weight=1)

        passos = [
            (
                "1. Escolha o Modo de Trabalho (TopBar)",
                "Alterne no topo entre 'Avançado' (Contratos com Etapa 1 e 2) ou 'Simples' (Emissão direta de Formulários avulsos: Form Cliente, ITBI, Isenção).",
                "Modos",
                "profiles",
            ),
            (
                "2. Preencha os Dados dos Participantes",
                "Informe Nome e CPF (validação em tempo real). Os campos dinâmicos adaptam-se automaticamente ao perfil e modelo selecionados.",
                "Etapa 1",
                "person",
            ),
            (
                "3. Emissão Rápida & Preservação de Dados",
                "Gere seus documentos em poucos segundos. Ative 'Preservar dados para Reutilizar' para emitir o próximo formulário sem precisar redigitar.",
                "Geração",
                "advance",
            ),
            (
                "4. Conversão e Conformidade PDF/A-2b",
                "No modo contrato, anexe os documentos da gerente e converta o dossiê automaticamente para o padrão oficial bancário ISO 19005-2.",
                "Etapa 2",
                "folder",
            ),
        ]

        for i, (titulo_p, desc_p, tag_p, icone_name) in enumerate(passos):
            card_p = ctk.CTkFrame(
                conteudo,
                fg_color=theme.COLOR_SURFACE_VARIANT,
                corner_radius=theme.RADIUS_CARD,
            )
            card_p.grid(row=i, column=0, sticky="ew", pady=4)
            card_p.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                card_p,
                text="",
                image=theme.get_icon(icone_name, (22, 22)),
            ).grid(row=0, column=0, padx=(16, 12), pady=12)

            tbox = ctk.CTkFrame(card_p, fg_color="transparent")
            tbox.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=10)
            ctk.CTkLabel(
                tbox,
                text=titulo_p,
                font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
                text_color=theme.COLOR_TEXT,
            ).pack(anchor="w")
            ctk.CTkLabel(
                tbox,
                text=desc_p,
                font=theme.get_font(theme.FONT_SIZE_CAPTION),
                text_color=theme.COLOR_TEXT_SECONDARY,
                wraplength=430,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

            tag_frame = ctk.CTkFrame(
                card_p,
                fg_color=theme.COLOR_SURFACE,
                corner_radius=theme.RADIUS_BUTTON,
            )
            tag_frame.grid(row=0, column=2, padx=12, pady=10)
            ctk.CTkLabel(
                tag_frame,
                text=tag_p,
                font=theme.get_font(theme.FONT_SIZE_CAPTION, "bold"),
                text_color=theme.get_color_primary_text(),
            ).pack(padx=8, pady=4)

        # Footer
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text=" Entendi, Começar!",
            image=theme.get_icon("success", (18, 18), light_only=True),
            compound="left",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self.dismiss,
        ).grid(row=0, column=0, sticky="ew")

    def dismiss(self):
        if WelcomeModal._instancia_ativa is self:
            WelcomeModal._instancia_ativa = None
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
        config_manager.definir("primeira_execucao", False)
