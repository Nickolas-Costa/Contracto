"""Métodos de layout da janela principal (mixin de MainWindow).

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



class LayoutMixin:
    def _construir_gradiente(self) -> None:
        self.canvas_gradient = tk.Canvas(self, highlightthickness=0)
        self.canvas_gradient.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.canvas_gradient.tk.call('lower', self.canvas_gradient._w)
        self._gradiente_timer = self.after(20, self._pintar_gradiente)

    def _pintar_gradiente(self) -> None:
        try:
            sw = max(self.winfo_screenwidth(), 1920)
            sh = max(self.winfo_screenheight(), 1080)
        except Exception:
            sw, sh = 1920, 1080

        largura = sw
        altura = sh
        modo = ctk.get_appearance_mode()
        is_dark = (modo == "Dark")
        cor_primaria = get_color_primary()
        
        bg_main = COLOR_BACKGROUND[1] if is_dark else COLOR_BACKGROUND[0]
        self.configure(fg_color=bg_main)
        if hasattr(self, 'canvas_gradient'):
            self.canvas_gradient.configure(bg=bg_main)

        cache_key = (is_dark, cor_primaria, largura, altura)
        if self._bg_photo is not None and self._bg_cache_key == cache_key:
            return
        
        import math
        from PIL import Image, ImageDraw, ImageTk

        # Renderização direta em 1x com PIL (ultra rápida: < 2ms, zero CPU lag)
        img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        line_color = "#242730" if is_dark else "#EAEFF5"
        line_accent = "#2B2E38" if is_dark else "#DFE4EE"
        
        destaque_indices = {6, 17, 26}
        cor_destaque_linha = get_color_primary_light() if is_dark else get_color_primary()
        
        num_linhas = 30
        for i in range(num_linhas):
            y_offset = (i - 5) * (altura / 18.0)
            points = []
            steps = 60
            for s in range(steps + 1):
                x = (s / steps) * largura
                y = y_offset + (x * 0.28) + math.sin(s * 0.14 + i * 0.22) * (altura * 0.05)
                points.append((x, y))
                
            if i in destaque_indices:
                cor = cor_destaque_linha
                w = 2
            else:
                cor = line_accent if i % 3 == 0 else line_color
                w = 1
                
            draw.line(points, fill=cor, width=w, joint="curve")
            
        nova_foto = ImageTk.PhotoImage(img)
        self._bg_photo = nova_foto
        self._bg_cache_key = cache_key
        
        if hasattr(self, 'canvas_gradient'):
            novo_item = self.canvas_gradient.create_image(0, 0, image=self._bg_photo, anchor="nw")
            if self._bg_item_id is not None:
                try:
                    self.canvas_gradient.delete(self._bg_item_id)
                except Exception:
                    pass
            self._bg_item_id = novo_item

    def _ao_redimensionar(self, event=None) -> None:
        """Garante fluidez máxima e adaptação automática de largura aos snaps de tela."""
        if event and getattr(event, 'widget', None) != self:
            return
        try:
            w = self.winfo_width()
        except Exception:
            return
        if w != self._ultimo_w:
            self._ultimo_w = w
            if self._resize_timer is not None:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(30, self._atualizar_tamanho_janela)

    def _calcular_margem_responsiva(self) -> int:
        """Calcula a margem lateral (padx) proporcional e responsiva para os quadros."""
        try:
            largura = self.winfo_width()
        except Exception:
            largura = 1200

        if largura <= 100:
            largura = 1200
            
        tamanho = config_manager.obter("tamanho_quadros")
        
        # Percentuais e limites de acordo com a preferência do usuário
        if tamanho == "Pequeno":
            pct = 0.18
            min_m = 24
            max_m = 320
        elif tamanho == "Grande":
            pct = 0.05
            min_m = 16
            max_m = 90
        else:
            pct = 0.10
            min_m = 20
            max_m = 200

        # Valores de base por faixa de resolução:
        if largura < 960:
            # Telas pequenas / compactas (< 960px): foco em aproveitamento máximo
            margem = max(16, int(largura * 0.03))
        elif largura <= 1366:
            # Telas médias (notebooks padrão 1366x768 / 1080p escalados a 125%/150%)
            margem = max(min_m, min(max_m, int(largura * pct)))
        elif largura <= 1920:
            # Telas grandes (Full HD 1080p sem escala)
            margem = max(min_m, min(max_m + 40, int(largura * pct)))
        else:
            # Telas ultrawide / 2K / 4K (> 1920px): trava em largura confortável (1150px)
            largura_card_alvo = 1150
            margem = max(min_m, int((largura - largura_card_alvo) / 2))

        return margem

    def _calcular_padding_vertical_responsivo(self) -> int:
        """Calcula o padding vertical do cartão baseado na altura da janela."""
        try:
            altura = self.winfo_height()
        except Exception:
            altura = 800

        if altura < 720:
            return SPACING_SMALL
        elif altura < 900:
            return SPACING_MEDIUM
        else:
            return SPACING_LARGE

    def _atualizar_tamanho_janela(self) -> None:
        margem_h = self._calcular_margem_responsiva()
        margem_v = self._calcular_padding_vertical_responsivo()
            
        if self._tela_atual == "inicio" and hasattr(self, 'container_etapa1'):
            self.container_etapa1.grid(padx=margem_h, pady=(0, margem_v), sticky="nsew")
        elif self._tela_atual == "etapa2" and hasattr(self, 'container_etapa2'):
            self.container_etapa2.grid(padx=margem_h, pady=(0, margem_v), sticky="nsew")
        elif self._tela_atual == "perfis" and hasattr(self, 'container_profiles') and self.container_profiles:
            self.container_profiles.grid(padx=margem_h, pady=(0, margem_v), sticky="nsew")
        elif self._tela_atual == "config" and hasattr(self, 'container_settings') and self.container_settings:
            self.container_settings.grid(padx=margem_h, pady=(0, margem_v), sticky="nsew")
        
        self.update_idletasks()

    def _criar_subtitulo_secao(self, master, titulo: str) -> ctk.CTkFrame:
        """Cria um cabeçalho/subtítulo elegante com ícone e linha divisória sutil."""
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        icone = icone_para_secao(titulo)

        header_box = ctk.CTkFrame(frame, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=SPACING_LARGE, pady=(SPACING_MEDIUM, 2))

        lbl = ctk.CTkLabel(
            header_box,
            text=f" {titulo}",
            image=get_icon(icone, (15, 15)),
            compound="left",
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=get_color_primary_text(),
        )
        lbl.pack(side="left")
        if not hasattr(self, "_subtitulos_labels"):
            self._subtitulos_labels = []
        self._subtitulos_labels.append(lbl)

        linha = ctk.CTkFrame(frame, height=1, fg_color=COLOR_BORDER)
        linha.grid(row=1, column=0, sticky="ew", padx=SPACING_LARGE, pady=(2, SPACING_XSMALL))

        return frame

