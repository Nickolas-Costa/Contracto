"""Métodos de telas da janela principal (mixin de MainWindow).

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



class TelasMixin:
    def _mostrar_tela(self, tela: str) -> None:
        """Alterna entre as telas: inicio, perfis, config."""
        self.frame_stepper.grid_forget()
        self.container_etapa1.grid_forget()
        self.container_etapa2.grid_forget()
        if self.container_settings:
            self.container_settings.grid_forget()
        if self.container_profiles:
            self.container_profiles.grid_forget()

        # Conclui a remoção da tela anterior antes de desenhar a seguinte. Isso
        # evita resíduos de frames transparentes sem acrescentar trabalho ao scroll.
        self.update_idletasks()

        normal = {"fg_color": "transparent", "text_color": "#FFFFFF"}
        active = {"fg_color": get_color_primary_hover(), "text_color": "#FFFFFF"}
        self.btn_inicio.configure(**normal)
        self.btn_perfis.configure(**normal)
        self.btn_config.configure(**normal)

        self._tela_atual = tela
        margem_h = self._calcular_margem_responsiva()
        margem_v = self._calcular_padding_vertical_responsivo()

        card_grid = {"row": 2, "column": 0, "sticky": "nsew", "padx": margem_h, "pady": (0, margem_v)}

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
            self._aplicar_perfil_ativo()
        elif tela == "perfis":
            self.btn_perfis.configure(**active)
            self.frame_stepper.grid_forget()
            if not self.container_profiles:
                self.container_profiles = ProfilesFrame(
                    self,
                    on_voltar=lambda: self._mostrar_tela("inicio"),
                    on_expand=self._redimensionar_container_perfis,
                )
                self.container_profiles.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD)
            else:
                self.container_profiles._carregar_lista()
            self._redimensionar_container_perfis(False)
        elif tela == "config":
            self.btn_config.configure(**active)
            self.frame_stepper.grid_forget()
            if not self.container_settings:
                self.container_settings = SettingsFrame(
                    self,
                    on_voltar=lambda: self._mostrar_tela("inicio"),
                    on_aplicar=self._ao_aplicar_config,
                )
                self.container_settings.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD)
            else:
                self.container_settings.recarregar_campos()
            self.container_settings.grid(**card_grid)

    def _redimensionar_container_perfis(self, expandir: bool = True) -> None:
        """Redimensiona o quadro do container de perfis (ocupando todo o espaço vertical)."""
        if not self.container_profiles:
            return

        margem_h = self._calcular_margem_responsiva()
        margem_v = self._calcular_padding_vertical_responsivo()
        self.container_profiles.grid(row=2, column=0, sticky="nsew", padx=margem_h, pady=(0, margem_v))

    def _ao_aplicar_config(self) -> None:
        """Aplica as alterações de configurações e tema instantaneamente em toda a interface."""
        try:
            # 1. Recarregar variáveis de tema e modo de aparência
            reload_theme()
            configure_appearance()

            # 2. Atualizar todos os componentes da janela de uma só vez
            self.toolbar.configure(fg_color=get_color_primary())
            if hasattr(self, 'sep1'):
                self.sep1.configure(fg_color=get_color_primary_hover())
            if hasattr(self, 'sep2'):
                self.sep2.configure(fg_color=get_color_primary_hover())

            for btn in (self.btn_inicio, self.btn_perfis, self.btn_config, self.btn_ajuda):
                try:
                    btn.configure(hover_color=get_color_primary_hover())
                except Exception:
                    pass

            if hasattr(self, 'btn_fila_status'):
                self.btn_fila_status.configure(
                    fg_color=get_color_primary_hover(),
                    hover_color=get_color_primary_hover()
                )

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
            if hasattr(self, 'botao_voltar'):
                self.botao_voltar.configure(
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
                    border_color=get_color_primary_text()
                )

            # Atualizar seletor de modo
            modo_atual = config_manager.obter("modo_operacao") or "avancado"
            self._atualizar_botoes_modo(modo_atual)

            # Atualizar checkbox de preservação de dados
            if hasattr(self, "chk_preservar_dados"):
                self.chk_preservar_dados.configure(
                    fg_color=get_color_primary(),
                    hover_color=get_color_primary_hover()
                )

            # Atualizar subtítulos globais
            if hasattr(self, "_subtitulos_labels"):
                for lbl in self._subtitulos_labels:
                    try:
                        lbl.configure(text_color=get_color_primary_text())
                    except Exception:
                        pass

            # Atualizar widgets dinâmicos globais (como checkboxes de tarifas)
            for w in self.widgets_dinamicos_globais.values():
                if hasattr(w, "atualizar_cores"):
                    w.atualizar_cores()
            
            # Atualizar frames de participantes
            if hasattr(self, 'participant_frames'):
                for pf in self.participant_frames:
                    pf.atualizar_cores()
                
            self._pintar_gradiente()
            self._atualizar_stepper(1 if self._tela_atual == "inicio" else 2 if self._tela_atual == "etapa2" else 1)
            
            if self._tela_atual == "config" and getattr(self, 'container_settings', None) is not None:
                self.container_settings.recarregar_campos()
            elif getattr(self, 'container_settings', None) is not None:
                self.container_settings.atualizar_cores()
                
            if getattr(self, 'container_profiles', None) is not None:
                self.container_profiles.atualizar_cores()
            
            if hasattr(self, 'entry_local'):
                self.entry_local.delete(0, 'end')
                self.entry_local.insert(0, config_manager.obter("local_padrao") or "CAMOCIM-CE")
            
            # Re-aplicar estado ativo dos botões da toolbar para atualizar a cor do botão ativo
            self._mostrar_tela(self._tela_atual)

            self._atualizar_tamanho_janela()
            self.update_idletasks()
            show_toast(self, "Configurações salvas e aplicadas com sucesso!", "success")
        except Exception as e:
            obter_logger("ui").error(f"Erro ao aplicar configurações: {e}", exc_info=True)

