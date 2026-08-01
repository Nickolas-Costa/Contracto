"""
Janela principal da aplicação Contracto.

Implementa a navegação entre telas (Início, Perfis, Configurações),
o gradiente de fundo inspirado no PDFCreator, e a integração com
o sistema de perfis e configurações.
"""

import os
import threading
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from models.participant import Participant
from services.generator_service import gerar_documentos, validar_antes_de_gerar
from services.pdf_service import PdfServiceError
from services.stage2_service import executar_etapa2
from ui.document_frame import DocumentFrame
from ui.participant_frame import ParticipantFrame
from ui.theme import (
    COLOR_BACKGROUND, COLOR_BORDER, COLOR_BORDER_ERROR, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_TEXT_DISABLED, COLOR_SUCCESS,
    COLOR_ERROR, COLOR_WARNING,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XXLARGE,
    SPACING_XSMALL,
    get_font, get_color_primary, get_color_primary_hover,
    get_color_primary_light, get_color_primary_dark_gradient, get_color_primary_text,
    aplicar_gradiente, configure_appearance, reload_theme,
)
from utils.date_formatter import validar_data
from ui.loading_modal import LoadingModal
from ui.feedback_toast import show_toast
from ui.settings_frame import SettingsFrame
from ui.profiles_frame import ProfilesFrame
from utils.file_picker import selecionar_arquivo_pdf, selecionar_pasta
from utils.resource_path import modelo_padrao_ppe, modelo_padrao_primeiro_imovel
from utils import config_manager
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil,
    carregar_perfis, obter_perfil, listar_nomes_perfis,
)
from PIL import Image
from ui.date_picker import DatePickerPopup


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        configure_appearance()

        self.title("Contracto v3.5 — Preparação de Documentos")
        self.geometry("1020x880")
        self.minsize(920, 700)
        self.configure(fg_color=COLOR_BACKGROUND)

        # Maximizar aplicativo por padrão ao iniciar
        self.after(10, lambda: self._maximizar_janela())

        # =============================================================
        # Estado da Aplicação
        # =============================================================
        self.pasta_saida: Path | None = None
        self.participant_frames: list[ParticipantFrame] = []

        self.participantes_etapa1: list[Participant] = []
        self.arquivos_gerados_etapa1: list[Path] = []

        self._tela_atual = "inicio"

        # Aplicar perfil ativo
        self._aplicar_perfil_ativo()

        # =============================================================
        # Layout Principal
        # =============================================================
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # row 0=toolbar, 1=gradient, 2=conteúdo

        self._load_icons()
        self._construir_toolbar()
        self._construir_gradiente()
        self._construir_stepper()

        # Containers das telas (largura de 1200px conforme Foto 2)
        card_kwargs = {"fg_color": COLOR_SURFACE, "corner_radius": RADIUS_CARD, "width": 1200}
        self.container_etapa1 = ctk.CTkFrame(self, **card_kwargs)
        self.container_etapa1.grid_columnconfigure(0, weight=1)
        self.container_etapa1.grid_rowconfigure(0, weight=1)

        self.container_etapa2 = ctk.CTkFrame(self, **card_kwargs)
        self.container_etapa2.grid_columnconfigure(0, weight=1)
        self.container_etapa2.grid_rowconfigure(2, weight=1)

        self.container_settings = None
        self.container_profiles = None

        self._construir_etapa1()
        self._construir_etapa2()

        self._adicionar_participante(principal=True)
        self._mostrar_tela("inicio")

        # Recarregar gradiente ao redimensionar
        self.bind("<Configure>", self._ao_redimensionar)
        
        # Tela de Boas Vindas
        if config_manager.obter("primeira_execucao"):
            from ui.welcome_modal import WelcomeModal
            self.after(500, lambda: WelcomeModal(self))

    def _maximizar_janela(self) -> None:
        """Maximiza a janela do aplicativo por padrão no Windows."""
        try:
            self.state("zoomed")
        except Exception:
            pass

    # ==================================================================
    # TOOLBAR (inspirada no PDFCreator)
    # ==================================================================
    def _load_icons(self) -> None:
        try:
            base = Path(__file__).parent.parent / "assets" / "icons"
            self.icon_home = ctk.CTkImage(Image.open(base / "home.png"), size=(20, 20))
            self.icon_profiles = ctk.CTkImage(Image.open(base / "profiles.png"), size=(20, 20))
            self.icon_settings = ctk.CTkImage(Image.open(base / "settings.png"), size=(20, 20))
            self.icon_calendar = ctk.CTkImage(Image.open(base / "calendar.png"), size=(20, 20))
            self.icon_help = ctk.CTkImage(Image.open(base / "help.png"), size=(20, 20))
        except Exception:
            self.icon_home = None
            self.icon_profiles = None
            self.icon_settings = None
            self.icon_calendar = None
            self.icon_help = None

    def _construir_toolbar(self) -> None:
        self.toolbar = ctk.CTkFrame(self, fg_color=get_color_primary(),
                                     corner_radius=0, height=48)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_columnconfigure(4, weight=1)  # spacer between left and right groups

        # Logo/título com fonte maior
        ctk.CTkLabel(
            self.toolbar, text="  Contracto",
            font=get_font(FONT_SIZE_H2, "bold"), text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL)

        # Separador vertical entre logo e navegação
        sep1 = ctk.CTkFrame(self.toolbar, width=1, height=28, fg_color=get_color_primary_hover(), corner_radius=0)
        sep1.grid(row=0, column=1, padx=(SPACING_SMALL, SPACING_SMALL))

        # Botões de navegação com estilo melhorado
        btn_style = {
            "fg_color": "transparent", "text_color": "#FFFFFF",
            "hover_color": get_color_primary_hover(),
            "corner_radius": RADIUS_BUTTON, "height": 36,
            "font": get_font(FONT_SIZE_BODY),
        }

        self.btn_inicio = ctk.CTkButton(
            self.toolbar, text=" Início", image=self.icon_home, width=100,
            command=lambda: self._mostrar_tela("inicio"), **btn_style,
        )
        self.btn_inicio.grid(row=0, column=2, padx=3, pady=SPACING_XSMALL)

        self.btn_perfis = ctk.CTkButton(
            self.toolbar, text=" Perfis", image=self.icon_profiles, width=100,
            command=lambda: self._mostrar_tela("perfis"), **btn_style,
        )
        self.btn_perfis.grid(row=0, column=3, padx=3, pady=SPACING_XSMALL)

        # Spacer (column 4 has weight=1)

        # Separador vertical antes dos botões à direita
        sep2 = ctk.CTkFrame(self.toolbar, width=1, height=28, fg_color=get_color_primary_hover(), corner_radius=0)
        sep2.grid(row=0, column=5, padx=(SPACING_SMALL, SPACING_SMALL))

        self.btn_ajuda = ctk.CTkButton(
            self.toolbar, text=" Ajuda", image=self.icon_help, width=95,
            command=self._abrir_ajuda, **btn_style,
        )
        self.btn_ajuda.grid(row=0, column=6, padx=3, pady=SPACING_XSMALL)

        self.btn_config = ctk.CTkButton(
            self.toolbar, text=" Configurações", image=self.icon_settings, width=140,
            command=lambda: self._mostrar_tela("config"), **btn_style,
        )
        self.btn_config.grid(row=0, column=7, padx=(3, SPACING_LARGE), pady=SPACING_XSMALL)

    def _abrir_ajuda(self) -> None:
        """Abre o guia interativo de uso do aplicativo."""
        from ui.welcome_modal import WelcomeModal
        WelcomeModal(self)

    # ==================================================================
    # GRADIENTE DE FUNDO
    # ==================================================================
    def _construir_gradiente(self) -> None:
        self.canvas_gradient = tk.Canvas(self, highlightthickness=0)
        self.canvas_gradient.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.canvas_gradient.tk.call('lower', self.canvas_gradient._w)
        self._pintar_gradiente()

    def _pintar_gradiente(self) -> None:
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura = max(self.winfo_width(), sw, 1024)
        altura = max(self.winfo_height(), sh, 768)
        modo = ctk.get_appearance_mode()
        
        if modo == "Dark":
            cor1 = get_color_primary_dark_gradient()
            cor2 = "#1E1E1E"
        else:
            cor1 = get_color_primary()
            cor2 = get_color_primary_light()
            
        # Gradiente vertical (cima para baixo)
        aplicar_gradiente(self.canvas_gradient, largura, altura, cor1, cor2, vertical=True)

    _ultimo_w = 0
    _ultimo_h = 0

    def _ao_redimensionar(self, event=None) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        if w != self._ultimo_w or h != self._ultimo_h:
            self._ultimo_w = w
            self._ultimo_h = h
            self._pintar_gradiente()

    # ==================================================================
    # STEPPER (indicador de etapas)
    # ==================================================================
    def _construir_stepper(self) -> None:
        self.frame_stepper = ctk.CTkFrame(self, fg_color="transparent",
                                           corner_radius=0, height=36)
        # Posicionado sobre o gradiente
        self.frame_stepper.grid(row=1, column=0, sticky="ew")
        self.frame_stepper.grid_columnconfigure(0, weight=1)
        self.frame_stepper.grid_columnconfigure(2, weight=1)
        self.frame_stepper.lift()

        self.lbl_etapa1 = ctk.CTkLabel(
            self.frame_stepper, text="1. Geração de Documentos",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=get_color_primary_text()
        )
        self.lbl_etapa1.grid(row=0, column=0, pady=SPACING_MEDIUM, sticky="e", padx=SPACING_MEDIUM)

        self.lbl_seta = ctk.CTkLabel(
            self.frame_stepper, text="  →  ",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED,
        )
        self.lbl_seta.grid(row=0, column=1, pady=SPACING_MEDIUM)

        self.lbl_etapa2 = ctk.CTkLabel(
            self.frame_stepper, text="2. Conversão e Organização",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED,
        )
        self.lbl_etapa2.grid(row=0, column=2, pady=SPACING_MEDIUM, sticky="w", padx=SPACING_MEDIUM)

        # Perfil ativo - Dropdown selecionável
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        nomes_perfis = listar_nomes_perfis()
        if not nomes_perfis:
            nomes_perfis = [PERFIL_PADRAO_NOME]

        frame_perfil_row = ctk.CTkFrame(self.frame_stepper, fg_color="transparent")
        frame_perfil_row.grid(row=1, column=0, columnspan=3, pady=(0, SPACING_SMALL))

        ctk.CTkLabel(
            frame_perfil_row, text="Perfil:",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        ).pack(side="left", padx=(0, SPACING_XSMALL))

        self.dropdown_perfil = ctk.CTkComboBox(
            frame_perfil_row,
            values=nomes_perfis,
            variable=ctk.StringVar(value=perfil_nome),
            command=self._ao_trocar_perfil,
            width=160,
            height=26,
            border_width=0,
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION),
            dropdown_font=get_font(FONT_SIZE_CAPTION),
            fg_color=get_color_primary(),
            button_color=get_color_primary_hover(),
            button_hover_color=get_color_primary_hover(),
            dropdown_fg_color=COLOR_SURFACE,
            dropdown_hover_color=COLOR_SURFACE_VARIANT,
            dropdown_text_color=COLOR_TEXT,
            text_color="#FFFFFF",
            state="readonly"
        )
        self.dropdown_perfil.pack(side="left")

    def _ao_trocar_perfil(self, nome_perfil: str) -> None:
        """Callback ao selecionar um perfil no dropdown."""
        config_manager.definir("perfil_ativo", nome_perfil)
        self._aplicar_perfil_ativo()
        show_toast(self, f"Perfil alterado para: {nome_perfil}", "success")

    def _atualizar_stepper(self, etapa: int) -> None:
        cor = get_color_primary()
        if etapa == 1:
            self.lbl_etapa1.configure(text_color=get_color_primary_text())
            self.lbl_etapa2.configure(text_color=COLOR_TEXT_DISABLED)
        else:
            self.lbl_etapa1.configure(text_color=COLOR_TEXT_DISABLED)
            self.lbl_etapa2.configure(text_color=get_color_primary_text())

        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        # Atualizar o dropdown de perfil
        nomes_perfis = listar_nomes_perfis()
        if nomes_perfis:
            self.dropdown_perfil.configure(values=nomes_perfis)
        self.dropdown_perfil.set(perfil_nome)

    # ==================================================================
    # NAVEGAÇÃO ENTRE TELAS
    # ==================================================================
    def _mostrar_tela(self, tela: str) -> None:
        """Alterna entre as telas: inicio, perfis, config."""
        # Esconder todas
        self.container_etapa1.grid_forget()
        self.container_etapa2.grid_forget()
        if self.container_settings:
            self.container_settings.grid_forget()
        if self.container_profiles:
            self.container_profiles.grid_forget()

        # Atualizar toolbar highlight
        normal = {"fg_color": "transparent", "text_color": "#FFFFFF"}
        active = {"fg_color": get_color_primary_hover(), "text_color": "#FFFFFF"}
        self.btn_inicio.configure(**normal)
        self.btn_perfis.configure(**normal)
        self.btn_config.configure(**normal)

        self._tela_atual = tela
        
        # Obter o tamanho dos quadros selecionado nas configurações
        tamanho = config_manager.obter("tamanho_quadros")
        
        # A largura dos quadros é controlada pelo 'padx' (margem lateral).
        # Para alterar manualmente:
        # - Valores MENORES (ex: 30) = Quadros mais LARGOS (menos margem)
        # - Valores MAIORES (ex: 120) = Quadros mais ESTREITOS (mais margem)
        if tamanho == "Pequeno":
            margem = 400
        elif tamanho == "Grande":
            margem = 100
        else:
            margem = 250 # Médio (Padrão)

        # Grid settings for floating cards
        card_grid = {"row": 2, "column": 0, "sticky": "ew", "padx": margem, "pady": SPACING_LARGE}

        if tela == "inicio":
            self.btn_inicio.configure(**active)
            self.frame_stepper.grid(row=1, column=0, sticky="ew")
            self.frame_stepper.lift()
            self.container_etapa1.grid(**card_grid)
            self._atualizar_stepper(1)
        elif tela == "etapa2":
            self.btn_inicio.configure(**active)
            self.frame_stepper.grid(row=1, column=0, sticky="ew")
            self.frame_stepper.lift()
            self.container_etapa2.grid(**card_grid)
            self._atualizar_stepper(2)
            # Atualizar documentos baseados no perfil ativo
            p_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
            from utils.profile_manager import obter_perfil
            p = obter_perfil(p_nome)
            if p:
                self.document_frame.carregar_documentos(p.documentos_extras)
        elif tela == "perfis":
            self.btn_perfis.configure(**active)
            self.frame_stepper.grid_forget()
            if not self.container_profiles:
                self.container_profiles = ProfilesFrame(self, on_voltar=lambda: self._mostrar_tela("inicio"))
                self.container_profiles.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD)
            else:
                self.container_profiles._carregar_lista()
            self.container_profiles.grid(**card_grid)
        elif tela == "config":
            self.btn_config.configure(**active)
            self.frame_stepper.grid_forget()
            if self.container_settings:
                self.container_settings.destroy()
            self.container_settings = SettingsFrame(
                self,
                on_voltar=lambda: self._mostrar_tela("inicio"),
                on_aplicar=self._ao_aplicar_config,
            )
            self.container_settings.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD)
            self.container_settings.grid(**card_grid)

    def _ao_aplicar_config(self) -> None:
        """Callback chamado após salvar configurações."""
        reload_theme()
        self.toolbar.configure(fg_color=get_color_primary())
        if hasattr(self, 'dropdown_perfil'):
            self.dropdown_perfil.configure(
                fg_color=get_color_primary(),
                button_color=get_color_primary_hover(),
                button_hover_color=get_color_primary_hover(),
                dropdown_fg_color=COLOR_SURFACE,
                dropdown_hover_color=COLOR_SURFACE_VARIANT,
                dropdown_text_color=COLOR_TEXT,
                text_color="#FFFFFF",
            )
        if hasattr(self, 'botao_avancar'):
            self.botao_avancar.configure(
                fg_color=get_color_primary(), hover_color=get_color_primary_hover(),
                text_color="#FFFFFF"
            )
        if hasattr(self, 'btn_voltar'):
            self.btn_voltar.configure(
                text_color=get_color_primary_text(), hover_color=COLOR_SURFACE_VARIANT
            )
        if hasattr(self, 'botao_finalizar'):
            self.botao_finalizar.configure(
                fg_color=get_color_primary(), hover_color=get_color_primary_hover(),
                text_color="#FFFFFF"
            )
        if hasattr(self, 'botao_adicionar'):
            self.botao_adicionar.configure(
                text_color=get_color_primary_text(),
                border_color=get_color_primary()
            )
        
        # Atualizar frames de participantes
        if hasattr(self, 'participant_frames'):
            for pf in self.participant_frames:
                pf.atualizar_cores()
            
        self._pintar_gradiente()
        self._atualizar_stepper(1 if self._tela_atual == "etapa1" else 2 if self._tela_atual == "etapa2" else 1)
        
        # Atualizar cores dos frames independentes
        if hasattr(self, 'container_settings'):
            self.container_settings.atualizar_cores()
        if hasattr(self, 'container_profiles'):
            self.container_profiles.atualizar_cores()
        
        # Atualizar entry de local
        if hasattr(self, 'entry_local'):
            self.entry_local.delete(0, 'end')
            self.entry_local.insert(0, config_manager.obter("local_padrao") or "CAMOCIM-CE")
        
        # Re-aplicar apenas as margens
        self._atualizar_tamanho_janela()
        
        show_toast(self, "Configurações atualizadas!", "success")

    def _atualizar_tamanho_janela(self) -> None:
        tamanho = config_manager.obter("tamanho_quadros")
        if tamanho == "Pequeno":
            margem = 400
        elif tamanho == "Grande":
            margem = 100
        else:
            margem = 250
            
        if self._tela_atual == "inicio" and hasattr(self, 'container_etapa1'):
            self.container_etapa1.grid(padx=margem)
        elif self._tela_atual == "etapa2" and hasattr(self, 'container_etapa2'):
            self.container_etapa2.grid(padx=margem)
        elif self._tela_atual == "perfis" and hasattr(self, 'container_profiles'):
            self.container_profiles.grid(padx=margem)
        elif self._tela_atual == "config" and hasattr(self, 'container_settings'):
            self.container_settings.grid(padx=margem)
        
        self.update_idletasks()

    def _aplicar_perfil_ativo(self) -> None:
        """Os modelos agora são carregados a partir do perfil no momento da geração."""
        pass

    # ------------------------------------------------------------------
    # ETAPA 1: Preenchimento e Validação
    # ------------------------------------------------------------------
    def _construir_etapa1(self) -> None:
        self._construir_secao_participantes()
        self._construir_secao_saida()

        self.botao_avancar = ctk.CTkButton(
            self.container_etapa1,
            text="AVANÇAR ETAPA ➔",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            text_color="#FFFFFF",
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_avancar,
        )
        self.botao_avancar.grid(row=3, column=0, padx=SPACING_LARGE,
                                 pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")



    def _construir_secao_participantes(self) -> None:
        self.secao_participantes = ctk.CTkFrame(self.container_etapa1, fg_color="transparent")
        self.secao_participantes.grid(row=0, column=0, padx=SPACING_LARGE,
                   pady=(SPACING_LARGE, SPACING_SMALL), sticky="nsew")
        self.secao_participantes.grid_columnconfigure(0, weight=1)
        self.secao_participantes.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(self.secao_participantes, text="Participantes",
                              font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")

        # Container simples (sem scroll) — usado quando há apenas 1 participante
        self.participantes_container = ctk.CTkFrame(
            self.secao_participantes, fg_color="transparent"
        )
        self.participantes_container.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.participantes_container.grid_columnconfigure(0, weight=1)

        # Container com scroll — será criado sob demanda quando houver 2+ participantes
        self.participantes_scroll = None
        self._usando_scroll = False

        self.botao_adicionar = ctk.CTkButton(
            self.secao_participantes, text="+ Adicionar Participante",
            fg_color=COLOR_SURFACE, text_color=get_color_primary_text(),
            border_width=1, border_color=get_color_primary_text(),
            hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
            command=self._adicionar_participante,
        )
        self.botao_adicionar.grid(row=2, column=0, padx=0, pady=(SPACING_XLARGE, 0), sticky="w")

    def _construir_secao_saida(self) -> None:
        secao = ctk.CTkFrame(self.container_etapa1, fg_color="transparent")
        secao.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        secao.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(secao, text="Destino",
                              font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, columnspan=3, padx=SPACING_LARGE,
                    pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        # Global fields
        ctk.CTkLabel(secao, text="Data da assinatura", font=get_font(FONT_SIZE_BODY)).grid(
            row=1, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")
            
        frame_data = ctk.CTkFrame(secao, fg_color="transparent")
        frame_data.grid(row=1, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        frame_data.grid_columnconfigure(0, weight=1)
        
        self.entry_data = ctk.CTkEntry(frame_data, placeholder_text="DD/MM/AAAA", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        self.entry_data.grid(row=0, column=0, sticky="ew")
        self.entry_data.bind("<KeyRelease>", lambda e: self._validar_data_realtime())
        self.entry_data.bind("<FocusOut>", lambda e: self._validar_data_realtime())
        
        self.btn_calendar = ctk.CTkButton(
            frame_data, text="", image=self.icon_calendar, width=32, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_VARIANT,
            command=lambda: DatePickerPopup(self, self.entry_data, anchor_widget=self.btn_calendar)
        )
        self.btn_calendar.grid(row=0, column=1, padx=(SPACING_SMALL, 0))

        ctk.CTkLabel(secao, text="Local da assinatura", font=get_font(FONT_SIZE_BODY)).grid(
            row=2, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")
        self.entry_local = ctk.CTkEntry(secao, corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        self.entry_local.grid(row=2, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        self.entry_local.insert(0, config_manager.obter("local_padrao") or "CAMOCIM-CE")
        self.entry_local.bind("<KeyRelease>", lambda e: self._validar_local_realtime())
        self.entry_local.bind("<FocusOut>", lambda e: self._validar_local_realtime())

        # Set default directory to Downloads
        if os.name == "nt":
            downloads_path = Path(os.environ["USERPROFILE"]) / "Downloads"
        else:
            downloads_path = Path.home() / "Downloads"
        self.pasta_saida = downloads_path

        # Directory Selector
        ctk.CTkLabel(secao, text="Diretório de saída:", font=get_font(FONT_SIZE_BODY, "bold")).grid(
            row=3, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM),
            pady=(SPACING_SMALL, SPACING_LARGE), sticky="w")
        
        frame_dir = ctk.CTkFrame(secao, fg_color="transparent")
        frame_dir.grid(row=3, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_dir.grid_columnconfigure(0, weight=1)

        self.entry_pasta_saida = ctk.CTkEntry(
            frame_dir, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_INPUT,
            border_color=COLOR_BORDER,
        )
        self.entry_pasta_saida.grid(row=0, column=0, sticky="ew")
        self.entry_pasta_saida.insert(0, str(downloads_path))
        # Entry editável — permite colar/digitar caminho manualmente
        self.entry_pasta_saida.bind("<KeyRelease>", lambda e: self._ao_editar_pasta_saida())
        self.entry_pasta_saida.bind("<FocusOut>", lambda e: self._ao_editar_pasta_saida())

        ctk.CTkButton(frame_dir, text="...", width=40, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_BORDER, text_color=COLOR_TEXT,
                      hover_color=COLOR_TEXT_DISABLED, command=self._selecionar_pasta_saida
                      ).grid(row=0, column=1, padx=(SPACING_SMALL, 0))

    def _validar_data_realtime(self) -> bool:
        val = self.entry_data.get().strip()
        if not val or not validar_data(val):
            self.entry_data.configure(border_color=COLOR_BORDER_ERROR)
            return False
        else:
            self.entry_data.configure(border_color=COLOR_BORDER)
            return True

    def _validar_local_realtime(self) -> bool:
        val = self.entry_local.get().strip()
        if not val:
            self.entry_local.configure(border_color=COLOR_BORDER_ERROR)
            return False
        else:
            self.entry_local.configure(border_color=COLOR_BORDER)
            return True

    def _obter_container_participantes(self):
        """Retorna o container atual onde os participantes são adicionados."""
        if self._usando_scroll and self.participantes_scroll:
            return self.participantes_scroll
        return self.participantes_container

    def _migrar_para_scroll(self) -> None:
        """Migra os participantes de um frame simples para um scrollable."""
        if self._usando_scroll:
            return

        # Criar scrollable frame
        self.participantes_scroll = ctk.CTkScrollableFrame(
            self.secao_participantes, fg_color="transparent", label_text="", height=380
        )
        self.participantes_scroll.grid_columnconfigure(0, weight=1)

        # Mover todos os frames existentes para o scroll
        for idx, pf in enumerate(self.participant_frames):
            pf.grid_forget()
            pf.pack_forget() if hasattr(pf, 'pack_forget') else None
            # Reparent: destruir e recriar não é necessário — basta re-griddar
            # Tkinter não suporta reparent nativo, então recriamos
        
        frames_dados = []
        for pf in self.participant_frames:
            dados = {
                "nome": pf.entry_nome.get(),
                "cpf": pf.entry_cpf.get(),
                "endereco": pf.entry_endereco.get() if pf.entry_endereco else "",
                "principal": pf.principal,
                "indice": pf.indice,
            }
            frames_dados.append(dados)
            pf.destroy()
        
        self.participant_frames.clear()

        # Esconder container simples, mostrar scroll
        self.participantes_container.grid_forget()
        self.participantes_scroll.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self._usando_scroll = True

        # Recriar participantes no scroll
        for dados in frames_dados:
            local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
            frame = ParticipantFrame(
                self.participantes_scroll,
                indice=dados["indice"],
                principal=dados["principal"],
                on_remover=None if dados["principal"] else self._remover_participante,
                local_padrao=local_padrao,
            )
            frame.grid(row=dados["indice"] - 1, column=0, padx=SPACING_XSMALL,
                       pady=SPACING_SMALL, sticky="ew")
            frame.entry_nome.insert(0, dados["nome"])
            frame.entry_cpf.insert(0, dados["cpf"])
            if frame.entry_endereco and dados["endereco"]:
                frame.entry_endereco.insert(0, dados["endereco"])
            self.participant_frames.append(frame)

    def _migrar_para_simples(self) -> None:
        """Migra de volta para um frame simples quando resta apenas 1 participante."""
        if not self._usando_scroll:
            return

        # Salvar dados do participante restante
        pf = self.participant_frames[0]
        dados = {
            "nome": pf.entry_nome.get(),
            "cpf": pf.entry_cpf.get(),
            "endereco": pf.entry_endereco.get() if pf.entry_endereco else "",
        }
        pf.destroy()
        self.participant_frames.clear()

        # Remover scroll e restaurar container simples
        self.participantes_scroll.grid_forget()
        self.participantes_scroll.destroy()
        self.participantes_scroll = None
        self._usando_scroll = False

        self.participantes_container = ctk.CTkFrame(
            self.secao_participantes, fg_color="transparent"
        )
        self.participantes_container.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.participantes_container.grid_columnconfigure(0, weight=1)

        # Recriar o participante no container simples
        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        frame = ParticipantFrame(
            self.participantes_container,
            indice=1,
            principal=True,
            on_remover=None,
            local_padrao=local_padrao,
        )
        frame.grid(row=0, column=0, padx=SPACING_XSMALL,
                   pady=SPACING_SMALL, sticky="ew")
        frame.entry_nome.insert(0, dados["nome"])
        frame.entry_cpf.insert(0, dados["cpf"])
        if frame.entry_endereco and dados["endereco"]:
            frame.entry_endereco.insert(0, dados["endereco"])
        self.participant_frames.append(frame)

    def _adicionar_participante(self, principal: bool = False) -> None:
        indice = len(self.participant_frames) + 1

        # Se vai passar de 1 para 2, migrar para scroll
        if indice == 2 and not self._usando_scroll:
            self._migrar_para_scroll()

        container = self._obter_container_participantes()
        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        frame = ParticipantFrame(
            container,
            indice=indice,
            principal=principal,
            on_remover=None if principal else self._remover_participante,
            local_padrao=local_padrao,
        )
        frame.grid(row=indice - 1, column=0, padx=SPACING_XSMALL,
                   pady=SPACING_SMALL, sticky="ew")
        self.participant_frames.append(frame)

        self._atualizar_tamanho_participantes()

        if not principal:
            frame.piscar_destaque()

    def _remover_participante(self, frame: ParticipantFrame) -> None:
        frame.destroy()
        self.participant_frames.remove(frame)
        for novo_indice, restante in enumerate(self.participant_frames, start=1):
            restante.atualizar_indice(novo_indice)

        # Se voltou a 1 participante, migrar de volta para simples
        if len(self.participant_frames) == 1 and self._usando_scroll:
            self._migrar_para_simples()
        else:
            self._atualizar_tamanho_participantes()

    def _atualizar_tamanho_participantes(self) -> None:
        qtd = len(self.participant_frames)
        if not self._usando_scroll or not self.participantes_scroll:
            return
        if qtd == 2:
            self.participantes_scroll.configure(height=380)
        else:
            self.participantes_scroll.configure(height=450)

    def _verificar_permissao_escrita(self, pasta: Path) -> bool:
        if not pasta or not pasta.exists():
            return False
        try:
            teste_arq = pasta / ".teste_escrita"
            teste_arq.touch()
            teste_arq.unlink()
            return True
        except Exception:
            return False

    def _ao_clicar_avancar(self) -> None:
        erros: list[str] = []

        # 1. Validar campos de todos os participantes (destacando os erros em vermelho)
        for frame in self.participant_frames:
            erros.extend(frame.validar_campos())

        # 2. Validar Data e Local da assinatura
        if not self._validar_data_realtime():
            val = self.entry_data.get().strip()
            if not val:
                erros.append("Data da assinatura é obrigatória.")
            else:
                erros.append("Data da assinatura é inválida. Utilize o formato DD/MM/AAAA (ex.: 15/07/2026).")

        if not self._validar_local_realtime():
            erros.append("Local da assinatura é obrigatório.")

        # 3. Validar perfil e arquivos de modelos
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        if not perfil:
            erros.append(f"O perfil ativo '{perfil_nome}' não foi encontrado.")
        elif not perfil.formularios:
            erros.append(f"O perfil '{perfil.nome}' não possui nenhum formulário configurado.")
        else:
            from services.generator_service import resolver_caminho_formulario
            for f in perfil.formularios:
                caminho_resolvido = resolver_caminho_formulario(f)
                if not caminho_resolvido or not caminho_resolvido.exists():
                    erros.append(f"O formulário '{f.nome}' aponta para um arquivo inexistente.")

        # 4. Validar pasta de saída e permissões
        if not self.pasta_saida:
            erros.append("Selecione a pasta de saída.")
        elif not self._verificar_permissao_escrita(self.pasta_saida):
            erros.append(f"Sem permissão de escrita na pasta de saída: {self.pasta_saida}")

        # Se houver qualquer erro, detalhar ao usuário com o Modal de Alerta
        if erros:
            from ui.alert_modal import AlertModal
            AlertModal(
                self,
                titulo="Campos Pendentes ou Inválidos",
                subtitulo="Não foi possível avançar. Verifique os seguintes itens:",
                erros=erros,
            )
            return

        principal = self.participant_frames[0].obter_participante()
        principal.data_assinatura = self.entry_data.get().strip()
        principal.local_assinatura = self.entry_local.get().strip()

        participantes = [principal]
        for frame in self.participant_frames[1:]:
            p = frame.obter_participante()
            p.copiar_dados_compartilhados(principal)
            participantes.append(p)

        self.participantes_etapa1 = participantes
        self.label_pasta_etapa2.configure(text=f"Pasta: {self.pasta_saida}")

        # Avança direto para a Etapa 2 (a geração ocorrerá na finalização)
        self._mostrar_tela("etapa2")

    # ------------------------------------------------------------------
    # ETAPA 2: Documentos da Gerente e PDF/A
    # ------------------------------------------------------------------
    def _construir_etapa2(self) -> None:
        frame_header = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_header.grid(row=0, column=0, padx=SPACING_LARGE,
                          pady=(SPACING_LARGE, 0), sticky="ew")
        frame_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_header, text="Organização de Arquivos",
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w", pady=(0, SPACING_SMALL))

        self.label_pasta_etapa2 = ctk.CTkLabel(
            frame_header, text="Pasta: ",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_pasta_etapa2.grid(row=1, column=0, sticky="w")

        # Mostrar formato de saída do perfil
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        formato = perfil.formato_saida if perfil else "PDF/A-2b"

        self.label_formato_etapa2 = ctk.CTkLabel(
            frame_header, text=f"Formato de saída: {formato}",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_formato_etapa2.grid(row=2, column=0, sticky="w")

        frame_docs = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_docs.grid(row=1, column=0, padx=SPACING_LARGE,
                        pady=SPACING_LARGE, sticky="nsew")
        frame_docs.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_docs, text="Adicionar documentos extras (opcional)",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")

        ctk.CTkLabel(
            frame_docs,
            text="Arquivos selecionados aqui serão renomeados e organizados.",
            text_color=COLOR_TEXT_SECONDARY, justify="left",
            font=get_font(FONT_SIZE_BODY),
        ).grid(row=1, column=0, padx=0, pady=(0, SPACING_LARGE), sticky="w")

        self.document_frame = DocumentFrame(frame_docs)
        self.document_frame.grid(row=2, column=0, padx=0, pady=0, sticky="ew")
        if perfil:
            self.document_frame.carregar_documentos(perfil.documentos_extras)

        frame_botoes = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_botoes.grid(row=3, column=0, padx=SPACING_LARGE,
                          pady=(0, SPACING_LARGE), sticky="ew")
        frame_botoes.grid_columnconfigure(1, weight=1)

        self.botao_voltar = ctk.CTkButton(
            frame_botoes, text="Voltar",
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON, height=48,
            command=lambda: self._mostrar_tela("inicio"),
        )
        self.botao_voltar.grid(row=0, column=0, padx=(0, SPACING_MEDIUM))

        self.botao_finalizar = ctk.CTkButton(
            frame_botoes,
            text="FINALIZAR PROCESSO",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            text_color="#FFFFFF",
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_finalizar,
        )
        self.botao_finalizar.grid(row=0, column=1, sticky="ew")

    def _ao_clicar_finalizar(self) -> None:
        if not self.pasta_saida:
            return

        documentos_externos = self.document_frame.obter_documentos_selecionados()
        total_documentos = self.document_frame.obter_total_documentos()

        if total_documentos > 0 and len(documentos_externos) < total_documentos:
            from ui.confirm_modal import ConfirmModal
            ConfirmModal(
                self,
                titulo="Documentos Incompletos",
                subtitulo="Você não selecionou todos os documentos extras recomendados. Tem certeza de que deseja gerar apenas os formulários selecionados e finalizar o processo?",
                on_confirm=self._prosseguir_finalizar,
            )
            return
            
        self._prosseguir_finalizar()
        
    def _prosseguir_finalizar(self) -> None:
        # Obter formato do perfil ativo
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        formato_saida = perfil.formato_saida if perfil else "PDF/A-2b"
        
        documentos_externos = self.document_frame.obter_documentos_selecionados()

        self.botao_finalizar.configure(state="disabled")
        self.botao_voltar.configure(state="disabled")

        self._loading2 = LoadingModal(self, "Gerando e organizando documentos...")

        thread = threading.Thread(
            target=self._finalizar_em_background,
            args=(documentos_externos, formato_saida), daemon=True,
        )
        thread.start()

    def _finalizar_em_background(self, documentos_externos, formato_saida):
        try:
            # 1. Gerar os documentos PDF a partir dos dados preenchidos
            perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
            perfil = obter_perfil(perfil_nome)

            resultado_geracao = gerar_documentos(
                self.participantes_etapa1, perfil, self.pasta_saida,
            )
            self.arquivos_gerados_etapa1 = resultado_geracao.arquivos_gerados

            # 2. Executar a conversão para PDF/A e organização de pastas
            resultado = executar_etapa2(
                pasta_base=self.pasta_saida,
                participantes=self.participantes_etapa1,
                arquivos_gerados_etapa1=self.arquivos_gerados_etapa1,
                documentos_externos=documentos_externos,
                formato_saida=formato_saida,
            )
            self.after(0, lambda: self._ao_concluir_etapa2(resultado))
        except Exception as exc:
            self.after(0, lambda: self._ao_erro_etapa2(exc))

    def _ao_concluir_etapa2(self, resultado):
        if hasattr(self, "_loading2"):
            self._loading2.dismiss()

        self.botao_finalizar.configure(state="normal")
        self.botao_voltar.configure(state="normal")

        if resultado["sucesso"]:
            msg = f"{resultado['mensagem']}\nEstrutura:\n{resultado['pasta_pdfa']}"
            if messagebox.askyesno("Concluído", msg + "\n\nDeseja abrir a pasta?"):
                self._abrir_pasta(resultado["pasta_pdfa"])
            self._resetar_aplicacao()
        else:
            show_toast(self, resultado["mensagem"], "error")

    def _ao_erro_etapa2(self, exc):
        if hasattr(self, "_loading2"):
            self._loading2.dismiss()
        self.botao_finalizar.configure(state="normal")
        self.botao_voltar.configure(state="normal")
        show_toast(self, f"Erro: {str(exc)}", "error")

    def _resetar_aplicacao(self) -> None:
        self._mostrar_tela("inicio")
        for frame in list(self.participant_frames[1:]):
            self._remover_participante(frame)

        primeiro = self.participant_frames[0]
        primeiro.entry_nome.delete(0, "end")
        primeiro.entry_cpf.delete(0, "end")
        primeiro._validar_campo(primeiro.entry_nome)
        primeiro._validar_campo(primeiro.entry_cpf)

        if primeiro.entry_endereco:
            primeiro.entry_endereco.delete(0, "end")
            primeiro._validar_campo(primeiro.entry_endereco)
            
        self.entry_data.delete(0, "end")
        
        self.document_frame.limpar()

    @staticmethod
    def _abrir_pasta(caminho: Path) -> None:
        if os.name == "nt":
            os.startfile(caminho)
        else:
            subprocess.run(["xdg-open", str(caminho)])

    # ------------------------------------------------------------------
    # Utilitários de Seleção (Etapa 1)
    # ------------------------------------------------------------------


    def _selecionar_pasta_saida(self) -> None:
        caminho = selecionar_pasta("Selecione a pasta de saída")
        if caminho:
            self.pasta_saida = caminho
            self._atualizar_entry(self.entry_pasta_saida, str(caminho))

    def _ao_editar_pasta_saida(self) -> None:
        """Sincroniza o caminho digitado/colado no entry com self.pasta_saida."""
        texto = self.entry_pasta_saida.get().strip()
        if texto:
            p = Path(texto)
            if p.exists() and p.is_dir():
                self.pasta_saida = p
                self.entry_pasta_saida.configure(border_color=COLOR_BORDER)
            else:
                self.entry_pasta_saida.configure(border_color=COLOR_BORDER_ERROR)
        else:
            self.entry_pasta_saida.configure(border_color=COLOR_BORDER_ERROR)

    @staticmethod
    def _atualizar_entry(entry: ctk.CTkEntry, texto: str) -> None:
        entry.configure(text_color=COLOR_TEXT)
        entry.delete(0, "end")
        entry.insert(0, texto)
