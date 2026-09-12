"""Métodos de lista da tela de perfis (mixin de ProfilesFrame).

Movido verbatim de `app/ui/profiles_frame.py`: mesma ordem, mesmo código,
sem mudança de comportamento. A classe `ProfilesFrame` herda este mixin.
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



class ListaPerfisMixin:
    def _construir_header(self) -> None:
        self.header_perfis = ctk.CTkFrame(self, fg_color="transparent")
        self.header_perfis.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="ew")
        self.header_perfis.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.header_perfis, text="Perfis",
            font=get_font(FONT_SIZE_H2, "bold"),
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            self.header_perfis,
            text="Configure modelos e formato de saída para diferentes cenários.",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", pady=(SPACING_SMALL, 0))

        self.btn_novo_perfil = ctk.CTkButton(
            self.header_perfis, text=" + Novo Perfil",
            image=get_icon("save", (16, 16)), compound="left",
            width=135,
            fg_color=COLOR_SURFACE, text_color=get_color_primary_text(),
            border_width=1, border_color=get_color_primary_text(),
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            command=self._criar_novo,
        )
        self.btn_novo_perfil.grid(row=0, column=1, sticky="e")

        self.btn_importar_perfil = ctk.CTkButton(
            self.header_perfis, text=" Importar",
            image=get_icon("folder", (16, 16)), compound="left",
            width=110,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
            border_width=1, border_color=COLOR_BORDER,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            command=self._importar,
        )
        self.btn_importar_perfil.grid(row=1, column=1, sticky="e")

        frame_backup = ctk.CTkFrame(self.header_perfis, fg_color="transparent")
        frame_backup.grid(row=2, column=1, sticky="e")
        ctk.CTkButton(
            frame_backup, text=" Backup",
            image=get_icon("save", (13, 13)), compound="left",
            width=95,
            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION),
            command=self._backup,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            frame_backup, text=" Restaurar",
            image=get_icon("back", (13, 13)), compound="left",
            width=95,
            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_CAPTION),
            command=self._restaurar,
        ).pack(side="left", padx=2)

    def _construir_lista_perfis(self) -> None:
        self.scroll_perfis = ctk.CTkScrollableFrame(
            self, fg_color="transparent", label_text="",
        )
        self.scroll_perfis.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_perfis.grid_columnconfigure(0, weight=1)

    def _carregar_lista(self) -> None:
        estava_visivel = self.scroll_perfis.winfo_manager() == "grid"
        if estava_visivel:
            self.scroll_perfis.grid_remove()
        for widget in self.scroll_perfis.winfo_children():
            widget.destroy()

        perfis = carregar_perfis()
        perfil_ativo = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME

        itens = []
        for modo, titulo in (("formulario_simples", "Modo simples"), ("contrato", "Modo avançado")):
            grupo = [perfil for perfil in perfis if perfil.modo_fluxo == modo]
            if grupo:
                itens.append(titulo)
                itens.extend(grupo)

        for i, item in enumerate(itens):
            if isinstance(item, str):
                ctk.CTkLabel(
                    self.scroll_perfis, text=item,
                    font=get_font(FONT_SIZE_BODY, "bold"), text_color=get_color_primary_text(),
                ).grid(row=i, column=0, padx=SPACING_SMALL, pady=(SPACING_MEDIUM, SPACING_XSMALL), sticky="w")
                continue
            perfil = item
            card = ctk.CTkFrame(self.scroll_perfis, fg_color=COLOR_SURFACE,
                                corner_radius=RADIUS_CARD, border_width=1,
                                border_color=get_color_primary_text() if perfil.nome == perfil_ativo else COLOR_BORDER)
            card.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            icone_card = "save" if perfil.nome == perfil_ativo else "bookmark"
            ctk.CTkLabel(
                card,
                text="",
                image=get_icon(icone_card, (20, 20)),
            ).grid(row=0, column=0, rowspan=2, padx=SPACING_LARGE, pady=SPACING_MEDIUM)

            ctk.CTkLabel(card, text=perfil.nome, font=get_font(FONT_SIZE_H3, "bold"),
                         text_color=COLOR_TEXT).grid(row=0, column=1, sticky="w", pady=(SPACING_MEDIUM, 0))

            detalhes = f"Formato: {perfil.formato_saida}"
            if perfil.usa_modelos_embutidos():
                detalhes += "  •  Modelos embutidos"
            else:
                detalhes += f"  •  {len(perfil.formularios)} Formulário(s)"

            ctk.CTkLabel(card, text=detalhes, font=get_font(FONT_SIZE_CAPTION),
                         text_color=COLOR_TEXT_SECONDARY).grid(row=1, column=1, sticky="w",
                                                                 pady=(0, SPACING_MEDIUM))

            frame_acoes = ctk.CTkFrame(card, fg_color="transparent")
            frame_acoes.grid(row=0, column=2, rowspan=2, padx=SPACING_LARGE, pady=SPACING_MEDIUM)

            if perfil.nome != perfil_ativo:
                ctk.CTkButton(frame_acoes, text=" Ativar", image=get_icon("check", (13, 13), light_only=True), compound="left",
                              width=75,
                              fg_color=get_color_primary(), text_color="#FFFFFF", hover_color="#004785",
                              corner_radius=RADIUS_BUTTON, font=get_font(FONT_SIZE_CAPTION),
                              command=lambda n=perfil.nome: self._ativar_perfil(n)
                              ).pack(side="left", padx=2)

            ctk.CTkButton(frame_acoes, text=" Editar", image=get_icon("edit", (13, 13)), compound="left",
                          width=75,
                          fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
                          hover_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
                          font=get_font(FONT_SIZE_CAPTION),
                          command=lambda p=perfil: self._abrir_editor(p)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(frame_acoes, text=" Duplicar", image=get_icon("copy", (13, 13)), compound="left",
                          width=85,
                          fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
                          hover_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
                          font=get_font(FONT_SIZE_CAPTION),
                          command=lambda n=perfil.nome: self._duplicar(n)
                          ).pack(side="left", padx=2)

            ctk.CTkButton(frame_acoes, text=" Exportar", image=get_icon("save", (13, 13)), compound="left",
                          width=85,
                          fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
                          hover_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
                          font=get_font(FONT_SIZE_CAPTION),
                          command=lambda n=perfil.nome: self._exportar(n)
                          ).pack(side="left", padx=2)

            if perfil.nome != PERFIL_PADRAO_NOME:
                ctk.CTkButton(frame_acoes, text="", image=get_icon("trash", (14, 14)), width=30,
                              fg_color="transparent", text_color=COLOR_ERROR,
                              hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
                              command=lambda n=perfil.nome: self._excluir(n)
                              ).pack(side="left", padx=2)

        configurar_autoscroll(self.scroll_perfis)
        if estava_visivel:
            self.scroll_perfis.grid()

    def _ativar_perfil(self, nome: str) -> None:
        config_manager.definir("perfil_ativo", nome)
        self._carregar_lista()

    def _duplicar(self, nome: str) -> None:
        try:
            novo = duplicar_perfil(nome)
            self._carregar_lista()
            self._abrir_editor(novo)
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Duplicar", "Não foi possível duplicar o perfil.", [str(e)])

    def _exportar(self, nome: str) -> None:
        """Grava o perfil em `.json` no local escolhido."""
        destino = salvar_arquivo(
            "Exportar perfil",
            f"{nome}.json",
            [("Perfil do Contracto", "*.json")],
            ".json",
        )
        if not destino:
            return
        try:
            exportar_perfil(nome, destino)
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Exportar", "Não foi possível exportar o perfil.", [str(e)])
            return
        show_toast(self.winfo_toplevel(), f"Perfil '{nome}' exportado.", "success")

    def _importar(self) -> None:
        """Lê um `.json` de perfil, valida e incorpora com nome único."""
        origem = selecionar_arquivo(
            "Importar perfil",
            [("Perfil do Contracto", "*.json")],
        )
        if not origem:
            return
        try:
            novo = importar_perfil(origem)
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Importar", "Não foi possível importar o perfil.", [str(e)])
            return
        self._carregar_lista()
        self._abrir_editor(novo)

    def _backup(self) -> None:
        """Gera o ZIP de segurança de perfis e configurações."""
        from ui.feedback_toast import show_toast
        from utils import backup as backup_mod

        try:
            caminho = backup_mod.criar_backup()
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Backup", "Não foi possível gerar o backup.", [str(e)])
            return
        show_toast(self.winfo_toplevel(), f"Backup gerado: {caminho.name}.", "success")

    def _restaurar(self) -> None:
        """Restaura perfis e configurações a partir de um ZIP de backup."""
        from utils import backup as backup_mod

        origem = selecionar_arquivo(
            "Restaurar backup",
            [("Backup do Contracto", "*.zip")],
        )
        if not origem:
            return
        try:
            backup_mod.restaurar_backup(origem)
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Restaurar", "Não foi possível restaurar o backup.", [str(e)])
            return
        self._carregar_lista()

    def _excluir(self, nome: str) -> None:
        def _confirmar_exclusao():
            try:
                excluir_perfil(nome)
                selecionados = config_manager.obter("formularios_basicos_selecionados") or []
                if nome in selecionados:
                    config_manager.definir(
                        "formularios_basicos_selecionados",
                        [item for item in selecionados if item != nome],
                    )
                # Se era o ativo, voltar ao padrão
                if config_manager.obter("perfil_ativo") == nome:
                    config_manager.definir("perfil_ativo", PERFIL_PADRAO_NOME)
                self._carregar_lista()
            except ValueError as e:
                AlertModal(self.winfo_toplevel(), "Erro ao Excluir", "Não foi possível remover o perfil.", [str(e)])

        ConfirmModal(
            self.winfo_toplevel(),
            titulo="Excluir Perfil",
            subtitulo=f"Tem certeza que deseja excluir permanentemente o perfil '{nome}'?",
            on_confirm=_confirmar_exclusao,
            texto_confirmar="Excluir Perfil",
            texto_cancelar="Cancelar",
        )

