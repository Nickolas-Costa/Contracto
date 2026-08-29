"""
Tela de configurações da aplicação.

Permite ao usuário configurar:
- Modo de aparência (Claro / Escuro / Sistema)
- Cor de destaque
- Formato de saída padrão
- Local padrão de assinatura
- Tamanho dos quadros
- Restaurar configurações padrão
- Diagnóstico e manutenção do sistema
"""

import customtkinter as ctk

from ui.theme import (
    COLOR_BACKGROUND, COLOR_BORDER, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XXLARGE,
    get_font, get_color_primary, get_color_primary_hover, reload_theme, configure_appearance,
    configurar_autoscroll, get_icon,
)
from utils import config_manager


# Cores pré-definidas para seleção
CORES_PREDEFINIDAS = [
    ("#1E6FB3", "Azul Institucional"),
    ("#00234E", "Azul Royal"),
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
        super().__init__(master, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, **kwargs)
        self.on_voltar = on_voltar
        self.on_aplicar = on_aplicar  # callback para atualizar a UI principal

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)  # scrollable area expande
        self.grid_rowconfigure(1, weight=0)  # separador
        self.grid_rowconfigure(2, weight=0)  # footer fixo

        self._config = config_manager.carregar_config()

        # Container scrollable para todo o conteúdo com cor de superfície consistente
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_SURFACE,
            scrollbar_button_color=COLOR_SURFACE_VARIANT,
            scrollbar_button_hover_color=COLOR_BORDER,
        )
        self._scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
        configurar_autoscroll(self._scroll)

        # Referência ao container de conteúdo (seções usam _scroll como parent)
        self._content = self._scroll

        self._construir_header()
        self._construir_secao_aparencia()
        self._construir_secao_cor()
        self._construir_secao_local()
        self._construir_secao_quadros()
        self._construir_secao_restaurar_padroes()
        self._construir_secao_diagnostico_reparo()

        # Separador visual antes do footer
        sep = ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER)
        sep.grid(row=1, column=0, sticky="ew", pady=(SPACING_SMALL, 0))

        # Footer fixo com botão Salvar (fora do scroll)
        self._construir_botoes()

    def _construir_header(self) -> None:
        header = ctk.CTkFrame(self._content, fg_color="transparent")
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
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        from ui.theme import get_icon

        ctk.CTkLabel(
            secao, text=" Aparência", image=get_icon("globe", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Tema do aplicativo", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", padx=SPACING_LARGE)

        aparencia_atual = self._config.get("aparencia", "system")
        mapa_config_to_aparencia = {"light": "Light", "dark": "Dark", "system": "Padrão do Sistema"}
        valor_inicial = mapa_config_to_aparencia.get(aparencia_atual, "Padrão do Sistema")

        self.var_aparencia = ctk.StringVar(value=valor_inicial)
        self.seg_tema = ctk.CTkSegmentedButton(
            secao,
            values=["Light", "Dark", "Padrão do Sistema"],
            variable=self.var_aparencia,
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
            selected_color=get_color_primary(),
            selected_hover_color=get_color_primary_hover(),
        )
        self.seg_tema.set(valor_inicial)
        self.seg_tema.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")

    def _construir_secao_cor(self) -> None:
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        from ui.theme import get_icon

        ctk.CTkLabel(
            secao, text=" Cor de Destaque", image=get_icon("success", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Escolha a cor principal do aplicativo",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        # Grid de cores
        cores_frame = ctk.CTkFrame(secao, fg_color="transparent")
        cores_frame.pack(padx=SPACING_LARGE, pady=SPACING_MEDIUM, fill="x")

        self._botoes_cor = []
        cor_atual = self._config.get("cor_destaque", "#1E6FB3")

        for i, (cor_hex, nome) in enumerate(CORES_PREDEFINIDAS):
            try:
                r, g, b = int(cor_hex[1:3], 16), int(cor_hex[3:5], 16), int(cor_hex[5:7], 16)
                hover = f"#{int(r*0.7):02x}{int(g*0.7):02x}{int(b*0.7):02x}"
            except:
                hover = cor_hex
            
            btn = ctk.CTkButton(
                cores_frame, text="", width=40, height=40,
                fg_color=cor_hex, hover_color=hover,
                corner_radius=RADIUS_BUTTON,
                border_width=3,
                border_color=cor_hex if cor_hex != cor_atual else "#FFFFFF",
                command=lambda c=cor_hex: self._selecionar_cor(c),
            )
            btn.grid(row=0, column=i, padx=SPACING_SMALL, pady=SPACING_SMALL)
            self._botoes_cor.append((btn, cor_hex))

        # Botão para mostrar custom color
        self.btn_toggle_custom = ctk.CTkButton(
            cores_frame, text="⚙", width=40, height=40,
            fg_color=COLOR_SURFACE_VARIANT, hover_color=COLOR_BORDER, text_color=COLOR_TEXT,
            corner_radius=RADIUS_BUTTON, font=get_font(FONT_SIZE_H3),
            command=self._toggle_custom_color
        )
        self.btn_toggle_custom.grid(row=0, column=len(CORES_PREDEFINIDAS), padx=SPACING_SMALL, pady=SPACING_SMALL)

        # Indicar cor selecionada
        self._selecionar_cor_visual(cor_atual)

        # Campo customizado (escondido por padrão)
        self.frame_custom = ctk.CTkFrame(secao, fg_color="transparent")
        
        ctk.CTkLabel(self.frame_custom, text="Cor personalizada (hex):",
                     font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY
                     ).pack(side="left")

        self.entry_cor = ctk.CTkEntry(self.frame_custom, width=100, corner_radius=RADIUS_INPUT,
                                       placeholder_text="#1E6FB3")
        self.entry_cor.pack(side="left", padx=SPACING_SMALL)
        self.entry_cor.insert(0, cor_atual)

        self.preview_cor = ctk.CTkLabel(self.frame_custom, text="  ██  ", font=get_font(FONT_SIZE_H3),
                                         text_color=cor_atual)
        self.preview_cor.pack(side="left", padx=SPACING_SMALL)

        self.entry_cor.bind("<KeyRelease>", self._ao_digitar_cor)

        self._cor_selecionada = cor_atual
        self._custom_visible = False

    def _toggle_custom_color(self) -> None:
        if self._custom_visible:
            self.frame_custom.pack_forget()
            self._custom_visible = False
            self.btn_toggle_custom.configure(fg_color=COLOR_SURFACE_VARIANT)
        else:
            self.frame_custom.pack(padx=SPACING_LARGE, pady=(0, SPACING_LARGE), fill="x")
            self._custom_visible = True
            self.btn_toggle_custom.configure(fg_color=get_color_primary())

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

    def _construir_secao_local(self) -> None:
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=3, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        from ui.theme import get_icon

        ctk.CTkLabel(
            secao, text=" Local Padrão", image=get_icon("location", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Local de assinatura pré-preenchido para novos participantes",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        self.entry_local = ctk.CTkEntry(secao, corner_radius=RADIUS_INPUT,
                                         placeholder_text="Ex: CAMOCIM-CE")
        self.entry_local.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")
        self.entry_local.insert(0, self._config.get("local_padrao", "CAMOCIM-CE"))

    def _construir_secao_quadros(self) -> None:
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=4, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        from ui.theme import get_icon

        ctk.CTkLabel(
            secao, text=" Tamanho dos Quadros", image=get_icon("ratio", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(secao, text="Largura horizontal ocupada pelas Etapas 1, 2 e aba de Perfis",
                     font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY
                     ).pack(anchor="w", padx=SPACING_LARGE)

        self.var_tamanho = ctk.StringVar(value=self._config.get("tamanho_quadros", "Médio"))
        self.seg_tamanho = ctk.CTkSegmentedButton(
            secao,
            values=["Pequeno", "Médio", "Grande"],
            variable=self.var_tamanho,
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
            selected_color=get_color_primary(),
            selected_hover_color=get_color_primary_hover(),
        )
        self.seg_tamanho.pack(padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), fill="x")

    def _construir_secao_restaurar_padroes(self) -> None:
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=5, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Restaurar Configurações Padrão", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(
            secao,
            text="Restaura todas as opções visuais, tema, cor de destaque, tamanho dos quadros e locais de assinatura para as configurações originais de fábrica.",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=SPACING_LARGE)

        from ui.theme import get_icon

        ctk.CTkButton(
            secao,
            text=" Restaurar Padrões de Fábrica",
            image=get_icon("back", (16, 16)),
            compound="left",
            fg_color=COLOR_SURFACE_VARIANT,
            text_color=COLOR_TEXT,
            border_width=1,
            border_color=COLOR_BORDER,
            hover_color=COLOR_BORDER,
            corner_radius=RADIUS_BUTTON,
            height=38,
            command=self._confirmar_e_restaurar_padroes,
        ).pack(padx=SPACING_LARGE, pady=(SPACING_MEDIUM, SPACING_LARGE), anchor="w")

    def _confirmar_e_restaurar_padroes(self) -> None:
        from ui.confirm_modal import ConfirmModal

        ConfirmModal(
            self.winfo_toplevel(),
            titulo="Restaurar Configurações Padrão",
            subtitulo="Tem certeza de que deseja restaurar todas as configurações visuais, cores e padrões para os valores de fábrica?\n\nEsta ação substituirá suas preferências atuais e não pode ser desfeita. Deseja prosseguir?",
            on_confirm=self._executar_restauracao_padroes,
            texto_confirmar="Sim, Restaurar Padrões",
            texto_cancelar="Cancelar",
        )

    def _executar_restauracao_padroes(self) -> None:
        defaults = config_manager.restaurar_padroes()

        ap = defaults.get("aparencia", "system")
        if ap == "system":
            self.var_aparencia.set("Padrão do Sistema")
        else:
            self.var_aparencia.set(ap.capitalize())
            
        self._selecionar_cor(defaults.get("cor_destaque", "#1E6FB3"))
        self.entry_local.delete(0, "end")
        self.entry_local.insert(0, defaults.get("local_padrao", "CAMOCIM-CE"))
        self.var_tamanho.set(defaults.get("tamanho_quadros", "Médio"))
        
        self._salvar()

    def _construir_secao_diagnostico_reparo(self) -> None:
        secao = ctk.CTkFrame(self._content, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                             border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=6, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

        ctk.CTkLabel(secao, text="Diagnóstico e Manutenção do Sistema", font=get_font(FONT_SIZE_H3, "bold"),
                     text_color=COLOR_TEXT).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL))

        ctk.CTkLabel(
            secao,
            text="Caso ocorram travamentos, lentidão ou falhas na automação, execute o reparo automático para encerrar processos travados em segundo plano, limpar resíduos temporários e validar os componentes do sistema.",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=SPACING_LARGE)

        from ui.theme import get_icon

        ctk.CTkButton(
            secao,
            text=" Diagnosticar e Reparar Sistema",
            image=get_icon("settings", (16, 16)),
            compound="left",
            fg_color=COLOR_SURFACE_VARIANT,
            text_color=COLOR_TEXT,
            border_width=1,
            border_color=COLOR_BORDER,
            hover_color=COLOR_BORDER,
            corner_radius=RADIUS_BUTTON,
            height=38,
            command=self._confirmar_e_reparar_sistema,
        ).pack(padx=SPACING_LARGE, pady=(SPACING_MEDIUM, SPACING_LARGE), anchor="w")

    def _confirmar_e_reparar_sistema(self) -> None:
        from ui.confirm_modal import ConfirmModal

        ConfirmModal(
            self.winfo_toplevel(),
            titulo="Diagnosticar e Reparar Sistema",
            subtitulo="Esta ação irá encerrar eventuais processos travados em segundo plano (como Word ou Ghostscript), limpar arquivos temporários e verificar a integridade dos modelos e ferramentas do sistema.\n\nEsta ação de manutenção não pode ser desfeita. Deseja prosseguir?",
            on_confirm=self._executar_reparo,
            texto_confirmar="Sim, Executar Reparo",
            texto_cancelar="Cancelar",
        )

    def _executar_reparo(self) -> None:
        import threading
        from ui.loading_modal import LoadingModal
        from ui.alert_modal import AlertModal
        from services.system_repair_service import executar_diagnostico_e_reparo

        loading = LoadingModal(self.winfo_toplevel(), message="Executando diagnóstico e reparo...")

        def _tarefa():
            import time
            time.sleep(0.5)
            resultado = executar_diagnostico_e_reparo()
            self.after(0, lambda: _ao_concluir(resultado))

        def _ao_concluir(resultado):
            loading.dismiss()
            mensagens = resultado.detalhes.copy()
            if resultado.alertas:
                mensagens.extend([f"[ALERTA] {a}" for a in resultado.alertas])

            AlertModal(
                self.winfo_toplevel(),
                titulo=resultado.titulo,
                subtitulo="Relatório de verificação e manutenção do sistema:",
                erros=mensagens,
            )

        threading.Thread(target=_tarefa, daemon=True).start()

    def _construir_botoes(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.btn_salvar = ctk.CTkButton(
            frame,
            text=" SALVAR CONFIGURAÇÕES",
            image=get_icon("save", (18, 18), light_only=True),
            compound="left",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=44,
            command=self._salvar,
        )
        self.btn_salvar.grid(row=0, column=0, sticky="ew")

    def _salvar(self) -> None:
        val = self.var_aparencia.get()
        mapa_aparencia_to_config = {
            "Light": "light",
            "Dark": "dark",
            "Padrão do Sistema": "system",
        }
        aparencia_config = mapa_aparencia_to_config.get(val, "system")
            
        config_manager.definir("aparencia", aparencia_config)
        config_manager.definir("cor_destaque", self._cor_selecionada)
        config_manager.definir("local_padrao", self.entry_local.get().strip() or "CAMOCIM-CE")
        config_manager.definir("tamanho_quadros", self.var_tamanho.get())

        if self.on_aplicar:
            self.on_aplicar()

    def atualizar_cores(self) -> None:
        """Atualiza dinamicamente as cores dos botões segmentados se o tema mudar."""
        if hasattr(self, 'seg_tema'):
            self.seg_tema.configure(
                selected_color=get_color_primary(),
                selected_hover_color=get_color_primary_hover()
            )
        if hasattr(self, 'seg_tamanho'):
            self.seg_tamanho.configure(
                selected_color=get_color_primary(),
                selected_hover_color=get_color_primary_hover()
            )
        if hasattr(self, 'btn_salvar'):
            self.btn_salvar.configure(
                fg_color=get_color_primary(),
                hover_color=get_color_primary_hover()
            )

    def recarregar_campos(self) -> None:
        """Recarrega os valores dos campos sem recriar os widgets e preservando seleções."""
        self._config = config_manager.carregar_config()
        aparencia = self._config.get("aparencia", "system")
        mapa_config_to_aparencia = {"light": "Light", "dark": "Dark", "system": "Padrão do Sistema"}
        valor_aparencia = mapa_config_to_aparencia.get(aparencia, "Padrão do Sistema")

        self.var_aparencia.set(valor_aparencia)
        if hasattr(self, 'seg_tema'):
            self.seg_tema.set(valor_aparencia)

        cor = self._config.get("cor_destaque", "#1E6FB3")
        self._selecionar_cor(cor)

        local = self._config.get("local_padrao", "CAMOCIM-CE")
        self.entry_local.delete(0, "end")
        self.entry_local.insert(0, local)

        tamanho = self._config.get("tamanho_quadros", "Médio")
        self.var_tamanho.set(tamanho)
        if hasattr(self, 'seg_tamanho'):
            self.seg_tamanho.set(tamanho)
        self.atualizar_cores()
