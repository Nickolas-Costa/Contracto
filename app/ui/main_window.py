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
    get_color_primary_light, get_color_primary_dark_gradient,
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

        self.title("Contracto — Preparação de Documentos")
        self.geometry("920x880")
        self.minsize(820, 720)
        self.configure(fg_color=COLOR_BACKGROUND)

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

        # Containers das telas
        card_kwargs = {"fg_color": COLOR_SURFACE, "corner_radius": RADIUS_CARD, "width": 800}
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
        except Exception:
            self.icon_home = None
            self.icon_profiles = None
            self.icon_settings = None
            self.icon_calendar = None

    def _construir_toolbar(self) -> None:
        self.toolbar = ctk.CTkFrame(self, fg_color=get_color_primary(),
                                     corner_radius=0, height=44)
        self.toolbar.grid(row=0, column=0, sticky="ew")
        self.toolbar.grid_columnconfigure(3, weight=1)

        # Logo/título
        ctk.CTkLabel(
            self.toolbar, text="  Contracto",
            font=get_font(FONT_SIZE_H3, "bold"), text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_XLARGE), pady=SPACING_SMALL)

        # Botões de navegação
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
        self.btn_inicio.grid(row=0, column=1, padx=2, pady=SPACING_XSMALL)

        self.btn_perfis = ctk.CTkButton(
            self.toolbar, text=" Perfis", image=self.icon_profiles, width=100,
            command=lambda: self._mostrar_tela("perfis"), **btn_style,
        )
        self.btn_perfis.grid(row=0, column=2, padx=2, pady=SPACING_XSMALL)

        self.btn_config = ctk.CTkButton(
            self.toolbar, text=" Configurações", image=self.icon_settings, width=130,
            command=lambda: self._mostrar_tela("config"), **btn_style,
        )
        self.btn_config.grid(row=0, column=4, padx=(2, SPACING_LARGE), pady=SPACING_XSMALL)

    # ==================================================================
    # GRADIENTE DE FUNDO
    # ==================================================================
    def _construir_gradiente(self) -> None:
        self.canvas_gradient = tk.Canvas(self, highlightthickness=0)
        self.canvas_gradient.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.canvas_gradient.tk.call('lower', self.canvas_gradient._w)
        self._pintar_gradiente()

    def _pintar_gradiente(self) -> None:
        largura = max(self.winfo_width(), 920)
        altura = max(self.winfo_height() - 44, 720)
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
            font=get_font(FONT_SIZE_H3, "bold"),
        )
        self.lbl_etapa1.grid(row=0, column=0, pady=SPACING_MEDIUM, sticky="e", padx=SPACING_LARGE)

        self.lbl_seta = ctk.CTkLabel(
            self.frame_stepper, text="  →  ",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED,
        )
        self.lbl_seta.grid(row=0, column=1, pady=SPACING_MEDIUM)

        self.lbl_etapa2 = ctk.CTkLabel(
            self.frame_stepper, text="2. Conversão e Organização",
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED,
        )
        self.lbl_etapa2.grid(row=0, column=2, pady=SPACING_MEDIUM, sticky="w", padx=SPACING_LARGE)

        # Perfil ativo
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        self.lbl_perfil = ctk.CTkLabel(
            self.frame_stepper, text=f"Perfil: {perfil_nome}",
            font=get_font(FONT_SIZE_CAPTION), text_color=COLOR_TEXT_SECONDARY,
        )
        self.lbl_perfil.grid(row=1, column=0, columnspan=3, pady=(0, SPACING_SMALL))

    def _atualizar_stepper(self, etapa: int) -> None:
        cor = get_color_primary()
        if etapa == 1:
            self.lbl_etapa1.configure(text_color=cor)
            self.lbl_etapa2.configure(text_color=COLOR_TEXT_DISABLED)
        else:
            self.lbl_etapa1.configure(text_color=COLOR_TEXT_DISABLED)
            self.lbl_etapa2.configure(text_color=cor)

        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        self.lbl_perfil.configure(text=f"Perfil: {perfil_nome}")

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
        normal = {"fg_color": "transparent"}
        active = {"fg_color": get_color_primary_hover()}
        self.btn_inicio.configure(**normal)
        self.btn_perfis.configure(**normal)
        self.btn_config.configure(**normal)

        self._tela_atual = tela
        
        # Grid settings for floating cards
        card_grid = {"row": 2, "column": 0, "sticky": "n", "pady": SPACING_XXLARGE}

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
        elif tela == "perfis":
            self.btn_perfis.configure(**active)
            self.frame_stepper.grid_forget()
            if not self.container_profiles:
                self.container_profiles = ProfilesFrame(self, on_voltar=lambda: self._mostrar_tela("inicio"))
                self.container_profiles.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, width=800)
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
            self.container_settings.configure(fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, width=800)
            self.container_settings.grid(**card_grid)

    def _ao_aplicar_config(self) -> None:
        """Callback chamado após salvar configurações."""
        reload_theme()
        # Atualizar toolbar
        self.toolbar.configure(fg_color=get_color_primary())
        self._pintar_gradiente()
        self._atualizar_stepper(1)
        show_toast(self, "Configurações salvas com sucesso!", "success")

    def _aplicar_perfil_ativo(self) -> None:
        """Os modelos agora são carregados a partir do perfil no momento da geração."""
        pass

    # ------------------------------------------------------------------
    # ETAPA 1: Preenchimento e Geração
    # ------------------------------------------------------------------
    def _construir_etapa1(self) -> None:
        self._construir_secao_participantes()
        self._construir_secao_saida()

        self.botao_avancar = ctk.CTkButton(
            self.container_etapa1,
            text="GERAR DOCUMENTOS E AVANÇAR",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_avancar,
        )
        self.botao_avancar.grid(row=3, column=0, padx=SPACING_LARGE,
                                 pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")

    def _construir_secao_participantes(self) -> None:
        secao = ctk.CTkFrame(self.container_etapa1, fg_color="transparent")
        secao.grid(row=0, column=0, padx=SPACING_LARGE,
                   pady=(SPACING_LARGE, SPACING_SMALL), sticky="nsew")
        secao.grid_columnconfigure(0, weight=1)
        secao.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(secao, text="Participantes",
                              font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")

        self.participantes_scroll = ctk.CTkScrollableFrame(
            secao, fg_color="transparent", label_text="",
        )
        self.participantes_scroll.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.participantes_scroll.grid_columnconfigure(0, weight=1)

        botao_adicionar = ctk.CTkButton(
            secao, text="+ Adicionar Participante",
            fg_color=COLOR_SURFACE, text_color=get_color_primary(),
            border_width=1, border_color=get_color_primary(),
            hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
            command=self._adicionar_participante,
        )
        botao_adicionar.grid(row=2, column=0, padx=0, pady=(SPACING_XLARGE, 0), sticky="w")



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
        
        ctk.CTkButton(frame_data, text="", image=self.icon_calendar, width=32, corner_radius=RADIUS_BUTTON,
                      fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_SURFACE_VARIANT,
                      command=lambda: DatePickerPopup(self, self.entry_data)).grid(row=0, column=1, padx=(SPACING_SMALL, 0))

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

        self.entry_pasta_saida = ctk.CTkEntry(frame_dir, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_INPUT)
        self.entry_pasta_saida.grid(row=0, column=0, sticky="ew")
        self.entry_pasta_saida.insert(0, str(downloads_path))
        self.entry_pasta_saida.configure(state="disabled")

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

    def _adicionar_participante(self, principal: bool = False) -> None:
        indice = len(self.participant_frames) + 1
        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        frame = ParticipantFrame(
            self.participantes_scroll,
            indice=indice,
            principal=principal,
            on_remover=None if principal else self._remover_participante,
            local_padrao=local_padrao,
        )
        frame.grid(row=indice - 1, column=0, padx=SPACING_XSMALL,
                   pady=SPACING_SMALL, sticky="ew")
        self.participant_frames.append(frame)

    def _remover_participante(self, frame: ParticipantFrame) -> None:
        frame.destroy()
        self.participant_frames.remove(frame)
        for novo_indice, restante in enumerate(self.participant_frames, start=1):
            restante.atualizar_indice(novo_indice)

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
            for f in perfil.formularios:
                if not f.caminho or not Path(f.caminho).exists():
                    erros.append(f"O formulário '{f.nome}' aponta para um arquivo inexistente: {f.caminho}")

        # 4. Validar pasta de saída e permissões
        if not self.pasta_saida:
            erros.append("Selecione a pasta de saída.")
        elif not self._verificar_permissao_escrita(self.pasta_saida):
            erros.append(f"Sem permissão de escrita na pasta de saída: {self.pasta_saida}")

        # Se houver qualquer erro, detalhar ao usuário sem prosseguir
        if erros:
            detalhes = "\n".join(f"• {e}" for e in erros)
            if len(erros) <= 2:
                show_toast(self, f"Atenção aos seguintes campos:\n{detalhes}", "error")
            else:
                messagebox.showwarning(
                    "Campos Pendentes ou Inválidos",
                    f"Não foi possível gerar os documentos. Verifique os seguintes itens:\n\n{detalhes}\n\n"
                    f"Os campos que precisam de atenção foram destacados com borda vermelha."
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

        self.botao_avancar.configure(state="disabled")
        self._loading = LoadingModal(self, "Gerando documentos...")

        thread = threading.Thread(target=self._gerar_em_background,
                                   args=(participantes,), daemon=True)
        thread.start()

    def _gerar_em_background(self, participantes):
        try:
            perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
            perfil = obter_perfil(perfil_nome)
            
            resultado = gerar_documentos(
                participantes, perfil, self.pasta_saida,
            )
            self.after(0, lambda: self._ao_concluir_geracao(resultado, participantes))
        except Exception as exc:
            self.after(0, lambda: self._ao_erro_geracao(exc))

    def _ao_concluir_geracao(self, resultado, participantes):
        if hasattr(self, "_loading"):
            self._loading.dismiss()

        self.participantes_etapa1 = participantes
        self.arquivos_gerados_etapa1 = resultado.arquivos_gerados

        if resultado.avisos:
            msg = " ".join(resultado.avisos)
            show_toast(self, f"Gerado com avisos: {msg}", "warning")
        else:
            show_toast(self, "Documentos gerados com sucesso!", "success")

        self.botao_avancar.configure(state="normal")
        self._mostrar_tela("etapa2")

    def _ao_erro_geracao(self, exc):
        if hasattr(self, "_loading"):
            self._loading.dismiss()
        self.botao_avancar.configure(state="normal")
        show_toast(self, f"Erro: {str(exc)}", "error")

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
            frame_botoes, text="FINALIZAR PROCESSO",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=get_color_primary(),
            hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON, height=48,
            command=self._ao_clicar_finalizar,
        )
        self.botao_finalizar.grid(row=0, column=1, sticky="ew")

    def _ao_clicar_finalizar(self) -> None:
        if not self.pasta_saida:
            return

        documentos_externos = self.document_frame.obter_documentos_selecionados()

        # Obter formato do perfil ativo
        perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
        perfil = obter_perfil(perfil_nome)
        formato_saida = perfil.formato_saida if perfil else "PDF/A-2b"

        self.botao_finalizar.configure(state="disabled")
        self.botao_voltar.configure(state="disabled")

        msg_loading = "Convertendo para PDF/A..." if formato_saida == "PDF/A-2b" else "Organizando documentos..."
        self._loading2 = LoadingModal(self, msg_loading)

        thread = threading.Thread(
            target=self._finalizar_em_background,
            args=(documentos_externos, formato_saida), daemon=True,
        )
        thread.start()

    def _finalizar_em_background(self, documentos_externos, formato_saida):
        try:
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

    @staticmethod
    def _atualizar_entry(entry: ctk.CTkEntry, texto: str) -> None:
        entry.configure(state="normal", text_color=COLOR_TEXT)
        entry.delete(0, "end")
        entry.insert(0, texto)
        entry.configure(state="disabled")
