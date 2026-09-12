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
from ui.mw_toolbar import ToolbarMixin
from ui.mw_stepper import StepperMixin
from ui.mw_modos import ModosMixin
from ui.mw_telas import TelasMixin
from ui.mw_layout import LayoutMixin
from ui.mw_etapa1 import Etapa1Mixin
from ui.mw_etapa2 import Etapa2Mixin
from ui.mw_fila import FilaMixin


class MainWindow(ToolbarMixin, StepperMixin, ModosMixin, TelasMixin, LayoutMixin, Etapa1Mixin, Etapa2Mixin, FilaMixin, ctk.CTk):
    def __init__(self):
        super().__init__()

        configure_appearance()

        self.title(f"Contracto v{__version__} — Preparação de Documentos")
        self.geometry("1020x880")
        self.minsize(920, 680)
        self.configure(fg_color=COLOR_BACKGROUND)

        # Maximizar aplicativo por padrão imediatamente ao iniciar
        self._maximizar_janela()
        self._maximizar_timer = self.after(10, self._maximizar_janela)
        try:
            import sys
            from utils.resource_path import caminho_recurso
            from PIL import Image, ImageTk

            icon_path = caminho_recurso("assets", "icons", "app_icon.ico")
            icon_png = caminho_recurso("assets", "icons", "app_icon.png")

            # 1. Definir iconphoto para compatibilidade geral do Tkinter
            if icon_png.exists():
                self._app_photo_icon = ImageTk.PhotoImage(Image.open(icon_png))
                self.iconphoto(True, self._app_photo_icon)

            # 2. Definir iconbitmap nativo
            if icon_path.exists():
                self.iconbitmap(str(icon_path.resolve()))

            # 3. Forçar Win32 WM_SETICON para a barra de tarefas do Windows
            if sys.platform == "win32" and icon_path.exists():
                import ctypes
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010

                abs_ico = str(icon_path.resolve())
                h_icon_big = ctypes.windll.user32.LoadImageW(None, abs_ico, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                h_icon_small = ctypes.windll.user32.LoadImageW(None, abs_ico, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()

                if h_icon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
                if h_icon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
        except Exception:
            pass

        # =============================================================
        # Gerenciador de Fila em Segundo Plano & Canal Thread-Safe
        # =============================================================
        self._ui_event_queue = queue.Queue()
        self._iniciar_loop_eventos_ui()

        self.queue_manager = QueueManager()
        self.queue_manager.on_job_started = self._ao_iniciar_job_fila
        self.queue_manager.on_job_progress = self._ao_progresso_job_fila
        self.queue_manager.on_job_completed = self._ao_concluir_job_fila
        self.queue_manager.on_job_failed = self._ao_erro_job_fila
        self.queue_manager.on_job_cancelled = self._ao_cancelado_job_fila
        self.queue_manager.on_queue_changed = self._ao_mudar_fila
        self.queue_manager.on_word_travado = self._ao_word_travar_na_fila

        self._modal_fila_ativo: Optional[LoadingModal] = None

        # =============================================================
        # Estado da Aplicação
        # =============================================================
        self.pasta_saida: Path | None = None
        self.participant_frames: list[ParticipantFrame] = []
        self.widgets_dinamicos_globais: dict[str, CampoDinamicoWidget] = {}
        self._pendencias_reveladas = False
        self._toast_pendencias_ativo = False
        self._tentativa_pendencias_id = 0
        selecao_salva = config_manager.obter("formularios_basicos_selecionados") or []
        self._perfis_simples_selecionados: list[str] = (
            list(selecao_salva) if isinstance(selecao_salva, list) else []
        )

        self.participantes_etapa1: list[Participant] = []
        self.arquivos_gerados_etapa1: list[Path] = []

        self._tela_atual = "inicio"

        # =============================================================
        # Layout Principal
        # =============================================================
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # row 0=toolbar, 1=gradient, 2=conteúdo

        self._load_icons()
        self._construir_toolbar()
        self._construir_gradiente()
        self._construir_stepper()

        # Containers principais das telas com bordas consistentes
        # Etapa 1: container estruturado responsivo com botões fixos e rolagem interna
        self.container_etapa1 = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.container_etapa1.grid_columnconfigure(0, weight=1)
        # Paginação fixa (row 0), conteúdo rolável (row 1) e ações fixas (row 2).
        self.container_etapa1.grid_rowconfigure(0, weight=0)
        self.container_etapa1.grid_rowconfigure(1, weight=1)
        self.container_etapa1.grid_rowconfigure(2, weight=0)

        # Etapa 2: container estruturado responsivo com botões fixos
        self.container_etapa2 = ctk.CTkFrame(
            self,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.container_etapa2.grid_columnconfigure(0, weight=1)
        self.container_etapa2.grid_rowconfigure(1, weight=1)

        self.container_settings = None
        self.container_profiles = None

        self._construir_etapa1()
        self._construir_etapa2()

        self._adicionar_participante(principal=True)
        self._aplicar_perfil_ativo()
        self._mostrar_tela("inicio")

        # Recarregar gradiente ao redimensionar
        self.bind("<Configure>", self._ao_redimensionar)
        
        # Tela de Boas Vindas (só na primeira execução, com a janela visível)
        self._boas_vindas_exibido = False
        if config_manager.obter("primeira_execucao"):
            self._boas_vindas_timer = self.after(500, self._abrir_boas_vindas)

    def _abrir_boas_vindas(self, tentativa: int = 0) -> None:
        """Abre o guia inicial quando a janela estiver visível (até 10 s)."""
        from ui.welcome_modal import WelcomeModal

        if self._boas_vindas_exibido or not config_manager.obter("primeira_execucao"):
            return
        try:
            visivel = self.winfo_viewable()
        except Exception:
            visivel = False
        if not visivel and tentativa < 20:
            self._boas_vindas_timer = self.after(500, lambda: self._abrir_boas_vindas(tentativa + 1))
            return
        self._boas_vindas_exibido = True
        WelcomeModal(self)

    def _maximizar_janela(self) -> None:
        """Maximiza a janela do aplicativo por padrão no Windows."""
        try:
            self.state("zoomed")
        except Exception:
            pass

    def destroy(self) -> None:
        """Encerra tarefas da interface antes de fechar a janela."""
        for janela in list(self.winfo_children()):
            if isinstance(janela, tk.Toplevel):
                try:
                    janela.destroy()
                except Exception:
                    pass
        for nome in ("_maximizar_timer", "_boas_vindas_timer", "_gradiente_timer", "_fila_timer", "_resize_timer"):
            timer = getattr(self, nome, None)
            if timer:
                try:
                    self.after_cancel(timer)
                except Exception:
                    pass
        super().destroy()

    # ==================================================================
    # TOOLBAR & STATUS DE FILA
    # ==================================================================



    # ==================================================================
    # GRADIENTE DE FUNDO
    # ==================================================================

    _bg_photo = None
    _bg_cache_key = None
    _bg_item_id = None


    _ultimo_w = 0
    _ultimo_h = 0
    _resize_timer = None


    # ==================================================================
    # STEPPER (indicador de etapas)
    # ==================================================================









    # ==================================================================
    # NAVEGAÇÃO ENTRE TELAS
    # ==================================================================


























    # ------------------------------------------------------------------
    # ETAPA 1: Preenchimento e Validação (Estrutura Responsiva e Flexível)
    # ------------------------------------------------------------------


















    # ------------------------------------------------------------------
    # ETAPA 2: Documentos da Gerente e PDF/A (Layout Responsivo)
    # ------------------------------------------------------------------


        



    # ------------------------------------------------------------------
    # Callbacks da Fila de Background
    # ------------------------------------------------------------------
    # Callbacks da Fila de Background (Thread-Safe via Queue)
    # ------------------------------------------------------------------


















    # ------------------------------------------------------------------
    # Utilitários de Seleção (Etapa 1)
    # ------------------------------------------------------------------


