"""
Tela de gerenciamento de perfis.

Similar ao sistema de perfis do PDFCreator, permite ao usuário
criar perfis pré-configurados com modelos e formato de saída.
"""

import copy
import json
import threading
import customtkinter as ctk
from pathlib import Path
from ports.dialog import salvar_arquivo, selecionar_arquivo

from ui.alert_modal import AlertModal
from ui.confirm_modal import ConfirmModal
from ui.feedback_toast import show_toast
from ui.loading_modal import LoadingModal
from ui.theme import (
    COLOR_BORDER, COLOR_ERROR, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_WARNING,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XSMALL,
    get_font, get_color_primary, get_color_primary_text, get_color_primary_hover,
    configurar_autoscroll, get_icon, configurar_janela_modal,
)
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil, FormularioModelo,
    carregar_perfis, salvar_perfis, adicionar_perfil,
    atualizar_perfil, excluir_perfil, duplicar_perfil,
    exportar_perfil, importar_perfil, problemas_estruturais,
)
from utils import config_manager
from services import pdf_service
from ui.pf_lista import ListaPerfisMixin
from ui.pf_editor import EditorPerfisMixin


class ProfilesFrame(ListaPerfisMixin, EditorPerfisMixin, ctk.CTkFrame):
    """Frame da tela de gerenciamento de perfis."""

    def __init__(self, master, on_voltar=None, on_expand=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_voltar = on_voltar
        self.on_expand = on_expand

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._perfil_editando: Perfil | None = None
        self._formularios_editando: list[FormularioModelo] = []

        self._construir_header()
        self._construir_lista_perfis()
        self._construir_editor()
        self._construir_botoes()
        self._carregar_lista()



































