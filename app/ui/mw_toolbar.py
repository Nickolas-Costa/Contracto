"""Métodos de toolbar da janela principal (mixin de MainWindow).

Movido verbatim de `app/ui/main_window.py`: mesma ordem, mesmo código,
sem mudança de comportamento. A classe `MainWindow` herda este mixin.
"""

"""
Janela principal da aplicação Contracto.

Implementa a navegação entre telas (Início, Perfis, Configurações),
o gradiente de fundo inspirado no PDFCreator, a fila de processamento
em segundo plano (com suporte a minimizar para a toolbar), e a integração
com o sistema de perfis e configurações.
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk
from PIL import Image

from models.participant import Participant
from services.field_calculator import calcular
from services.generator_service import gerar_documentos, validar_antes_de_gerar
from services.profile_composer import combinar_perfis, limite_participantes_para_pagina
from services.pdf_service import PdfServiceError
from services.pdfa_converter import ProcessoCanceladoError
from services.queue_manager import ProcessJob, QueueManager
from services.stage2_service import ResultadoEtapa2, executar_etapa2
from ui.animated_loader import CanvasSpinner
from ui.alert_modal import AlertModal
from ui.campo_dinamico_widget import CampoDinamicoWidget
from ui.date_picker import DatePickerPopup
from ui.document_frame import DocumentFrame
from ui.feedback_toast import show_toast
from ui.loading_modal import LoadingModal
from ui.participant_frame import ParticipantFrame
from ui.profiles_frame import ProfilesFrame
from ui.settings_frame import SettingsFrame
from ui.theme import (
    COLOR_BACKGROUND, COLOR_BORDER, COLOR_BORDER_ERROR, COLOR_ERROR, COLOR_SUCCESS,
    COLOR_SURFACE, COLOR_SURFACE_VARIANT, COLOR_TEXT, COLOR_TEXT_DISABLED,
    COLOR_TEXT_SECONDARY, COLOR_WARNING,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XXLARGE,
    SPACING_XSMALL,
    aplicar_gradiente, configurar_autoscroll, configure_appearance, get_color_primary,
    get_color_primary_dark_gradient, get_color_primary_hover, get_color_primary_light,
    get_color_primary_text, get_font, get_icon, reload_theme, rolar_para_widget_se_necessario,
    icone_para_secao, configurar_janela_modal,
)
from utils import config_manager
from utils.caminhos import pasta_downloads
from utils.date_formatter import validar_data
from utils.document_validator import formatar_data_progressiva
from ports.dialog import selecionar_pasta
from utils.logger import configurar_logger, obter_logger
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil, carregar_perfis, listar_nomes_perfis,
    listar_perfis_por_modo, listar_nomes_perfis_por_modo, obter_perfil,
)
from version import __version__



class ToolbarMixin:
    def _load_icons(self) -> None:
        self.icon_home = get_icon("home", (20, 20), light_only=True)
        self.icon_profiles = get_icon("profiles", (20, 20), light_only=True)
        self.icon_settings = get_icon("settings", (20, 20), light_only=True)
        self.icon_calendar = get_icon("calendar", (18, 18))
        self.icon_help = get_icon("question_circle", (20, 20), light_only=True)
        self.icon_advance = get_icon("advance", (20, 20), light_only=True)
        self.icon_contract = get_icon("contract", (20, 20), light_only=True)
        self.icon_back = get_icon("back", (18, 18))
        self.icon_success = get_icon("finish", (20, 20), light_only=True)
        self.icon_folder = get_icon("folder", (18, 18))
        self.icon_add_user = get_icon("user_add", (18, 18))
        self.icon_queue = get_icon("finish", (16, 16), light_only=True)

    def _construir_toolbar(self) -> None:
        self.toolbar = ctk.CTkFrame(self, fg_color=get_color_primary(),
                                     corner_radius=0, height=48)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_columnconfigure(5, weight=1)  # spacer between left and right groups

        # Nome oficial por extenso na barra superior
        ctk.CTkLabel(
            self.toolbar, text=" Contracto",
            font=get_font(FONT_SIZE_H2, "bold"), text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL)

        # Separador vertical entre logo e navegação
        self.sep1 = ctk.CTkFrame(self.toolbar, width=1, height=28, fg_color=get_color_primary_hover(), corner_radius=0)
        self.sep1.grid(row=0, column=1, padx=(SPACING_SMALL, SPACING_SMALL))

        # Botões de navegação com estilo consistente
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

        # Seletor de Modo na TopBar (Simples | Avançado)
        modo_atual = config_manager.obter("modo_operacao") or "avancado"

        frame_switch = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        frame_switch.grid(row=0, column=4, padx=(SPACING_SMALL, SPACING_SMALL), pady=SPACING_XSMALL, sticky="w")

        ctk.CTkLabel(
            frame_switch, text="Modo:",
            font=get_font(FONT_SIZE_CAPTION, "bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=(0, SPACING_XSMALL))

        self.frame_switch_bg = ctk.CTkFrame(
            frame_switch,
            fg_color="transparent",
            corner_radius=0,
            height=30,
        )
        self.frame_switch_bg.pack(side="left")

        self.btn_modo_simples = ctk.CTkButton(
            self.frame_switch_bg,
            text="Simples",
            width=70,
            height=26,
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION, "bold"),
            command=lambda: self._ao_alterar_modo_operacao("simples"),
        )
        self.btn_modo_simples.pack(side="left", padx=2, pady=2)

        self.btn_modo_avancado = ctk.CTkButton(
            self.frame_switch_bg,
            text="Avançado",
            width=76,
            height=26,
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION, "bold"),
            command=lambda: self._ao_alterar_modo_operacao("avancado"),
        )
        self.btn_modo_avancado.pack(side="left", padx=2, pady=2)

        self._atualizar_botoes_modo(modo_atual)

        # Spacer (coluna 5)

        # Botão de Status da Fila em Segundo Plano (à esquerda do botão Ajuda)
        self.btn_fila_status = ctk.CTkButton(
            self.toolbar,
            text=" FILA: Ociosa",
            image=self.icon_queue,
            compound="left",
            width=150,
            height=32,
            fg_color=get_color_primary_hover(),
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION, "bold"),
            text_color="#FFFFFF",
            command=self._abrir_modal_fila,
        )
        self.btn_fila_status.grid(row=0, column=6, padx=(SPACING_SMALL, SPACING_SMALL), pady=SPACING_XSMALL)
        self.btn_fila_status.grid_remove()  # Oculto por padrão

        # Separador vertical antes dos botões de ajuda e config
        self.sep2 = ctk.CTkFrame(self.toolbar, width=1, height=28, fg_color=get_color_primary_hover(), corner_radius=0)
        self.sep2.grid(row=0, column=7, padx=(SPACING_SMALL, SPACING_SMALL))

        self.btn_ajuda = ctk.CTkButton(
            self.toolbar, text=" Ajuda", image=self.icon_help, width=95,
            command=self._abrir_ajuda, **btn_style,
        )
        self.btn_ajuda.grid(row=0, column=8, padx=3, pady=SPACING_XSMALL)

        self.btn_config = ctk.CTkButton(
            self.toolbar, text=" Configurações", image=self.icon_settings, width=140,
            command=lambda: self._mostrar_tela("config"), **btn_style,
        )
        self.btn_config.grid(row=0, column=9, padx=(3, SPACING_LARGE), pady=SPACING_XSMALL)

    def _abrir_ajuda(self) -> None:
        """Abre o guia interativo de uso do aplicativo."""
        from ui.welcome_modal import WelcomeModal
        WelcomeModal(self)

    def _atualizar_botoes_modo(self, modo: str) -> None:
        """Atualiza o estilo visual dos botões do seletor de modo com o quadro arredondado ativo."""
        if not hasattr(self, "btn_modo_simples") or not hasattr(self, "btn_modo_avancado"):
            return

        is_simples = (modo == "simples")
        cor_destaque = get_color_primary_hover()

        if is_simples:
            self.btn_modo_simples.configure(
                fg_color=cor_destaque,
                hover_color=cor_destaque,
                text_color="#FFFFFF",
                border_width=1,
                border_color="#FFFFFF",
                corner_radius=RADIUS_BUTTON,
            )
            self.btn_modo_avancado.configure(
                fg_color="transparent",
                hover_color=get_color_primary_hover(),
                text_color="#CBD5E1",
                border_width=0,
                corner_radius=RADIUS_BUTTON,
            )
        else:
            self.btn_modo_avancado.configure(
                fg_color=cor_destaque,
                hover_color=cor_destaque,
                text_color="#FFFFFF",
                border_width=1,
                border_color="#FFFFFF",
                corner_radius=RADIUS_BUTTON,
            )
            self.btn_modo_simples.configure(
                fg_color="transparent",
                hover_color=get_color_primary_hover(),
                text_color="#CBD5E1",
                border_width=0,
                corner_radius=RADIUS_BUTTON,
            )

