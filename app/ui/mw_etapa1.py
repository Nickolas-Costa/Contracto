"""Métodos de etapa1 da janela principal (mixin de MainWindow).

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



class Etapa1Mixin:
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

