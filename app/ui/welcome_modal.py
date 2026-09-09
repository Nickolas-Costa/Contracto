"""
Modal de instrução e guia rápido de uso do aplicativo.
Apresenta os 4 passos essenciais de forma limpa, sem barra de rolagem desnecessária.
"""

import customtkinter as ctk
from ui import theme
from ui.base_modal import BaseModal
from utils import config_manager


class WelcomeModal(BaseModal):
    """Modal de instrução e guia de uso do aplicativo com overlay escuro translúcido e cartão alinhado."""

    _instancia_ativa = None

    def __init__(self, master):
        # Sem trava de teclado (comportamento original: guia inicial não bloqueante).
        super().__init__(master, 680, 560, usar_grab=False)
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
                "1. Escolha o Modo de Trabalho (Barra Superior)",
                "Alterne no topo entre 'Avançado' (Contratos completos com Etapa 1 e Etapa 2) ou 'Simples' (Emissão direta de Formulários avulsos: Form Cliente, ITBI, Isenção).",
                "Modos",
                "profiles",
            ),
            (
                "2. Preencha os Dados dos Participantes",
                "Informe Nome e CPF com validação e pontuação automática. Os campos adaptam-se automaticamente ao perfil e modelo selecionados.",
                "Etapa 1",
                "person",
            ),
            (
                "3. Emissão Rápida e Preservação de Dados",
                "Gere seus documentos em PDF em poucos segundos. Deixe marcada a opção 'Preservar dados para Reutilizar' para emitir o próximo formulário sem precisar redigitar.",
                "Geração",
                "advance",
            ),
            (
                "4. Organização e Padrão Bancário (PDF/A)",
                "No modo contrato, anexe os documentos da gerente e converta todo o processo automaticamente para o formato oficial e seguro do banco.",
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
        super().dismiss()
        config_manager.definir("primeira_execucao", False)
