"""Métodos de modos da janela principal (mixin de MainWindow).

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



class ModosMixin:
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

