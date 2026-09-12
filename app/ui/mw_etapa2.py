"""Métodos de etapa2 da janela principal (mixin de MainWindow).

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



class Etapa2Mixin:
    def _construir_etapa2(self) -> None:
        frame_header = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_header.grid(row=0, column=0, padx=SPACING_LARGE,
                          pady=(SPACING_LARGE, 0), sticky="ew")
        frame_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_header, text=" Organização de Arquivos",
            image=get_icon("folder", (20, 20)), compound="left",
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w", pady=(0, SPACING_SMALL))

        self.label_pasta_etapa2 = ctk.CTkLabel(
            frame_header, text="Pasta: ",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_pasta_etapa2.grid(row=1, column=0, sticky="w")

        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        formato = perfil.formato_saida if perfil else "PDF/A-2b"

        self.label_formato_etapa2 = ctk.CTkLabel(
            frame_header, text=f"Formato de saída: {formato}",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_formato_etapa2.grid(row=2, column=0, sticky="w")

        # Área rolável da Etapa 2 (com row 1 weight=1 no container principal)
        self.scroll_etapa2 = ctk.CTkScrollableFrame(
            self.container_etapa2, fg_color="transparent", label_text=""
        )
        self.scroll_etapa2.grid(row=1, column=0, padx=SPACING_MEDIUM, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_etapa2.grid_columnconfigure(0, weight=1)
        configurar_autoscroll(self.scroll_etapa2)

        # 1. Card de Formulários Dinâmicos do Perfil
        self.card_forms_dinamicos = ctk.CTkFrame(
            self.scroll_etapa2,
            fg_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.card_forms_dinamicos.grid(row=0, column=0, padx=SPACING_SMALL, pady=(0, SPACING_SMALL), sticky="ew")
        self.card_forms_dinamicos.grid_columnconfigure(0, weight=1)

        frame_header_forms = ctk.CTkFrame(self.card_forms_dinamicos, fg_color="transparent")
        frame_header_forms.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_SMALL, 0), sticky="ew")
        frame_header_forms.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_header_forms,
            text=" Formulários Dinâmicos Gerados",
            image=get_icon("form", (18, 18)),
            compound="left",
            font=get_font(FONT_SIZE_H3, "bold"),
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            frame_header_forms,
            text=" Gerenciar Perfis",
            image=get_icon("settings", (14, 14)),
            compound="left",
            width=140,
            height=30,
            corner_radius=RADIUS_BUTTON,
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            hover_color=COLOR_BORDER,
            font=get_font(FONT_SIZE_CAPTION, "bold"),
            command=lambda: self._mostrar_tela("perfis"),
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            self.card_forms_dinamicos,
            text="Selecione quais formulários preenchidos serão gerados e convertidos para o pacote final:",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
        ).grid(row=1, column=0, padx=SPACING_LARGE, pady=(0, SPACING_XSMALL), sticky="w")

        self.frame_checkboxes_forms = ctk.CTkFrame(self.card_forms_dinamicos, fg_color="transparent")
        self.frame_checkboxes_forms.grid(row=2, column=0, padx=SPACING_LARGE, pady=(0, SPACING_SMALL), sticky="ew")
        self.frame_checkboxes_forms.grid_columnconfigure(0, weight=1)
        self._vars_forms_dinamicos: dict[str, ctk.BooleanVar] = {}
        self._carregar_formularios_dinamicos_etapa2()

        # 2. Card de Documentos Extras
        self.card_docs_extras = ctk.CTkFrame(
            self.scroll_etapa2,
            fg_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.card_docs_extras.grid(row=1, column=0, padx=SPACING_SMALL, pady=0, sticky="ew")
        self.card_docs_extras.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.card_docs_extras, text=" Adicionar documentos extras (opcional)",
            image=get_icon("contract", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT,
        ).grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_XSMALL), sticky="w")

        ctk.CTkLabel(
            self.card_docs_extras,
            text="Arquivos selecionados aqui serão renomeados e organizados.",
            text_color=COLOR_TEXT_SECONDARY, justify="left",
            font=get_font(FONT_SIZE_BODY),
        ).grid(row=1, column=0, padx=SPACING_LARGE, pady=(0, SPACING_SMALL), sticky="w")

        self.document_frame = DocumentFrame(self.card_docs_extras, fg_color="transparent", border_width=0)
        self.document_frame.grid(row=2, column=0, padx=SPACING_SMALL, pady=(0, SPACING_XSMALL), sticky="ew")
        if perfil:
            self.document_frame.carregar_documentos(perfil.documentos_extras)

        # Botões de ação inferiores SEMPRE visíveis e ancorados na parte inferior
        frame_botoes = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_botoes.grid(row=2, column=0, padx=SPACING_LARGE,
                          pady=(SPACING_MEDIUM, SPACING_LARGE), sticky="ew")
        frame_botoes.grid_columnconfigure(1, weight=1)

        self.botao_voltar = ctk.CTkButton(
            frame_botoes, text=" Voltar",
            image=self.icon_back, compound="left",
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON, height=48,
            command=lambda: self._mostrar_tela("inicio"),
        )
        self.botao_voltar.grid(row=0, column=0, padx=(0, SPACING_MEDIUM))
        self.botao_voltar.bind("<FocusIn>", lambda e: self.botao_voltar.configure(border_width=2, border_color=get_color_primary()))
        self.botao_voltar.bind("<FocusOut>", lambda e: self.botao_voltar.configure(border_width=1, border_color=COLOR_BORDER))

        self.botao_finalizar = ctk.CTkButton(
            frame_botoes,
            text=" FINALIZAR PROCESSO",
            image=self.icon_success,
            compound="left",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            text_color="#FFFFFF",
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_finalizar,
        )
        self.botao_finalizar.grid(row=0, column=1, sticky="ew")
        self.botao_finalizar.bind("<FocusIn>", lambda e: self.botao_finalizar.configure(border_width=2, border_color="#FFFFFF"))
        self.botao_finalizar.bind("<FocusOut>", lambda e: self.botao_finalizar.configure(border_width=0))

    def _carregar_formularios_dinamicos_etapa2(self) -> None:
        """Recarrega a checklist de formulários dinâmicos baseando-se no perfil ativo."""
        if not hasattr(self, "frame_checkboxes_forms"):
            return

        for w in self.frame_checkboxes_forms.winfo_children():
            w.destroy()

        self._vars_forms_dinamicos = {}

        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        if not perfil or not perfil.formularios:
            lbl = ctk.CTkLabel(
                self.frame_checkboxes_forms,
                text="Nenhum formulário dinâmico configurado neste perfil.",
                font=get_font(FONT_SIZE_BODY),
                text_color=COLOR_TEXT_SECONDARY,
            )
            lbl.grid(row=0, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="w")
            return

        for idx, form in enumerate(perfil.formularios):
            var = ctk.BooleanVar(value=True)
            self._vars_forms_dinamicos[form.nome] = var

            tipo_desc = "Por participante" if form.geracao == "por_participante" else "Documento único"
            chk = ctk.CTkCheckBox(
                self.frame_checkboxes_forms,
                text=f" {form.nome}  ({tipo_desc})",
                variable=var,
                font=get_font(FONT_SIZE_BODY),
                text_color=COLOR_TEXT,
                fg_color=get_color_primary(),
                hover_color=get_color_primary_hover(),
                border_color=COLOR_BORDER,
                corner_radius=RADIUS_BUTTON,
            )
            chk.grid(row=idx, column=0, padx=0, pady=SPACING_XSMALL, sticky="w")

    def _ao_clicar_finalizar(self) -> None:
        if not self.pasta_saida:
            return

        forms_selecionados = [
            nome for nome, var in getattr(self, "_vars_forms_dinamicos", {}).items()
            if var.get()
        ]
        documentos_externos = self.document_frame.obter_documentos_selecionados()
        total_documentos = self.document_frame.obter_total_documentos()

        if not forms_selecionados and not documentos_externos:
            from ui.alert_modal import AlertModal
            AlertModal(
                self,
                titulo="Nenhum Documento Selecionado",
                subtitulo="Selecione ao menos um formulário dinâmico ou documento extra para finalizar.",
                erros=["Marque ao menos um formulário dinâmico ou anexe um arquivo na lista de documentos extras."],
            )
            return

        if total_documentos > 0 and len(documentos_externos) < total_documentos:
            from ui.confirm_modal import ConfirmModal
            ConfirmModal(
                self,
                titulo="Documentos Incompletos",
                subtitulo="Você não selecionou todos os documentos extras recomendados. Tem certeza de que deseja gerar apenas os documentos selecionados e finalizar o processo?",
                on_confirm=self._prosseguir_finalizar,
            )
            return
            
        self._prosseguir_finalizar()

    def _prosseguir_finalizar(self) -> None:
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        formato_saida = perfil.formato_saida if perfil else "PDF/A-2b"
        
        documentos_externos = self.document_frame.obter_documentos_selecionados()
        forms_selecionados = [
            nome for nome, var in getattr(self, "_vars_forms_dinamicos", {}).items()
            if var.get()
        ]

        # Enfileira o job no QueueManager
        job = self.queue_manager.adicionar_job(
            participantes=list(self.participantes_etapa1),
            pasta_saida=self.pasta_saida,
            documentos_externos=documentos_externos,
            forms_selecionados=forms_selecionados,
            formato_saida=formato_saida,
            perfil=perfil,
        )

        # Exibir modal de carregamento inicial com opções de Parar e Minimizar
        self._modal_fila_ativo = LoadingModal(
            self,
            message="Processando documentos...",
            submessage=f"(Etapa 1/3: {job.titulo})",
            on_cancel=lambda: self.queue_manager.cancelar_job(job.id),
            on_minimize=self._ao_minimizar_modal_fila,
        )

