"""Métodos de stepper da janela principal (mixin de MainWindow).

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
from pathlib import Path
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



class StepperMixin:
    def _construir_stepper(self) -> None:
        # Fundo opaco: rótulos transparentes do CustomTkinter podem deixar rastros
        # sobre o canvas ao alternar modo, etapa ou tema.
        self.frame_stepper = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND,
                                           corner_radius=0, height=36)
        self.frame_stepper.grid(row=1, column=0, sticky="ew")
        self.frame_stepper.grid_columnconfigure(0, weight=1)
        self.frame_stepper.grid_columnconfigure(2, weight=1)
        self.frame_stepper.lift()

        self.lbl_etapa1 = ctk.CTkLabel(
            self.frame_stepper, text=" 1. Geração de Documentos",
            image=get_icon("document", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=get_color_primary_text()
        )
        self.lbl_etapa1.grid(row=0, column=0, pady=SPACING_MEDIUM, sticky="e", padx=SPACING_MEDIUM)

        self.lbl_seta = ctk.CTkLabel(
            self.frame_stepper, text="  →  ",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED,
        )
        self.lbl_seta.grid(row=0, column=1, pady=SPACING_MEDIUM)

        self.lbl_etapa2 = ctk.CTkLabel(
            self.frame_stepper, text=" 2. Conversão e Organização",
            image=get_icon("folder", (16, 16)), compound="left",
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

        self.label_seletor_perfil = ctk.CTkLabel(
            frame_perfil_row, text=" Perfil:",
            image=get_icon("profiles", (15, 15)), compound="left",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_seletor_perfil.pack(side="left", padx=(0, SPACING_XSMALL))

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

        self.btn_selecionar_formularios = ctk.CTkButton(
            frame_perfil_row,
            text="Selecionar formulários",
            image=get_icon("check", (14, 14), light_only=True),
            compound="left",
            width=190,
            height=28,
            corner_radius=RADIUS_BUTTON,
            fg_color=get_color_primary(),
            hover_color=get_color_primary_hover(),
            command=self._abrir_seletor_formularios_basicos,
        )
        self.btn_selecionar_formularios.pack_forget()

    def _atualizar_stepper(self, etapa: int) -> None:
        modo = config_manager.obter("modo_operacao") or "avancado"
        is_simples = (modo == "simples")

        if is_simples:
            self.lbl_seta.grid_forget()
            self.lbl_etapa2.grid_forget()
            self.lbl_etapa1.configure(
                text=" Emissão de Formulário Único",
                text_color=get_color_primary_text(),
            )
            self.lbl_etapa1.grid(row=0, column=0, columnspan=3, pady=SPACING_MEDIUM, sticky="n")
        else:
            self.lbl_etapa1.configure(
                text=" 1. Geração de Documentos",
                text_color=get_color_primary_text() if etapa == 1 else COLOR_TEXT_DISABLED,
            )
            self.lbl_etapa1.grid(row=0, column=0, columnspan=1, pady=SPACING_MEDIUM, sticky="e", padx=SPACING_MEDIUM)
            self.lbl_seta.grid(row=0, column=1, columnspan=1, pady=SPACING_MEDIUM)
            self.lbl_etapa2.configure(
                text=" 2. Conversão e Organização",
                text_color=get_color_primary_text() if etapa == 2 else COLOR_TEXT_DISABLED,
            )
            self.lbl_etapa2.grid(row=0, column=2, columnspan=1, pady=SPACING_MEDIUM, sticky="w", padx=SPACING_MEDIUM)

            if hasattr(self, "botao_adicionar"):
                self.botao_adicionar.grid(row=3, column=0, padx=0, pady=(SPACING_LARGE, 0), sticky="w")

        nomes_perfis = listar_nomes_perfis_por_modo(modo)
        perfil_nome = config_manager.obter("perfil_ativo") or (nomes_perfis[0] if nomes_perfis else PERFIL_PADRAO_NOME)
        if nomes_perfis:
            self.dropdown_perfil.configure(values=nomes_perfis)
        self.dropdown_perfil.set(perfil_nome)
        if is_simples:
            self.dropdown_perfil.pack_forget()
            self.label_seletor_perfil.configure(text=" Formulários:")
            self.btn_selecionar_formularios.pack(side="left")
            self._atualizar_seletor_formularios_basicos()
        else:
            self.btn_selecionar_formularios.pack_forget()
            self.label_seletor_perfil.configure(text=" Perfil:")
            self.dropdown_perfil.pack(side="left")

