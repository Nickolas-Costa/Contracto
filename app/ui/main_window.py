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


class MainWindow(ctk.CTk):
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
        self.bind("<FocusIn>", self._recuperar_interacao_campos, add="+")
        
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

    def _recuperar_interacao_campos(self, event=None) -> None:
        """Recupera entradas após um popup do Windows/Tk perder a captura de foco."""
        try:
            captura = self.grab_current()
            if captura is not None:
                estado = captura.state() if hasattr(captura, "state") else "normal"
                if not captura.winfo_exists() or estado == "withdrawn":
                    captura.grab_release()
        except Exception:
            pass

        entradas = []
        for participante in getattr(self, "participant_frames", []):
            entradas.extend((participante.entry_nome, participante.entry_cpf))
        for nome in ("entry_data", "entry_local", "entry_pasta_saida"):
            entrada = getattr(self, nome, None)
            if entrada is not None:
                entradas.append(entrada)

        for entrada in entradas:
            try:
                if entrada.winfo_exists() and entrada.cget("state") == "disabled":
                    entrada.configure(state="normal")
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

    # ==================================================================
    # GRADIENTE DE FUNDO
    # ==================================================================
    def _construir_gradiente(self) -> None:
        self.canvas_gradient = tk.Canvas(self, highlightthickness=0)
        self.canvas_gradient.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.canvas_gradient.tk.call('lower', self.canvas_gradient._w)
        self._gradiente_timer = self.after(20, self._pintar_gradiente)

    _bg_photo = None
    _bg_cache_key = None
    _bg_item_id = None

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

    _ultimo_w = 0
    _ultimo_h = 0
    _resize_timer = None

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

    # ==================================================================
    # STEPPER (indicador de etapas)
    # ==================================================================
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

    def _obter_perfis_basicos_selecionados(self) -> list[Perfil]:
        """Devolve os perfis marcados no modo simples (chave estável `identificador`, com migração do formato antigo por nome)."""
        disponiveis = listar_perfis_por_modo("simples")
        por_chave = {(perfil.identificador or perfil.nome): perfil for perfil in disponiveis}
        por_nome = {perfil.nome: perfil for perfil in disponiveis}
        selecionados = [
            por_chave[chave]
            for chave in self._perfis_simples_selecionados
            if chave in por_chave
        ]
        if not selecionados:
            selecionados = [por_nome[nome] for nome in self._perfis_simples_selecionados if nome in por_nome]
            if selecionados:
                self._perfis_simples_selecionados = [perfil.identificador or perfil.nome for perfil in selecionados]
                config_manager.definir("formularios_basicos_selecionados", self._perfis_simples_selecionados)
        if not selecionados and disponiveis:
            nome_ativo = config_manager.obter("perfil_ativo") or ""
            selecionados = [por_nome.get(nome_ativo) or disponiveis[0]]
            self._perfis_simples_selecionados = [selecionados[0].identificador or selecionados[0].nome]
        return selecionados

    def _obter_perfil_em_uso(self) -> Optional[Perfil]:
        """No modo simples combina os perfis marcados; no avançado usa o perfil ativo."""
        modo = config_manager.obter("modo_operacao") or "avancado"
        if modo == "simples":
            resultado = combinar_perfis(self._obter_perfis_basicos_selecionados())
            return resultado.perfil
        nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        return obter_perfil(nome)

    def _atualizar_seletor_formularios_basicos(self) -> None:
        """Atualiza o rótulo do botão com a quantidade de formulários marcados."""
        if not hasattr(self, "btn_selecionar_formularios"):
            return
        perfis = self._obter_perfis_basicos_selecionados()
        nomes = [perfil.nome for perfil in perfis]
        if not nomes:
            texto = "✓ Selecionar formulários"
        elif len(nomes) <= 2:
            texto = "✓ " + " + ".join(nomes)
        else:
            texto = f"✓ {len(nomes)} formulários: {nomes[0]}, {nomes[1]} e mais"
        self.btn_selecionar_formularios.configure(text=texto, width=260)

    def _abrir_seletor_formularios_basicos(self) -> None:
        """Abre o modal de checkboxes para marcar os formulários do modo simples."""
        perfis = listar_perfis_por_modo("simples")
        if not perfis:
            AlertModal(self, "Nenhum Formulário", "Não há formulários no modo simples.")
            return

        overlay = ctk.CTkToplevel(self)
        modal = ctk.CTkToplevel(self)
        altura = min(720, max(430, 270 + len(perfis) * 62))
        configurar_janela_modal(self, modal, overlay, 620, altura)

        painel = ctk.CTkFrame(
            modal, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
            border_width=1, border_color=COLOR_BORDER,
        )
        painel.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            painel, text="Selecionar formulários", font=get_font(FONT_SIZE_H2, "bold"),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, 2))
        ctk.CTkLabel(
            painel,
            text="Escolha um ou mais documentos. Os campos serão agrupados por formulário.",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(0, SPACING_MEDIUM))

        barra_selecao = ctk.CTkFrame(painel, fg_color="transparent")
        barra_selecao.pack(fill="x", padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
        barra_selecao.grid_columnconfigure(0, weight=1)

        acoes_selecao = ctk.CTkFrame(barra_selecao, fg_color="transparent")
        acoes_selecao.grid(row=0, column=0, sticky="e")
        label_quantidade = ctk.CTkLabel(
            barra_selecao, text="", font=get_font(FONT_SIZE_CAPTION, "bold"),
            text_color=get_color_primary_text(), justify="left", anchor="w",
            wraplength=520,
        )
        label_quantidade.grid(
            row=1, column=0, sticky="ew", pady=(SPACING_XSMALL, 0)
        )

        lista = ctk.CTkScrollableFrame(painel, fg_color=COLOR_SURFACE_VARIANT)
        lista.pack(fill="both", expand=True, padx=SPACING_LARGE, pady=(0, SPACING_MEDIUM))
        lista.grid_columnconfigure(0, weight=1)
        configurar_autoscroll(lista)
        nomes_atuais = set(self._perfis_simples_selecionados)
        variaveis: dict[str, ctk.BooleanVar] = {}
        for linha, perfil in enumerate(perfis):
            chave = perfil.identificador or perfil.nome
            var = ctk.BooleanVar(value=chave in nomes_atuais or perfil.nome in nomes_atuais)
            variaveis[chave] = var
            item = ctk.CTkFrame(lista, fg_color="transparent")
            item.grid(row=linha, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            item.grid_columnconfigure(0, weight=1)
            ctk.CTkCheckBox(
                item, text=perfil.nome, variable=var, font=get_font(FONT_SIZE_BODY, "bold"),
                fg_color=get_color_primary(), hover_color=get_color_primary_hover(),
                command=lambda: atualizar_resumo(),
            ).grid(row=0, column=0, padx=SPACING_SMALL, pady=(SPACING_SMALL, 1), sticky="w")
            total_campos = len(perfil.campos_entrada)
            total_paginas = len(perfil.obter_abas_disponiveis()) if perfil.usar_paginacao else 1
            regra_participantes = (
                "somente proponente principal"
                if perfil.max_participantes == 1
                else f"até {perfil.max_participantes} proponentes"
            )
            ctk.CTkLabel(
                item,
                text=(
                    f"{total_campos} campos  •  {total_paginas} página(s)"
                    f"  •  {regra_participantes}"
                ),
                font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
            ).grid(row=1, column=0, padx=(42, SPACING_SMALL), pady=(0, SPACING_SMALL), sticky="w")

        def fechar():
            try:
                modal.destroy()
            except Exception:
                pass
            try:
                overlay.destroy()
            except Exception:
                pass

        def aplicar():
            escolhidos = [
                perfil for perfil in perfis
                if variaveis[perfil.identificador or perfil.nome].get()
            ]
            if not escolhidos:
                AlertModal(modal, "Seleção necessária", "Marque ao menos um formulário para continuar.")
                return
            resultado = combinar_perfis(escolhidos)
            if resultado.erros:
                AlertModal(
                    modal, "Configurações Incompatíveis",
                    "Alguns campos precisam ser ajustados antes de combinar os formulários.",
                    resultado.erros,
                )
                return
            self._perfis_simples_selecionados = [perfil.identificador or perfil.nome for perfil in escolhidos]
            config_manager.definir("formularios_basicos_selecionados", self._perfis_simples_selecionados)
            config_manager.definir("perfil_ativo", escolhidos[0].nome)
            self._atualizar_seletor_formularios_basicos()
            self._aplicar_perfil_ativo()
            fechar()
            show_toast(self, f"{len(escolhidos)} formulário(s) selecionado(s).", "success")

        botoes = ctk.CTkFrame(painel, fg_color="transparent")
        botoes.pack(fill="x", padx=SPACING_LARGE, pady=(0, SPACING_LARGE))
        botoes.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(
            acoes_selecao, text="Selecionar todos", width=110,
            fg_color="transparent", text_color=get_color_primary_text(),
            hover_color=COLOR_SURFACE_VARIANT,
            command=lambda: alterar_todos(True),
        ).pack(side="right", padx=(SPACING_SMALL, 0))
        ctk.CTkButton(
            acoes_selecao, text="Limpar", width=70,
            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
            hover_color=COLOR_SURFACE_VARIANT,
            command=lambda: alterar_todos(False),
        ).pack(side="right")
        ctk.CTkButton(
            botoes, text="Cancelar", fg_color=COLOR_SURFACE_VARIANT,
            text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=fechar,
        ).grid(row=0, column=0, padx=(0, SPACING_SMALL))
        btn_aplicar = ctk.CTkButton(botoes, text="Aplicar seleção", command=aplicar)
        btn_aplicar.grid(
            row=0, column=2, sticky="ew"
        )

        def atualizar_resumo() -> None:
            escolhidos = [
                perfil for perfil in perfis
                if variaveis[perfil.identificador or perfil.nome].get()
            ]
            quantidade = len(escolhidos)
            limites = {perfil.max_participantes for perfil in escolhidos}
            if len(limites) > 1:
                detalhe = " • regras de proponentes serão respeitadas em cada formulário"
            elif limites == {1}:
                detalhe = " • somente proponente principal"
            elif limites:
                detalhe = f" • até {max(limites)} proponentes"
            else:
                detalhe = ""
            label_quantidade.configure(
                text=f"{quantidade} formulário(s) selecionado(s){detalhe}"
            )
            btn_aplicar.configure(state="normal" if quantidade else "disabled")

        def alterar_todos(selecionar: bool) -> None:
            for var in variaveis.values():
                var.set(selecionar)
            atualizar_resumo()

        atualizar_resumo()
        overlay.bind("<Button-1>", lambda _evento: fechar())
        modal.bind("<Escape>", lambda _evento: fechar())

    def _ao_alterar_modo_operacao(self, modo_str: str) -> None:
        """Alterna entre o modo Avançado (Contratos) e Simples (Formulários Únicos)."""
        novo_modo = "simples" if modo_str.lower() == "simples" else "avancado"
        config_manager.definir("modo_operacao", novo_modo)
        self._atualizar_botoes_modo(novo_modo)

        perfis_modo = listar_perfis_por_modo(novo_modo)
        nomes_perfis = [p.nome for p in perfis_modo]
        perfil_ativo_atual = config_manager.obter("perfil_ativo") or ""

        if perfil_ativo_atual not in nomes_perfis and nomes_perfis:
            novo_perfil = nomes_perfis[0]
            config_manager.definir("perfil_ativo", novo_perfil)
            self.dropdown_perfil.set(novo_perfil)

        self._atualizar_stepper(1)
        self._aplicar_perfil_ativo()
        modo_lbl = "Simples" if novo_modo == "simples" else "Avançado"
        complemento = (
            "Escolha um ou mais formulários para preencher."
            if novo_modo == "simples"
            else "Selecione um perfil para gerar o conjunto completo de documentos."
        )
        show_toast(self, f"Modo {modo_lbl} ativado. {complemento}", "info")

    def _ao_trocar_perfil(self, nome_perfil: str) -> None:
        """Callback ao selecionar um perfil no dropdown."""
        config_manager.definir("perfil_ativo", nome_perfil)
        self._aplicar_perfil_ativo()
        show_toast(self, f"Perfil alterado para: {nome_perfil}", "success")

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

    # ==================================================================
    # NAVEGAÇÃO ENTRE TELAS
    # ==================================================================
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

    def _aplicar_perfil_ativo(self) -> None:
        """Atualiza a UI da Etapa 1 e Etapa 2 para refletir o perfil ativo."""
        self._ocultar_analise_pendencias()
        perfil = self._obter_perfil_em_uso()
        modo = config_manager.obter("modo_operacao") or "avancado"
        is_simples = (modo == "simples")

        # 1. Atualizar campos customizados dos participantes na Etapa 1
        campos_participante = perfil.obter_campos_participante() if perfil else []
        for pf in self.participant_frames:
            pf.reconstruir_campos_customizados(
                campos_participante,
                perfil.agrupamento_paginas if perfil else None,
            )

        # 2. Reconstruir campos globais na Seção de Destino
        self._reconstruir_campos_globais_saida(perfil)

        # 3. Controlar visibilidade do botão de adicionar participante baseado em perfil.max_participantes
        max_part = getattr(perfil, "max_participantes", 4) if perfil else 4
        if len(self.participant_frames) > max_part:
            for f in list(self.participant_frames[max_part:]):
                try:
                    f.destroy()
                except Exception:
                    pass
            self.participant_frames = self.participant_frames[:max_part]
            for novo_indice, restante in enumerate(self.participant_frames, start=1):
                restante.atualizar_indice(novo_indice)

        self._configurar_paginacao(perfil)

        # 4. Atualizar texto do botão de ação da Etapa 1
        if hasattr(self, "botao_avancar"):
            if is_simples:
                self.botao_avancar.configure(
                    text="GERAR FORMULÁRIOS (PDF) ",
                    image=self.icon_contract,
                )
            else:
                self.botao_avancar.configure(
                    text="GERAR DOCUMENTOS E AVANÇAR ",
                    image=self.icon_advance,
                )

        # 5. Atualizar UI da Etapa 2
        self._carregar_formularios_dinamicos_etapa2()

        if hasattr(self, 'document_frame') and perfil:
            self.document_frame.carregar_documentos(perfil.documentos_extras)

        if hasattr(self, 'label_formato_etapa2') and perfil:
            self.label_formato_etapa2.configure(text=f"Formato de saída: {perfil.formato_saida}")
        self._atualizar_estado_geracao()

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

    def _reconstruir_campos_globais_saida(self, perfil: Optional[Perfil]) -> None:
        """Reconstrói dinamicamente os campos de escopo global na seção de destino."""
        if not hasattr(self, "container_campos_globais"):
            return

        estava_visivel = self.container_campos_globais.winfo_manager() == "grid"
        if estava_visivel:
            self.container_campos_globais.grid_remove()

        if hasattr(self, "_subtitulos_labels"):
            self._subtitulos_labels.clear()

        valores_atuais = {cid: w.obter_valor() for cid, w in self.widgets_dinamicos_globais.items()}

        for w in self.widgets_dinamicos_globais.values():
            try:
                w.destroy()
            except Exception:
                pass
        self.widgets_dinamicos_globais.clear()
        self._paginas_widgets_globais = {}
        self._paginas_secoes_globais = {}

        if hasattr(self, "_frames_subtitulos_globais"):
            for f in self._frames_subtitulos_globais:
                try:
                    f.destroy()
                except Exception:
                    pass
        self._frames_subtitulos_globais = []

        if not perfil:
            self.container_campos_globais.grid_remove()
            return

        campos_globais = perfil.obter_campos_globais()
        if not any(c.id not in ("data_assinatura", "local_assinatura") for c in campos_globais):
            self.container_campos_globais.grid_remove()
            return

        self.container_campos_globais.grid()
        linha = 0
        secao_anterior = None
        for campo in campos_globais:
            if campo.id in ("data_assinatura", "local_assinatura"):
                continue

            nome_secao = campo.aba.strip() if campo.aba else ""
            if nome_secao and nome_secao != "Geral" and nome_secao != secao_anterior:
                frame_sub = self._criar_subtitulo_secao(self.container_campos_globais, nome_secao)
                frame_sub.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=(SPACING_SMALL, 0))
                self._frames_subtitulos_globais.append(frame_sub)
                pagina = perfil.obter_pagina_do_campo(campo)
                self._paginas_secoes_globais.setdefault(pagina, []).append(frame_sub)
                linha += 1
                secao_anterior = nome_secao

            widget_campo = CampoDinamicoWidget(
                self.container_campos_globais,
                campo=campo,
                on_change=lambda valor, campo_id=campo.id: self._ao_alterar_campo_global(campo_id, valor),
                on_open_datepicker=lambda entry: DatePickerPopup(self, entry),
            )
            widget_campo.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=0)
            self.widgets_dinamicos_globais[campo.id] = widget_campo
            pagina = perfil.obter_pagina_do_campo(campo)
            self._paginas_widgets_globais.setdefault(pagina, []).append(widget_campo)

            if campo.id in valores_atuais:
                widget_campo.definir_valor(valores_atuais[campo.id])
            linha += 1

        self._aplicar_calculos_globais()
        self._atualizar_campos_globais_condicionais()

        if linha > 0:
            self.container_campos_globais.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, SPACING_SMALL))
        else:
            self.container_campos_globais.grid_remove()

    def _construir_navegacao_paginas(self) -> None:
        self.frame_paginas = ctk.CTkFrame(
            self.container_etapa1, fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER,
        )
        self.frame_paginas.grid(
            row=0, column=0, padx=SPACING_LARGE,
            pady=(SPACING_MEDIUM, 0), sticky="ew",
        )
        self.frame_paginas.grid_columnconfigure(1, weight=1)
        self.btn_pagina_anterior = ctk.CTkButton(
            self.frame_paginas, text="← Anterior", width=96,
            fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
            hover_color=COLOR_BORDER, command=lambda: self._mudar_pagina(-1),
        )
        self.btn_pagina_anterior.grid(row=0, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL)
        contexto = ctk.CTkFrame(self.frame_paginas, fg_color="transparent")
        contexto.grid(row=0, column=1, padx=SPACING_SMALL, pady=SPACING_SMALL)

        self.linha_formulario_pagina = ctk.CTkFrame(contexto, fg_color="transparent")
        self.linha_formulario_pagina.pack(anchor="center", pady=(0, 2))
        self.label_formulario_contador = ctk.CTkLabel(
            self.linha_formulario_pagina, text="", width=104, height=22,
            fg_color=get_color_primary_hover(), corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION, "bold"), text_color="#FFFFFF",
        )
        self.label_formulario_contador.pack(side="left", padx=(0, SPACING_SMALL))
        self.label_formulario_nome = ctk.CTkLabel(
            self.linha_formulario_pagina, text="",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=get_color_primary_text(),
        )
        self.label_formulario_nome.pack(side="left")

        self.linha_pagina_atual = ctk.CTkFrame(contexto, fg_color="transparent")
        self.linha_pagina_atual.pack(anchor="center")
        self.label_pagina_contador = ctk.CTkLabel(
            self.linha_pagina_atual, text="", width=84, height=20,
            fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION, "bold"), text_color=COLOR_TEXT_SECONDARY,
        )
        self.label_pagina_contador.pack(side="left", padx=(0, SPACING_SMALL))
        self.label_pagina = ctk.CTkLabel(
            self.linha_pagina_atual, text="", font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=COLOR_TEXT,
        )
        self.label_pagina.pack(side="left")
        self.btn_proxima_pagina = ctk.CTkButton(
            self.frame_paginas, text="Próxima →", width=96,
            command=lambda: self._mudar_pagina(1),
        )
        self.btn_proxima_pagina.grid(row=0, column=2, padx=SPACING_SMALL, pady=SPACING_SMALL)
        self.frame_paginas.grid_remove()
        self._paginas_perfil: list[str] = []
        self._indice_pagina = 0

    def _configurar_paginacao(self, perfil: Optional[Perfil]) -> None:
        paginas = perfil.obter_abas_disponiveis() if perfil else []
        if not perfil or not perfil.usar_paginacao or len(paginas) < 2:
            self._paginas_perfil = []
            self.frame_paginas.grid_remove()
            limite = self._limite_participantes_pagina(None)
            for participante in self.participant_frames:
                participante.aplicar_pagina(
                    None,
                    participante_permitido=participante.indice <= limite,
                )
            self._atualizar_contexto_participantes(None)
            self._atualizar_visibilidade_participantes()
            self._aplicar_pagina_global(None)
            self._atualizar_visibilidade_secao_saida()
            self._atualizar_estado_geracao()
            return
        self._paginas_perfil = paginas
        self._indice_pagina = 0
        self.frame_paginas.grid()
        self._mostrar_pagina_atual()

    def _mudar_pagina(self, deslocamento: int) -> None:
        if not self._paginas_perfil:
            return
        novo_indice = max(0, min(len(self._paginas_perfil) - 1, self._indice_pagina + deslocamento))
        if novo_indice == self._indice_pagina:
            return
        self._indice_pagina = novo_indice
        self._mostrar_pagina_atual()

    def _limite_participantes_pagina(self, pagina: str | None) -> int:
        modo = config_manager.obter("modo_operacao") or "avancado"
        if modo == "simples":
            return limite_participantes_para_pagina(
                self._obter_perfis_basicos_selecionados(), pagina
            )
        perfil = self._obter_perfil_em_uso()
        return max(1, getattr(perfil, "max_participantes", 4) if perfil else 4)

    def _pagina_eh_inicial_do_formulario(self, pagina: str | None) -> bool:
        if not pagina or " • " not in pagina:
            return not self._paginas_perfil or self._indice_pagina == 0
        formulario = pagina.split(" • ", 1)[0]
        paginas = [item for item in self._paginas_perfil if item.startswith(f"{formulario} • ")]
        return bool(paginas) and pagina == paginas[0]

    def _atualizar_contexto_participantes(self, pagina: str | None) -> None:
        if not hasattr(self, "label_participantes_contexto"):
            return
        limite = self._limite_participantes_pagina(pagina)
        if limite == 1:
            texto = "Este formulário utiliza somente os dados do proponente principal."
        else:
            texto = f"Este formulário permite até {limite} proponentes."
        self.label_participantes_contexto.configure(text=texto)

    def _mostrar_pagina_atual(self) -> None:
        pagina = self._paginas_perfil[self._indice_pagina]
        total = len(self._paginas_perfil)
        if " • " in pagina:
            formulario, secao = pagina.split(" • ", 1)
            formularios = list(dict.fromkeys(
                item.split(" • ", 1)[0]
                for item in self._paginas_perfil
                if " • " in item
            ))
            paginas_formulario = [
                item for item in self._paginas_perfil
                if item.startswith(f"{formulario} • ")
            ]
            indice_formulario = formularios.index(formulario) + 1
            indice_secao = paginas_formulario.index(pagina) + 1
            self.linha_formulario_pagina.pack(anchor="center", pady=(0, 2))
            self.label_formulario_contador.configure(
                text=f"FORMULÁRIO {indice_formulario}/{len(formularios)}"
            )
            self.label_formulario_nome.configure(text=formulario)
            self.label_pagina_contador.configure(
                text=f"PÁGINA {indice_secao}/{len(paginas_formulario)}"
            )
            texto_pagina = secao
        else:
            modo = config_manager.obter("modo_operacao") or "avancado"
            if modo == "simples":
                perfis = self._obter_perfis_basicos_selecionados()
                nome_formulario = perfis[0].nome if perfis else "Formulário selecionado"
                self.linha_formulario_pagina.pack(anchor="center", pady=(0, 2))
                self.label_formulario_contador.configure(text="FORMULÁRIO 1/1")
                self.label_formulario_nome.configure(text=nome_formulario)
            else:
                self.linha_formulario_pagina.pack_forget()
            self.label_pagina_contador.configure(text=f"PÁGINA {self._indice_pagina + 1}/{total}")
            texto_pagina = pagina
        self.label_pagina.configure(text=texto_pagina)
        self.btn_pagina_anterior.configure(state="normal" if self._indice_pagina > 0 else "disabled")
        self.btn_proxima_pagina.configure(state="normal" if self._indice_pagina < total - 1 else "disabled")
        limite_participantes = self._limite_participantes_pagina(pagina)
        primeira_do_formulario = self._pagina_eh_inicial_do_formulario(pagina)
        for participante in self.participant_frames:
            participante.aplicar_pagina(
                pagina,
                primeira=primeira_do_formulario,
                participante_permitido=participante.indice <= limite_participantes,
            )
        self._atualizar_contexto_participantes(pagina)
        self._atualizar_visibilidade_participantes()
        self._aplicar_pagina_global(pagina)
        self._atualizar_visibilidade_secao_saida()
        self._atualizar_estado_geracao()
        try:
            self.scroll_etapa1._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _aplicar_pagina_global(self, pagina: str | None) -> None:
        for nome, widgets in getattr(self, "_paginas_widgets_globais", {}).items():
            for widget in widgets:
                widget.definir_pagina_visivel(pagina is None or nome == pagina)
        for nome, secoes in getattr(self, "_paginas_secoes_globais", {}).items():
            for secao in secoes:
                if pagina is None or nome == pagina:
                    secao.grid()
                else:
                    secao.grid_remove()
        self._atualizar_visibilidade_container_campos_globais()

    def _atualizar_visibilidade_container_campos_globais(self) -> None:
        """Remove o espaço reservado quando a página não possui campos globais visíveis."""
        if not hasattr(self, "container_campos_globais"):
            return

        possui_campo_visivel = any(
            widget.ativo and widget.pagina_visivel
            for widget in self.widgets_dinamicos_globais.values()
        )
        if possui_campo_visivel:
            self.container_campos_globais.grid()
        else:
            self.container_campos_globais.grid_remove()

    def _atualizar_visibilidade_secao_saida(self) -> None:
        """Oculta blocos vazios e deixa os dados finais apenas na última página."""
        if not hasattr(self, "secao_saida"):
            return
        globais_visiveis = any(
            widget.ativo and widget.pagina_visivel
            for widget in self.widgets_dinamicos_globais.values()
        )
        if globais_visiveis:
            self.container_campos_globais.grid()
        else:
            self.container_campos_globais.grid_remove()

        pagina_final = (
            not self._paginas_perfil
            or self._indice_pagina == len(self._paginas_perfil) - 1
        )
        if pagina_final:
            self.frame_data_fixa.grid()
            self.secao_saida.grid()
        elif globais_visiveis:
            self.frame_data_fixa.grid_remove()
            self.secao_saida.grid()
        else:
            self.secao_saida.grid_remove()

    def _atualizar_visibilidade_participantes(self) -> None:
        """Evita que uma página sem campos do participante mantenha um quadro vazio."""
        if not hasattr(self, "secao_participantes"):
            return
        ha_participante_visivel = any(
            frame.winfo_manager() == "grid" for frame in self.participant_frames
        )
        if ha_participante_visivel:
            self.secao_participantes.grid()
        else:
            self.secao_participantes.grid_remove()

        if not hasattr(self, "botao_adicionar"):
            return
        pagina = (
            self._paginas_perfil[self._indice_pagina]
            if self._paginas_perfil else None
        )
        primeira_pagina = self._pagina_eh_inicial_do_formulario(pagina)
        limite = self._limite_participantes_pagina(pagina)
        if primeira_pagina and limite > 1 and len(self.participant_frames) < limite:
            self.botao_adicionar.grid()
        else:
            self.botao_adicionar.grid_remove()

    def _ao_alterar_campo_global(self, campo_id: str, valor: str) -> None:
        self._aplicar_calculos_globais()
        self._atualizar_campos_globais_condicionais()
        self._atualizar_estado_geracao()

    def _aplicar_calculos_globais(self) -> None:
        """Atualiza os campos que possuem um cálculo salvo no perfil."""
        valores = {
            campo_id: widget.obter_valor()
            for campo_id, widget in self.widgets_dinamicos_globais.items()
        }
        for widget in self.widgets_dinamicos_globais.values():
            expressao = getattr(widget.campo, "calculo", "").strip()
            if expressao:
                novo_valor = calcular(expressao, valores)
                widget.definir_valor(novo_valor)
                valores[widget.campo.id] = novo_valor

    def _atualizar_campos_globais_condicionais(self) -> None:
        valores = {campo_id: widget.obter_valor() for campo_id, widget in self.widgets_dinamicos_globais.items()}
        for widget in self.widgets_dinamicos_globais.values():
            alternativas = getattr(widget.campo, "visivel_quando", []) or []
            visivel = True
            if alternativas:
                visivel = any(
                    all(valores.get(dependencia, "") in aceitos for dependencia, aceitos in condicao.items())
                    for condicao in alternativas
                )
            estava_ativo = widget.ativo
            widget.definir_ativo(
                visivel,
                limpar=(estava_ativo and not visivel and widget.campo.limpar_quando_oculto),
            )
        self._atualizar_visibilidade_secao_saida()

    def _limpar_campos_etapa1(self) -> None:
        """Limpa os campos preenchidos da Etapa 1."""
        for pf in self.participant_frames:
            pf.limpar_campos()
        self.entry_data.delete(0, "end")
        self.entry_data.configure(border_color=COLOR_BORDER)
        for w in self.widgets_dinamicos_globais.values():
            w.limpar()

    def _ao_foco_widget(self, widget, border_color=None, border_width=2) -> None:
        """Destaca visualmente o elemento em foco e ajusta o scroll se necessário."""
        try:
            widget.configure(border_color=border_color or get_color_primary(), border_width=border_width)
            if hasattr(self, "scroll_etapa1"):
                self.after(50, lambda: rolar_para_widget_se_necessario(widget, self.scroll_etapa1))
        except Exception:
            pass

    def _ao_desfoco_widget(self, widget, callback_validar=None, default_border_width=1, default_border_color=COLOR_BORDER) -> None:
        """Restaura o estilo padrão ao perder o foco."""
        try:
            widget.configure(border_width=default_border_width, border_color=default_border_color)
            if callback_validar:
                callback_validar()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # ETAPA 1: Preenchimento e Validação (Estrutura Responsiva e Flexível)
    # ------------------------------------------------------------------
    def _construir_etapa1(self) -> None:
        # Área rolável da Etapa 1, entre a paginação e as ações fixas.
        self.scroll_etapa1 = ctk.CTkScrollableFrame(
            self.container_etapa1, fg_color="transparent", label_text=""
        )
        self.scroll_etapa1.grid(row=1, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_etapa1.grid_columnconfigure(0, weight=1)
        configurar_autoscroll(self.scroll_etapa1)

        self._construir_navegacao_paginas()
        self._construir_secao_participantes()
        self._construir_secao_saida()

        # Ações sempre fixadas na base do card.
        frame_botoes = ctk.CTkFrame(self.container_etapa1, fg_color="transparent")
        frame_botoes.grid(row=2, column=0, padx=SPACING_LARGE,
                          pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_botoes.grid_columnconfigure(0, weight=1)

        self.chk_preservar_dados = ctk.CTkCheckBox(
            frame_botoes,
            text="Preservar dados para Reutilizar",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT,
            border_color=COLOR_BORDER,
            fg_color=get_color_primary(),
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
        )
        self.chk_preservar_dados.grid(row=0, column=0, padx=SPACING_XSMALL, pady=(0, SPACING_XSMALL), sticky="w")

        self.frame_pendencias = ctk.CTkFrame(
            frame_botoes,
            fg_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_INPUT,
            border_width=1,
            border_color=COLOR_WARNING,
        )
        self.frame_pendencias.grid(
            row=1, column=0, pady=(SPACING_XSMALL, SPACING_SMALL), sticky="ew"
        )
        self.frame_pendencias.grid_columnconfigure(0, weight=1)

        self.label_pendencias_titulo = ctk.CTkLabel(
            self.frame_pendencias,
            text="Pendências do preenchimento",
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=COLOR_WARNING,
            anchor="w",
        )
        self.label_pendencias_titulo.grid(
            row=0, column=0, padx=(SPACING_MEDIUM, SPACING_SMALL),
            pady=(SPACING_SMALL, 0), sticky="ew",
        )
        self.label_pendencias = ctk.CTkLabel(
            self.frame_pendencias,
            text="",
            font=get_font(FONT_SIZE_CAPTION),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self.label_pendencias.grid(
            row=1, column=0, padx=(SPACING_MEDIUM, SPACING_SMALL),
            pady=(0, SPACING_SMALL), sticky="ew",
        )
        self.btn_ver_pendencias = ctk.CTkButton(
            self.frame_pendencias,
            text="Ver e corrigir",
            width=120,
            height=32,
            fg_color=COLOR_WARNING,
            text_color="#FFFFFF",
            hover_color="#D96C00",
            command=self._mostrar_pendencias,
        )
        self.btn_ver_pendencias.grid(
            row=0, column=1, rowspan=2, padx=SPACING_SMALL,
            pady=SPACING_SMALL, sticky="e",
        )

        self.botao_avancar = ctk.CTkButton(
            frame_botoes,
            text="GERAR DOCUMENTOS E AVANÇAR ",
            image=self.icon_advance,
            compound="right",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            text_color="#FFFFFF",
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_avancar,
        )
        self.botao_avancar.grid(row=2, column=0, sticky="ew")
        self.botao_avancar.bind("<FocusIn>", lambda e: self.botao_avancar.configure(border_width=2, border_color="#FFFFFF"))
        self.botao_avancar.bind("<FocusOut>", lambda e: self.botao_avancar.configure(border_width=0))
        self._atualizar_estado_geracao()

    def _construir_secao_participantes(self) -> None:
        self.secao_participantes = ctk.CTkFrame(self.scroll_etapa1, fg_color="transparent")
        self.secao_participantes.grid(row=0, column=0, padx=SPACING_MEDIUM,
                   pady=(SPACING_MEDIUM, SPACING_SMALL), sticky="nsew")
        self.secao_participantes.grid_columnconfigure(0, weight=1)

        titulo = ctk.CTkLabel(self.secao_participantes, text="Participantes",
                              font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")

        self.label_participantes_contexto = ctk.CTkLabel(
            self.secao_participantes,
            text="",
            font=get_font(FONT_SIZE_CAPTION),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self.label_participantes_contexto.grid(
            row=1, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="ew"
        )

        # Container onde os ParticipantFrames serão empilhados de forma limpa
        self.participantes_container = ctk.CTkFrame(
            self.secao_participantes, fg_color="transparent"
        )
        self.participantes_container.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        self.participantes_container.grid_columnconfigure(0, weight=1)

        self.botao_adicionar = ctk.CTkButton(
            self.secao_participantes, text=" Adicionar Participante",
            image=self.icon_add_user, compound="left",
            fg_color=COLOR_SURFACE, text_color=get_color_primary_text(),
            border_width=1, border_color=get_color_primary_text(),
            hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
            command=self._adicionar_participante,
        )
        self.botao_adicionar.grid(row=3, column=0, padx=0, pady=(SPACING_LARGE, 0), sticky="w")
        self.botao_adicionar.bind("<FocusIn>", lambda e: self._ao_foco_widget(self.botao_adicionar, border_color=get_color_primary(), border_width=2))
        self.botao_adicionar.bind("<FocusOut>", lambda e: self._ao_desfoco_widget(self.botao_adicionar, default_border_width=1, default_border_color=get_color_primary_text()))

    def _construir_secao_saida(self) -> None:
        secao = ctk.CTkFrame(self.scroll_etapa1, fg_color="transparent")
        self.secao_saida = secao
        secao.grid(row=1, column=0, padx=SPACING_MEDIUM, pady=(SPACING_SMALL, SPACING_MEDIUM), sticky="ew")
        secao.grid_columnconfigure(0, minsize=145)
        secao.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            secao, text=" Destino e Dados Complementares",
            image=get_icon("briefcase", (18, 18)), compound="left",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT
        )
        titulo.grid(row=0, column=0, columnspan=3, padx=SPACING_LARGE,
                    pady=(SPACING_MEDIUM, SPACING_SMALL), sticky="w")

        # Container para campos globais dinâmicos do perfil (inicialmente oculto se vazio)
        self.container_campos_globais = ctk.CTkFrame(secao, fg_color="transparent")
        self.container_campos_globais.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.container_campos_globais.grid_columnconfigure(0, minsize=145)
        self.container_campos_globais.grid_columnconfigure(1, weight=1)
        self.container_campos_globais.grid_remove()

        # Campos Globais Fixos (Data e Local)
        self.frame_data_fixa = ctk.CTkFrame(secao, fg_color="transparent")
        self.frame_data_fixa.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.frame_data_fixa.grid_columnconfigure(0, minsize=145)
        self.frame_data_fixa.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.frame_data_fixa, text=" Data da assinatura",
            image=get_icon("calendar", (16, 16)), compound="left",
            width=145, anchor="w",
            font=get_font(FONT_SIZE_BODY)
        ).grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")
            
        frame_data = ctk.CTkFrame(self.frame_data_fixa, fg_color="transparent")
        frame_data.grid(row=0, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        frame_data.grid_columnconfigure(0, weight=1)
        
        self.entry_data = ctk.CTkEntry(frame_data, placeholder_text="DD/MM/AAAA", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        self.entry_data.grid(row=0, column=0, sticky="ew")
        self.entry_data.bind("<KeyRelease>", self._ao_digitar_data)
        self.entry_data.bind("<FocusIn>", lambda e: self._ao_foco_widget(self.entry_data))
        self.entry_data.bind("<FocusOut>", lambda e: self._ao_desfoco_widget(self.entry_data, self._validar_data_realtime))
        
        self.btn_calendar = ctk.CTkButton(
            frame_data, text="", image=self.icon_calendar, width=40, corner_radius=RADIUS_BUTTON,
            fg_color=COLOR_BORDER, text_color=COLOR_TEXT, hover_color=COLOR_TEXT_DISABLED,
            command=lambda: DatePickerPopup(
                self, self.entry_data, anchor_widget=self.btn_calendar,
                on_select=lambda d: (self._validar_data_realtime(), self._atualizar_estado_geracao())
            )
        )
        self.btn_calendar.grid(row=0, column=1, padx=(SPACING_SMALL, 0))

        ctk.CTkLabel(
            self.frame_data_fixa, text=" Local da assinatura",
            image=get_icon("location", (16, 16)), compound="left",
            width=145, anchor="w",
            font=get_font(FONT_SIZE_BODY)
        ).grid(row=1, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")
        self.entry_local = ctk.CTkEntry(self.frame_data_fixa, placeholder_text="Ex: CAMOCIM-CE", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        self.entry_local.grid(row=1, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        self.entry_local.insert(0, config_manager.obter("local_padrao") or "CAMOCIM-CE")
        self.entry_local.bind("<KeyRelease>", lambda e: (self._validar_local_realtime(), self._atualizar_estado_geracao()))
        self.entry_local.bind("<FocusIn>", lambda e: self._ao_foco_widget(self.entry_local))
        self.entry_local.bind("<FocusOut>", lambda e: self._ao_desfoco_widget(self.entry_local, self._validar_local_realtime))

        # Pasta padrão Downloads (com fallbacks seguros)
        self.pasta_saida = pasta_downloads()

        # Seletor de diretório
        ctk.CTkLabel(
            secao, text=" Diretório de saída:",
            image=get_icon("folder", (16, 16)), compound="left",
            width=145, anchor="w",
            font=get_font(FONT_SIZE_BODY, "bold")
        ).grid(row=3, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=(SPACING_SMALL, SPACING_LARGE), sticky="w")
        
        frame_dir = ctk.CTkFrame(secao, fg_color="transparent")
        frame_dir.grid(row=3, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_dir.grid_columnconfigure(0, weight=1)

        self.entry_pasta_saida = ctk.CTkEntry(
            frame_dir, placeholder_text="Selecione o diretório de destino...",
            fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_INPUT,
            border_color=COLOR_BORDER,
        )
        self.entry_pasta_saida.grid(row=0, column=0, sticky="ew")
        self.entry_pasta_saida.insert(0, str(self.pasta_saida))
        self.entry_pasta_saida.bind("<KeyRelease>", lambda e: self._ao_editar_pasta_saida())
        self.entry_pasta_saida.bind("<FocusOut>", lambda e: self._ao_editar_pasta_saida())

        ctk.CTkButton(frame_dir, text="", image=self.icon_folder, width=40, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_BORDER, text_color=COLOR_TEXT,
                      hover_color=COLOR_TEXT_DISABLED, command=self._selecionar_pasta_saida
                      ).grid(row=0, column=1, padx=(SPACING_SMALL, 0))

    def _ao_digitar_data(self, event=None) -> None:
        if event and event.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down", "Return"):
            return
        val = self.entry_data.get()
        if event and event.keysym != "BackSpace":
            novo_val = formatar_data_progressiva(val)
            if novo_val != val:
                self.entry_data.delete(0, "end")
                self.entry_data.insert(0, novo_val)
        self._validar_data_realtime()
        self._atualizar_estado_geracao()

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

    def _adicionar_participante(self, principal: bool = False) -> None:
        perfil = self._obter_perfil_em_uso()
        max_part = getattr(perfil, "max_participantes", 4) if perfil else 4

        if not principal and len(self.participant_frames) >= max_part:
            if hasattr(self, "botao_adicionar"):
                self.botao_adicionar.grid_remove()
            return

        indice = len(self.participant_frames) + 1
        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        campos_participante = perfil.obter_campos_participante() if perfil else None

        frame = ParticipantFrame(
            self.participantes_container,
            indice=indice,
            principal=principal,
            on_remover=None if principal else self._remover_participante,
            campos_customizados=campos_participante,
            on_open_datepicker=lambda entry: DatePickerPopup(self, entry),
            on_change=self._atualizar_estado_geracao,
            local_padrao=local_padrao,
            agrupamento_paginas=perfil.agrupamento_paginas if perfil else None,
        )
        frame.grid(row=indice - 1, column=0, padx=SPACING_SMALL,
                   pady=SPACING_SMALL, sticky="ew")
        self.participant_frames.append(frame)

        if getattr(self, "_paginas_perfil", []):
            pagina_atual = self._paginas_perfil[self._indice_pagina]
            limite_pagina = self._limite_participantes_pagina(pagina_atual)
            frame.aplicar_pagina(
                pagina_atual,
                primeira=self._pagina_eh_inicial_do_formulario(pagina_atual),
                participante_permitido=indice <= limite_pagina,
            )

        if not principal:
            frame.piscar_destaque()

        self._atualizar_visibilidade_participantes()
        self._atualizar_estado_geracao()

    def _remover_participante(self, frame: ParticipantFrame) -> None:
        frame.destroy()
        if frame in self.participant_frames:
            self.participant_frames.remove(frame)
        perfil = self._obter_perfil_em_uso()
        campos_participante = perfil.obter_campos_participante() if perfil else []
        for novo_indice, restante in enumerate(self.participant_frames, start=1):
            restante.atualizar_indice(novo_indice)
            restante.reconstruir_campos_customizados(
                campos_participante,
                perfil.agrupamento_paginas if perfil else None,
            )

        self._atualizar_visibilidade_participantes()
        self._atualizar_estado_geracao()

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

    def _listar_pendencias_etapa1(self) -> list[str]:
        """Verifica todas as páginas sem obrigar o usuário a visitá-las."""
        erros: list[str] = []
        for frame in getattr(self, "participant_frames", []):
            erros.extend(frame.listar_pendencias())
        for widget in getattr(self, "widgets_dinamicos_globais", {}).values():
            if widget.ativo and not widget.validar_campo(mostrar_erro=False):
                valor = widget.obter_valor()
                if widget.campo.obrigatorio and not valor:
                    erros.append(f"Destino / Complemento: {widget.campo.rotulo} é obrigatório.")
                else:
                    erros.append(f"Destino / Complemento: {widget.campo.rotulo} é inválido.")
        if hasattr(self, "entry_data"):
            data = self.entry_data.get().strip()
            if not data:
                erros.append("Data da assinatura é obrigatória.")
            elif not validar_data(data):
                erros.append("Data da assinatura é inválida.")
        if hasattr(self, "entry_local") and not self.entry_local.get().strip():
            erros.append("Local da assinatura é obrigatório.")
        if hasattr(self, "entry_pasta_saida") and not self.entry_pasta_saida.get().strip():
            erros.append("Diretório de saída é obrigatório.")
        return erros

    def _atualizar_estado_geracao(self) -> None:
        """Mantém a ação acessível e atualiza o destaque das pendências."""
        if not hasattr(self, "botao_avancar"):
            return
        pendencias = self._listar_pendencias_etapa1()
        pronto = not pendencias
        # O clique continua disponível: a validação mostra ao usuário o que
        # falta, em vez de deixar um botão aparentemente quebrado/desabilitado.
        self.botao_avancar.configure(state="normal")
        if hasattr(self, "frame_pendencias"):
            if self._pendencias_reveladas:
                self.frame_pendencias.grid()
            else:
                self.frame_pendencias.grid_remove()
        if hasattr(self, "label_pendencias"):
            if pronto:
                self.frame_pendencias.configure(border_color=COLOR_SUCCESS)
                self.label_pendencias_titulo.configure(
                    text="Tudo certo para gerar", text_color=COLOR_SUCCESS
                )
                self.label_pendencias.configure(
                    text="Todos os campos obrigatórios foram preenchidos.",
                    text_color=COLOR_TEXT_SECONDARY,
                )
                if hasattr(self, "btn_ver_pendencias"):
                    self.btn_ver_pendencias.grid_remove()
            else:
                paginas = len(self._paginas_perfil) if getattr(self, "_paginas_perfil", []) else 1
                self.frame_pendencias.configure(border_color=COLOR_WARNING)
                self.label_pendencias_titulo.configure(
                    text=f"Faltam {len(pendencias)} campos para gerar",
                    text_color=COLOR_WARNING,
                )
                self.label_pendencias.configure(
                    text=f"Pendências distribuídas em {paginas} página(s). Veja a lista para localizar cada campo.",
                    text_color=COLOR_TEXT_SECONDARY,
                )
                if hasattr(self, "btn_ver_pendencias"):
                    self.btn_ver_pendencias.grid()

    def _ocultar_analise_pendencias(self) -> None:
        """Reinicia o aviso ao trocar de perfil; antes da tentativa a tela fica limpa."""
        self._tentativa_pendencias_id += 1
        self._pendencias_reveladas = False
        self._toast_pendencias_ativo = False
        if hasattr(self, "frame_pendencias"):
            self.frame_pendencias.grid_remove()

    def _avisar_pendencias_antes_de_exibir(self, quantidade: int) -> None:
        """Mostra o toast e revela o quadro somente depois que ele desaparecer."""
        if self._toast_pendencias_ativo:
            return
        self._toast_pendencias_ativo = True
        self._tentativa_pendencias_id += 1
        tentativa_id = self._tentativa_pendencias_id

        def revelar() -> None:
            if tentativa_id != self._tentativa_pendencias_id:
                return
            self._toast_pendencias_ativo = False
            self._pendencias_reveladas = True
            self._atualizar_estado_geracao()

        show_toast(
            self,
            f"Ainda faltam {quantidade} campos. Veja os detalhes logo abaixo.",
            "warning",
            on_dismiss=revelar,
            duration_ms=3000,
        )

    def _mostrar_pendencias(self) -> None:
        """Exibe o modal com a lista completa de campos pendentes."""
        pendencias = self._listar_pendencias_etapa1()
        if not pendencias:
            return
        AlertModal(
            self,
            titulo="Campos pendentes",
            subtitulo="Preencha os itens abaixo, inclusive os que estão em outras páginas.",
            erros=pendencias,
        )

    def _ao_clicar_avancar(self) -> None:
        erros: list[str] = []

        # 1. Validar campos de todos os participantes
        for frame in self.participant_frames:
            erros.extend(frame.validar_campos())

        # 2. Validar campos globais dinâmicos
        for campo_id, widget in self.widgets_dinamicos_globais.items():
            erros.extend(widget.validar(prefixo="Destino / Complemento"))

        # 3. Validar Data e Local
        if not self._validar_data_realtime():
            val = self.entry_data.get().strip()
            if not val:
                erros.append("Data da assinatura é obrigatória.")
            else:
                erros.append("Data da assinatura é inválida. Utilize o formato DD/MM/AAAA (ex.: 15/07/2026).")

        if not self._validar_local_realtime():
            erros.append("Local da assinatura é obrigatório.")

        # 4. Validar perfil e modelos
        perfil = self._obter_perfil_em_uso()
        if not perfil:
            erros.append("Os formulários selecionados não puderam ser carregados.")
        elif not perfil.formularios:
            erros.append(f"O perfil '{perfil.nome}' não possui nenhum formulário configurado.")
        else:
            from services.generator_service import resolver_caminho_formulario
            for f in perfil.formularios:
                caminho_resolvido = resolver_caminho_formulario(f)
                if not caminho_resolvido or not caminho_resolvido.exists():
                    erros.append(f"O formulário '{f.nome}' aponta para um arquivo inexistente.")

        # 5. Validar pasta de saída
        if not self.pasta_saida:
            erros.append("Selecione a pasta de saída.")
        elif not self._verificar_permissao_escrita(self.pasta_saida):
            erros.append(f"Sem permissão de escrita na pasta de saída: {self.pasta_saida}")

        if erros:
            self._avisar_pendencias_antes_de_exibir(len(erros))
            return

        principal = self.participant_frames[0].obter_participante()
        principal.data_assinatura = self.entry_data.get().strip()
        principal.local_assinatura = self.entry_local.get().strip()

        # Coletar campos globais para o participante principal
        for campo_id, widget in self.widgets_dinamicos_globais.items():
            principal.definir_campo(campo_id, widget.obter_valor())

        participantes = [principal]
        for frame in self.participant_frames[1:]:
            p = frame.obter_participante()
            p.copiar_dados_compartilhados(principal)
            for campo_id, widget in self.widgets_dinamicos_globais.items():
                p.definir_campo(campo_id, widget.obter_valor())
            participantes.append(p)

        modo = config_manager.obter("modo_operacao") or "avancado"
        if modo == "simples" or getattr(perfil, "modo_fluxo", "contrato") == "formulario_simples":
            self._executar_geracao_simples(participantes, perfil)
            return

        self.participantes_etapa1 = participantes
        self.label_pasta_etapa2.configure(text=f"Pasta: {self.pasta_saida}")
        self._mostrar_tela("etapa2")

    def _executar_geracao_simples(self, participantes: list[Participant], perfil: Perfil) -> None:
        """Gera o formulário simples diretamente sem passar pela Etapa 2."""
        try:
            from ui.loading_modal import LoadingModal
            from services.generator_service import gerar_documentos_de_perfis

            perfis = self._obter_perfis_basicos_selecionados()

            modal = LoadingModal(
                self,
                message="Gerando formulários...",
                submessage="Preenchendo e salvando o documento...",
            )

            def _tarefa():
                try:
                    res = gerar_documentos_de_perfis(
                        participantes=participantes,
                        perfis=perfis,
                        pasta_saida=self.pasta_saida,
                    )
                    self.after(0, lambda: self._pos_geracao_simples(modal, res, perfil))
                except Exception as e:
                    self.after(0, lambda: self._falha_geracao_simples(modal, str(e)))

            threading.Thread(target=_tarefa, daemon=True).start()
        except Exception as e:
            from ui.alert_modal import AlertModal
            AlertModal(
                self,
                titulo="Erro na Geração",
                subtitulo="Ocorreu um problema ao iniciar a geração:",
                erros=[str(e)],
            )

    def _pos_geracao_simples(self, modal, resultado, perfil) -> None:
        try:
            modal.dismiss()
        except Exception:
            pass

        preservar = bool(self.chk_preservar_dados.get())
        total = len(resultado.arquivos_gerados)

        if total > 0:
            from ui.success_modal import SuccessModal
            SuccessModal(
                self,
                titulo="Formulários Gerados com Sucesso!",
                subtitulo="Os documentos selecionados foram preenchidos e salvos:",
                arquivos_gerados=resultado.arquivos_gerados,
                pasta_destino=self.pasta_saida,
            )
            if config_manager.obter("abrir_pasta_ao_concluir"):
                self._abrir_pasta(self.pasta_saida)

        if resultado.avisos:
            from ui.alert_modal import AlertModal
            AlertModal(self, titulo="Avisos na Geração", subtitulo="Atenção aos seguintes avisos:", erros=resultado.avisos)

        if not preservar:
            self._limpar_campos_etapa1()

    def _falha_geracao_simples(self, modal, erro_msg: str) -> None:
        try:
            modal.dismiss()
        except Exception:
            pass
        from ui.alert_modal import AlertModal
        AlertModal(self, titulo="Erro na Geração", subtitulo="Ocorreu um problema ao gerar o formulário:", erros=[erro_msg])

    # ------------------------------------------------------------------
    # ETAPA 2: Documentos da Gerente e PDF/A (Layout Responsivo)
    # ------------------------------------------------------------------
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

    def _ao_minimizar_modal_fila(self) -> None:
        """Minimiza o modal de progresso, retorna à tela inicial limpa e atualiza o status na toolbar."""
        self._modal_fila_ativo = None
        self._resetar_aplicacao()
        self._atualizar_botao_fila_status()
        show_toast(self, "Processo minimizado. Executando em segundo plano.", "info")

    def _abrir_modal_fila(self) -> None:
        """Reabre o modal de acompanhamento do processo ativo na fila."""
        job_ativo = self.queue_manager.obter_job_ativo()
        if job_ativo is None:
            show_toast(self, "Nenhum processo em execução no momento.", "info")
            return

        self._modal_fila_ativo = LoadingModal(
            self,
            message=job_ativo.mensagem or "Processando documentos...",
            submessage=job_ativo.submensagem or f"(Etapa {job_ativo.etapa_atual}/{job_ativo.etapa_total})",
            on_cancel=lambda: self.queue_manager.cancelar_job(job_ativo.id),
            on_minimize=self._ao_minimizar_modal_fila,
        )

    # ------------------------------------------------------------------
    # Callbacks da Fila de Background
    # ------------------------------------------------------------------
    # Callbacks da Fila de Background (Thread-Safe via Queue)
    # ------------------------------------------------------------------
    def _iniciar_loop_eventos_ui(self) -> None:
        """Processa eventos enviados pela thread de background no loop principal do Tkinter."""
        def _poll():
            try:
                while hasattr(self, "_ui_event_queue") and not self._ui_event_queue.empty():
                    fn, args = self._ui_event_queue.get_nowait()
                    fn(*args)
            except Exception:
                pass
            try:
                if self.winfo_exists():
                    self._fila_timer = self.after(40, _poll)
            except Exception:
                pass

        self._fila_timer = self.after(40, _poll)

    def _ao_iniciar_job_fila(self, job: ProcessJob) -> None:
        self._ui_event_queue.put((self._ui_job_iniciado, (job,)))

    def _ao_word_travar_na_fila(self, nome_arquivo: str, prazo: int, encerrar) -> None:
        """Recebe o aviso da thread de fundo e agenda o modal na thread da UI."""
        self._ui_event_queue.put((self._mostrar_aviso_word, (nome_arquivo, prazo, encerrar)))

    def _mostrar_aviso_word(self, nome_arquivo: str, prazo: int, encerrar) -> None:
        """Exibe a contagem regressiva antes do encerramento do Word travado."""
        from ui.word_travado_modal import WordTravadoModal

        WordTravadoModal(self, nome_arquivo, prazo, on_fechar_agora=encerrar)

    def _ui_job_iniciado(self, job: ProcessJob) -> None:
        self._atualizar_botao_fila_status()
        if self._modal_fila_ativo:
            self._modal_fila_ativo.update_message(
                "Processando documentos...",
                job.submensagem or f"(Etapa {job.etapa_atual}/{job.etapa_total})"
            )

    def _ao_progresso_job_fila(self, job: ProcessJob, etapa: int, total: int, submsg: str) -> None:
        self._ui_event_queue.put((self._ui_job_progresso, (job, etapa, total, submsg)))

    def _ui_job_progresso(self, job: ProcessJob, etapa: int, total: int, submsg: str) -> None:
        self._atualizar_botao_fila_status()
        if self._modal_fila_ativo:
            self._modal_fila_ativo.atualizar_etapa(etapa, total, submsg)

    def _ao_concluir_job_fila(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        self._ui_event_queue.put((self._ui_job_concluido, (job, resultado)))

    def _ui_job_concluido(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        modal_estava_aberto = (self._modal_fila_ativo is not None)
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None

        # Alerta sonoro amigável do Windows
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        # Exibir modal de confirmação para o usuário saber que finalizou e poder abrir a pasta
        msg = f"{resultado['mensagem']}\n\nPasta de saída:\n{resultado['pasta_pdfa']}"
        from ui.confirm_modal import ConfirmModal

        def _abrir():
            self._abrir_pasta(resultado["pasta_pdfa"])

        ConfirmModal(
            self,
            titulo="Geração Concluída ✓",
            subtitulo=f"Processo '{job.titulo}' finalizado com sucesso!\n\n" + msg + "\n\nDeseja abrir a pasta com os documentos agora?",
            on_confirm=_abrir,
            texto_confirmar="Sim, Abrir Pasta",
            texto_cancelar="Fechar",
        )

        preservar = bool(hasattr(self, "chk_preservar_dados") and self.chk_preservar_dados.get())
        if modal_estava_aberto:
            self._resetar_aplicacao(preservar_dados=preservar)
        else:
            show_toast(self, f"Sucesso: {job.titulo} finalizado!", "success")

        self._exibir_status_concluido_temporario(job, resultado)

    def _exibir_status_concluido_temporario(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        if not hasattr(self, "btn_fila_status"):
            return

        self._status_concluido_ativo = True
        self.btn_fila_status.configure(
            text=" FILA: Concluído ✓",
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS,
            command=lambda: self._abrir_pasta(resultado["pasta_pdfa"]),
        )
        self.btn_fila_status.grid()

        def _expirar():
            self._status_concluido_ativo = False
            self._atualizar_botao_fila_status()

        self.after(8000, _expirar)

    def _ao_erro_job_fila(self, job: ProcessJob, erro: str) -> None:
        self._ui_event_queue.put((self._ui_job_erro, (job, erro)))

    def _ui_job_erro(self, job: ProcessJob, erro: str) -> None:
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None
        show_toast(self, f"Erro: {erro}", "error")
        self._atualizar_botao_fila_status()

    def _ao_cancelado_job_fila(self, job: ProcessJob) -> None:
        self._ui_event_queue.put((self._ui_job_cancelado, (job,)))

    def _ui_job_cancelado(self, job: ProcessJob) -> None:
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None
        show_toast(self, f"Processo '{job.titulo}' foi cancelado.", "warning")
        self._atualizar_botao_fila_status()

    def _ao_mudar_fila(self) -> None:
        self._ui_event_queue.put((self._atualizar_botao_fila_status, ()))

    def _atualizar_botao_fila_status(self) -> None:
        if not hasattr(self, "btn_fila_status"):
            return

        if getattr(self, "_status_concluido_ativo", False):
            # Mantém exibindo o status de sucesso pelo período definido
            return

        if self.queue_manager.tem_trabalho_ativo():
            resumo = self.queue_manager.obter_status_resumo()
            self.btn_fila_status.configure(
                text=f" {resumo}",
                fg_color=get_color_primary_hover(),
                hover_color=get_color_primary_hover(),
                command=self._abrir_modal_fila,
            )
            self.btn_fila_status.grid()
        else:
            self.btn_fila_status.grid_remove()

    def _resetar_aplicacao(self, preservar_dados: bool = False) -> None:
        self._mostrar_tela("inicio")
        if not preservar_dados:
            for frame in list(self.participant_frames[1:]):
                self._remover_participante(frame)

            if self.participant_frames:
                primeiro = self.participant_frames[0]
                primeiro.limpar_campos()
                
            self.entry_data.delete(0, "end")
            self.entry_data.configure(border_color=COLOR_BORDER)
            for w in self.widgets_dinamicos_globais.values():
                w.limpar()

        if hasattr(self, 'document_frame') and self.document_frame:
            self.document_frame.limpar_campos()

        self.participantes_etapa1 = []
        self.arquivos_gerados_etapa1 = []

        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        self.entry_local.delete(0, "end")
        self.entry_local.insert(0, local_padrao)
        self.entry_local.configure(border_color=COLOR_BORDER)
        
        self.entry_pasta_saida.configure(border_color=COLOR_BORDER)
        self.document_frame.limpar()

    @staticmethod
    @staticmethod
    def _abrir_pasta(caminho: Path | str) -> bool:
        """Compatibilidade: delega para `utils.files.abrir_pasta`."""
        from utils.files import abrir_pasta

        return abrir_pasta(caminho)

    # ------------------------------------------------------------------
    # Utilitários de Seleção (Etapa 1)
    # ------------------------------------------------------------------
    def _selecionar_pasta_saida(self) -> None:
        caminho = selecionar_pasta("Selecione a pasta de saída")
        if caminho:
            self.pasta_saida = caminho
            self._atualizar_entry(self.entry_pasta_saida, str(caminho))
            self._atualizar_estado_geracao()

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
        self._atualizar_estado_geracao()

    @staticmethod
    @staticmethod
    def _atualizar_entry(entry: ctk.CTkEntry, texto: str) -> None:
        """Compatibilidade: delega para `utils.files.atualizar_entry`."""
        from utils.files import atualizar_entry

        atualizar_entry(entry, texto)
