"""
Tela de configurações da aplicação.

Permite ao usuário configurar:
- Modo de aparência (Claro / Escuro / Sistema)
- Cor de destaque
- Formato de saída padrão
- Local padrão de assinatura
"""

import customtkinter as ctk

from ui.theme import (
    COLOR_BACKGROUND, COLOR_BORDER, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XXLARGE,
    get_font, get_color_primary, reload_theme, configure_appearance,
)
from utils import config_manager


# Cores pré-definidas para seleção
CORES_PREDEFINIDAS = [
    ("#005CA9", "Azul CAIXA"),
    ("#1565C0", "Azul Royal"),
    ("#00838F", "Ciano"),
    ("#2E7D32", "Verde"),
    ("#6A1B9A", "Roxo"),
    ("#AD1457", "Rosa"),
    ("#E65100", "Laranja"),
    ("#455A64", "Cinza Azulado"),
]


class SettingsFrame(ctk.CTkFrame):
    """Frame da tela de configurações."""

    def __init__(self, master, on_voltar=None, on_aplicar=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_voltar = on_voltar
        self.on_aplicar = on_aplicar  # callback para atualizar a UI principal

        self.grid_columnconfigure(0, weight=1)

        self._config = config_manager.carregar_config()

        self._construir_header()
        self._construir_secao_aparencia()
        self._construir_secao_cor()
        self._construir_secao_formato()
        self._construir_secao_local()
        self._construir_botoes()

    def _construir_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="ew")

        ctk.CTkLabel(
            header, text="Configurações",
            font=get_font(FONT_SIZE_H2, "bold"),
            text_color=COLOR_TEXT,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Personalize a aparência e o comportamento do Contracto.",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", pady=(SPACING_SMALL, 0))

    def _construir_secao_aparencia(self) -> None:
        secao = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Aparência", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Tema do aplicativo", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=SPACING_LARGE)

        self.var_aparencia = ctk.StringVar(value=self._config.get("aparencia", "system"))
        seg = ctk.CTkSegmentedButton(
            secao,
            values=["light", "dark", "system"],
            variable=self.var_aparencia,
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
        )
        seg.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")
        # Renomear os labels visualmente
        seg.configure(command=self._ao_mudar_aparencia)

    def _ao_mudar_aparencia(self, valor: str) -> None:
        ctk.set_appearance_mode(valor)

    def _construir_secao_cor(self) -> None:
        secao = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Cor de Destaque", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Escolha a cor principal do aplicativo",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        # Grid de cores
        cores_frame = ctk.CTkFrame(secao, fg_color="transparent")
        cores_frame.pack(padx=SPACING_LARGE, pady=SPACING_MEDIUM, fill="x")

        self._botoes_cor = []
        cor_atual = self._config.get("cor_destaque", "#005CA9")

        for i, (cor_hex, nome) in enumerate(CORES_PREDEFINIDAS):
            btn = ctk.CTkButton(
                cores_frame, text="", width=40, height=40,
                fg_color=cor_hex, hover_color=cor_hex,
                corner_radius=RADIUS_BUTTON,
                border_width=3,
                border_color=cor_hex if cor_hex != cor_atual else "#FFFFFF",
                command=lambda c=cor_hex: self._selecionar_cor(c),
            )
            btn.grid(row=0, column=i, padx=SPACING_SMALL, pady=SPACING_SMALL)
            self._botoes_cor.append((btn, cor_hex))

        # Indicar cor selecionada
        self._selecionar_cor_visual(cor_atual)

        # Campo customizado
        frame_custom = ctk.CTkFrame(secao, fg_color="transparent")
        frame_custom.pack(padx=SPACING_LARGE, pady=(0, SPACING_LARGE), fill="x")

        ctk.CTkLabel(frame_custom, text="Cor personalizada (hex):",
                     font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY
                     ).pack(side="left")

        self.entry_cor = ctk.CTkEntry(frame_custom, width=100, corner_radius=RADIUS_INPUT,
                                       placeholder_text="#005CA9")
        self.entry_cor.pack(side="left", padx=SPACING_SMALL)
        self.entry_cor.insert(0, cor_atual)

        self.preview_cor = ctk.CTkLabel(frame_custom, text="  ██  ", font=get_font(FONT_SIZE_H3),
                                         text_color=cor_atual)
        self.preview_cor.pack(side="left", padx=SPACING_SMALL)

        self.entry_cor.bind("<KeyRelease>", self._ao_digitar_cor)

        self._cor_selecionada = cor_atual

    def _selecionar_cor(self, cor_hex: str) -> None:
        self._cor_selecionada = cor_hex
        self.entry_cor.delete(0, "end")
        self.entry_cor.insert(0, cor_hex)
        self.preview_cor.configure(text_color=cor_hex)
        self._selecionar_cor_visual(cor_hex)

    def _selecionar_cor_visual(self, cor_selecionada: str) -> None:
        for btn, cor_hex in self._botoes_cor:
            if cor_hex == cor_selecionada:
                btn.configure(border_color="#FFFFFF")
            else:
                btn.configure(border_color=cor_hex)

    def _ao_digitar_cor(self, event=None) -> None:
        cor = self.entry_cor.get().strip()
        if len(cor) == 7 and cor.startswith("#"):
            try:
                int(cor[1:], 16)
                self._cor_selecionada = cor
                self.preview_cor.configure(text_color=cor)
                self._selecionar_cor_visual(cor)
            except ValueError:
                pass

    def _construir_secao_formato(self) -> None:
        secao = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=3, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Formato de Saída", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Formato padrão para os documentos gerados",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        self.var_formato = ctk.StringVar(value=self._config.get("formato_saida", "PDF/A-2b"))
        seg_formato = ctk.CTkSegmentedButton(
            secao,
            values=["PDF/A-2b", "PDF"],
            variable=self.var_formato,
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
        )
        seg_formato.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")

    def _construir_secao_local(self) -> None:
        secao = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=4, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Local Padrão", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Local de assinatura pré-preenchido para novos participantes",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        self.entry_local = ctk.CTkEntry(secao, corner_radius=RADIUS_INPUT,
                                         placeholder_text="Ex: CAMOCIM-CE")
        self.entry_local.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")
        self.entry_local.insert(0, self._config.get("local_padrao", "CAMOCIM-CE"))

    def _construir_botoes(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=5, column=0, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame, text="Restaurar Padrões",
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON, height=42,
            command=self._restaurar_padroes,
        ).grid(row=0, column=0, padx=(0, SPACING_MEDIUM))

        ctk.CTkButton(
            frame, text="SALVAR CONFIGURAÇÕES",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(), hover_color="#004785",
            corner_radius=RADIUS_BUTTON, height=42,
            command=self._salvar,
        ).grid(row=0, column=1, sticky="ew")

    def _salvar(self) -> None:
        config_manager.definir("aparencia", self.var_aparencia.get())
        config_manager.definir("cor_destaque", self._cor_selecionada)
        config_manager.definir("formato_saida", self.var_formato.get())
        config_manager.definir("local_padrao", self.entry_local.get().strip() or "CAMOCIM-CE")

        # Recarregar tema
        reload_theme()
        configure_appearance()

        if self.on_aplicar:
            self.on_aplicar()

    def _restaurar_padroes(self) -> None:
        defaults = config_manager.restaurar_padroes()

        self.var_aparencia.set(defaults["aparencia"])
        self._selecionar_cor(defaults["cor_destaque"])
        self.var_formato.set(defaults["formato_saida"])
        self.entry_local.delete(0, "end")
        self.entry_local.insert(0, defaults["local_padrao"])

        ctk.set_appearance_mode(defaults["aparencia"])
