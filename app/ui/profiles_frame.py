"""
Tela de gerenciamento de perfis.

Similar ao sistema de perfis do PDFCreator, permite ao usuário
criar perfis pré-configurados com modelos e formato de saída.
"""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

from ui.alert_modal import AlertModal
from ui.confirm_modal import ConfirmModal
from ui.theme import (
    COLOR_BORDER, COLOR_ERROR, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS,
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
)
from utils import config_manager
from services import pdf_service


class ProfilesFrame(ctk.CTkFrame):
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

        ctk.CTkButton(
            self.header_perfis, text=" + Novo Perfil",
            image=get_icon("save", (16, 16)), compound="left",
            width=135,
            fg_color=COLOR_SURFACE, text_color=get_color_primary_text(),
            border_width=1, border_color=get_color_primary_text(),
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            command=self._criar_novo,
        ).grid(row=0, column=1, sticky="e")

    def _construir_lista_perfis(self) -> None:
        self.scroll_perfis = ctk.CTkScrollableFrame(
            self, fg_color="transparent", label_text="",
        )
        self.scroll_perfis.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_perfis.grid_columnconfigure(0, weight=1)

    def _construir_editor(self) -> None:
        """Editor de perfil — aparece quando se clica em Editar."""
        self.frame_editor = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
            border_width=1, border_color=COLOR_BORDER
        )
        self.frame_editor.grid_columnconfigure(0, weight=1)
        self.frame_editor.grid_rowconfigure(0, weight=1)

        self.scroll_editor = ctk.CTkScrollableFrame(
            self.frame_editor, fg_color="transparent", label_text=""
        )
        self.scroll_editor.grid(row=0, column=0, sticky="nsew", padx=SPACING_SMALL, pady=SPACING_SMALL)
        self.scroll_editor.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.scroll_editor, text="Editar Perfil",
                     font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT
                     ).grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE,
                            pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        # Nome
        ctk.CTkLabel(
            self.scroll_editor, text=" Nome:",
            image=get_icon("form", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=1, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
        self.edit_nome = ctk.CTkEntry(self.scroll_editor, corner_radius=RADIUS_INPUT)
        self.edit_nome.grid(row=1, column=1, padx=(0, SPACING_LARGE),
                            pady=SPACING_SMALL, sticky="ew")

        # Formato
        ctk.CTkLabel(
            self.scroll_editor, text=" Formato:",
            image=get_icon("ratio", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=2, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
        self.edit_formato = ctk.CTkSegmentedButton(
            self.scroll_editor, values=["PDF/A-2b", "PDF"],
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
            selected_color=get_color_primary(),
            selected_hover_color=get_color_primary_hover(),
        )
        self.edit_formato.grid(row=2, column=1, padx=(0, SPACING_LARGE),
                               pady=SPACING_SMALL, sticky="ew")

        # Formulários Dinâmicos
        header_form = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_form.grid(row=3, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_form.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_form, text="Formulários Dinâmicos:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_form, text=" Adicionar Formulário PDF", image=get_icon("document", (14, 14)),
                      compound="left", width=190, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_formulario).grid(row=0, column=1, sticky="e")

        self.scroll_forms = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_forms.grid(row=4, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_forms.grid_columnconfigure(0, weight=1)

        # Documentos Extras (Etapa 2)
        header_extras = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_extras.grid(row=5, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_extras.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_extras, text="Documentos Extras (Etapa 2):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_extras, text=" Adicionar Documento", image=get_icon("contract", (14, 14)),
                      compound="left", width=175, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_documento_extra).grid(row=0, column=1, sticky="e")

        self.scroll_extras = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_extras.grid(row=6, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_extras.grid_columnconfigure(0, weight=1)

        # Campos de Entrada (Etapa 1)
        header_campos = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_campos.grid(row=7, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_campos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_campos, text="Campos de Entrada (Etapa 1):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_campos, text=" Adicionar Campo", image=get_icon("form", (14, 14)),
                      compound="left", width=160, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_campo_entrada).grid(row=0, column=1, sticky="e")

        self.scroll_campos = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_campos.grid(row=8, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_campos.grid_columnconfigure(0, weight=1)

        # Botões do editor
        frame_btns = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        frame_btns.grid(row=9, column=0, columnspan=2, padx=SPACING_LARGE,
                        pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(frame_btns, text=" Cancelar", image=get_icon("back", (14, 14)), compound="left",
                      fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
                      border_width=1, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_VARIANT,
                      corner_radius=RADIUS_BUTTON, command=self._fechar_editor
                      ).grid(row=0, column=0, padx=(0, SPACING_SMALL))

        ctk.CTkButton(frame_btns, text=" Salvar Perfil", image=get_icon("save", (16, 16), light_only=True), compound="left",
                      fg_color=get_color_primary(), text_color="#FFFFFF",
                      hover_color=get_color_primary_hover(), corner_radius=RADIUS_BUTTON,
                      command=self._salvar_edicao
                      ).grid(row=0, column=1, sticky="ew")

        configurar_autoscroll(self.scroll_editor)

    def _construir_botoes(self) -> None:
        pass

    def _carregar_lista(self) -> None:
        for widget in self.scroll_perfis.winfo_children():
            widget.destroy()

        perfis = carregar_perfis()
        perfil_ativo = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME

        for i, perfil in enumerate(perfis):
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

            if perfil.nome != PERFIL_PADRAO_NOME:
                ctk.CTkButton(frame_acoes, text="", image=get_icon("trash", (14, 14)), width=30,
                              fg_color="transparent", text_color=COLOR_ERROR,
                              hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
                              command=lambda n=perfil.nome: self._excluir(n)
                              ).pack(side="left", padx=2)

        configurar_autoscroll(self.scroll_perfis)

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

    def _criar_novo(self) -> None:
        self._perfil_editando = None
        self._abrir_editor(Perfil(nome="", formato_saida="PDF/A-2b", formularios=[]))
        self.edit_nome.configure(state="normal")

    def _abrir_editor(self, perfil: Perfil) -> None:
        from utils.profile_manager import DocumentoExtra, CampoEntrada, _campos_entrada_padrao
        self._perfil_editando = perfil
        self._formularios_editando = [FormularioModelo(f.nome, f.caminho, f.geracao, f.mapeamento.copy()) for f in perfil.formularios]
        
        doc_extras_brutos = getattr(perfil, 'documentos_extras', [])
        self._documentos_extras_editando = []
        for d in doc_extras_brutos:
            if isinstance(d, DocumentoExtra):
                self._documentos_extras_editando.append(DocumentoExtra(d.rotulo, d.nome_padrao))
            elif isinstance(d, dict):
                self._documentos_extras_editando.append(DocumentoExtra(d.get('rotulo', ''), d.get('nome_padrao', '')))

        campos_brutos = getattr(perfil, 'campos_entrada', [])
        self._campos_entrada_editando = []
        for c in (campos_brutos if campos_brutos else _campos_entrada_padrao()):
            if isinstance(c, CampoEntrada):
                self._campos_entrada_editando.append(
                    CampoEntrada(c.id, c.rotulo, c.tipo, c.obrigatorio, c.placeholder, c.escopo, list(c.opcoes), c.valor_padrao, c.icone, c.aba)
                )
            elif isinstance(c, dict):
                self._campos_entrada_editando.append(CampoEntrada(**c))

        self.edit_nome.configure(state="normal")
        self.edit_nome.delete(0, "end")
        self.edit_nome.insert(0, perfil.nome)

        self.edit_formato.set(perfil.formato_saida)
        
        self._atualizar_lista_formularios_editando()
        self._atualizar_lista_documentos_editando()
        self._atualizar_lista_campos_editando()

        self.header_perfis.grid_remove()
        self.scroll_perfis.grid_remove()
        self.frame_editor.grid(row=0, column=0, rowspan=2, padx=SPACING_LARGE, pady=SPACING_LARGE, sticky="nsew")
        self.scroll_editor._parent_canvas.yview_moveto(0)
        configurar_autoscroll(self.scroll_editor)
        if self.on_expand:
            self.on_expand(True)

    def _atualizar_lista_formularios_editando(self):
        for widget in self.scroll_forms.winfo_children():
            widget.destroy()
            
        for i, form in enumerate(self._formularios_editando):
            f_frame = ctk.CTkFrame(self.scroll_forms, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            f_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            f_frame.grid_columnconfigure(0, weight=1)
            
            nome_label = ctk.CTkLabel(f_frame, text=f"{form.nome} ({form.geracao})", font=get_font(FONT_SIZE_BODY, "bold"))
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_XSMALL)
            
            ctk.CTkButton(f_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
                          command=lambda f=form, idx=i: self._editar_formulario(f, idx)).grid(row=0, column=1, padx=SPACING_SMALL)
                          
            ctk.CTkButton(f_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_formulario(idx)).grid(row=0, column=2, padx=SPACING_SMALL)

    def _fechar_editor(self) -> None:
        self.frame_editor.grid_remove()
        self.header_perfis.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="ew")
        self.scroll_perfis.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_perfis._parent_canvas.yview_moveto(0)
        configurar_autoscroll(self.scroll_perfis)
        if self.on_expand:
            self.on_expand(False)
        self._perfil_editando = None
        self._formularios_editando = []
        self._documentos_extras_editando = []
        self._campos_entrada_editando = []
        self._carregar_lista()

    def _atualizar_lista_documentos_editando(self):
        for widget in self.scroll_extras.winfo_children():
            widget.destroy()
            
        for i, doc in enumerate(self._documentos_extras_editando):
            d_frame = ctk.CTkFrame(self.scroll_extras, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            d_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            d_frame.grid_columnconfigure(0, weight=1)
            
            nome_label = ctk.CTkLabel(d_frame, text=f"{doc.rotulo} -> {doc.nome_padrao}", font=get_font(FONT_SIZE_BODY, "bold"))
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_XSMALL)
            
            ctk.CTkButton(d_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
                          command=lambda d=doc, idx=i: self._editar_documento_extra(d, idx)).grid(row=0, column=1, padx=SPACING_SMALL)
                          
            ctk.CTkButton(d_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_documento_extra(idx)).grid(row=0, column=2, padx=SPACING_SMALL)

    def _atualizar_lista_campos_editando(self):
        for widget in self.scroll_campos.winfo_children():
            widget.destroy()
            
        for i, campo in enumerate(self._campos_entrada_editando):
            c_frame = ctk.CTkFrame(self.scroll_campos, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            c_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            c_frame.grid_columnconfigure(0, weight=1)
            
            obrig_str = " (Obrigatório)" if campo.obrigatorio else ""
            desc = f"{campo.rotulo} [{campo.tipo.upper()}] — Escopo: {campo.escopo}{obrig_str}"
            nome_label = ctk.CTkLabel(c_frame, text=desc, font=get_font(FONT_SIZE_BODY, "bold"))
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_XSMALL)
            
            ctk.CTkButton(c_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
                          command=lambda c=campo, idx=i: self._editar_campo_entrada(c, idx)).grid(row=0, column=1, padx=SPACING_SMALL)
                          
            ctk.CTkButton(c_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_campo_entrada(idx)).grid(row=0, column=2, padx=SPACING_SMALL)
    def _adicionar_campo_entrada(self) -> None:
        self._abrir_modal_campo_entrada()

    def _editar_campo_entrada(self, campo, index: int) -> None:
        self._abrir_modal_campo_entrada(campo, index)

    def _remover_campo_entrada(self, index: int) -> None:
        if 0 <= index < len(self._campos_entrada_editando):
            del self._campos_entrada_editando[index]
            self._atualizar_lista_campos_editando()

    def _abrir_modal_campo_entrada(self, campo_existente=None, index=None) -> None:
        from utils.profile_manager import CampoEntrada, TIPOS_CAMPO_ENTRADA
        if hasattr(self, "_modal_campo_fechar") and self._modal_campo_fechar:
            try:
                self._modal_campo_fechar()
            except Exception:
                pass

        root = self.winfo_toplevel()
        w, h = 520, 560

        overlay = ctk.CTkToplevel(root)
        modal = ctk.CTkToplevel(root)

        configurar_janela_modal(root, modal, overlay, w, h)

        frame = ctk.CTkFrame(
            modal,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        frame.grid_columnconfigure(0, weight=1)

        # Header do Modal
        titulo = "Editar Campo de Entrada" if campo_existente else "Novo Campo de Entrada"
        ctk.CTkLabel(
            frame,
            text=titulo,
            font=get_font(FONT_SIZE_H3, "bold"),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, 2))

        ctk.CTkLabel(
            frame,
            text="Configure o campo que será solicitado na Etapa 1 para este perfil.",
            font=get_font(FONT_SIZE_CAPTION),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(0, SPACING_MEDIUM))

        # Conteúdo do formulário
        f_campos = ctk.CTkFrame(frame, fg_color="transparent")
        f_campos.pack(fill="x", padx=SPACING_LARGE)
        f_campos.grid_columnconfigure(1, weight=1)

        # 1. Rótulo
        ctk.CTkLabel(f_campos, text="Rótulo:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=4)
        entry_rotulo = ctk.CTkEntry(f_campos, placeholder_text="Ex: CNPJ da Empresa ou Valor")
        entry_rotulo.grid(row=0, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente:
            entry_rotulo.insert(0, campo_existente.rotulo)

        # 2. ID da Variável
        ctk.CTkLabel(f_campos, text="ID da Variável:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        entry_id = ctk.CTkEntry(f_campos, placeholder_text="Ex: cnpj, valor_avaliacao")
        entry_id.grid(row=1, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente:
            entry_id.insert(0, campo_existente.id)

        # Auto-gerar ID a partir do rótulo se estiver criando novo
        if not campo_existente:
            def _ao_digitar_rotulo(event=None):
                txt = entry_rotulo.get().strip().lower()
                import re
                txt = re.sub(r"[^\w\s]", "", txt)
                txt = re.sub(r"\s+", "_", txt)
                entry_id.delete(0, "end")
                entry_id.insert(0, txt)
            entry_rotulo.bind("<KeyRelease>", _ao_digitar_rotulo)

        # 3. Tipo
        ctk.CTkLabel(f_campos, text="Tipo de Dado:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        tipos_disponiveis = TIPOS_CAMPO_ENTRADA
        tipo_var = ctk.StringVar(value=campo_existente.tipo.upper() if campo_existente else "TEXTO")
        dropdown_tipo = ctk.CTkComboBox(f_campos, values=tipos_disponiveis, variable=tipo_var, state="readonly")
        dropdown_tipo.grid(row=2, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)

        # 4. Escopo
        ctk.CTkLabel(f_campos, text="Escopo:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=4)
        escopo_var = ctk.StringVar(value=campo_existente.escopo if campo_existente else "participante")
        dropdown_escopo = ctk.CTkComboBox(f_campos, values=["participante", "global"], variable=escopo_var, state="readonly")
        dropdown_escopo.grid(row=3, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)

        # 5. Aba / Seção
        ctk.CTkLabel(f_campos, text="Aba / Seção:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=4)
        entry_aba = ctk.CTkEntry(f_campos, placeholder_text="Ex: Geral, Dados do Imóvel, etc.")
        entry_aba.grid(row=4, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        entry_aba.insert(0, campo_existente.aba if (campo_existente and campo_existente.aba) else "Geral")

        # 6. Placeholder
        ctk.CTkLabel(f_campos, text="Dica (Placeholder):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=5, column=0, sticky="w", pady=4)
        entry_placeholder = ctk.CTkEntry(f_campos, placeholder_text="Ex: Digite o valor...")
        entry_placeholder.grid(row=5, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.placeholder:
            entry_placeholder.insert(0, campo_existente.placeholder)

        # 7. Opções (para tipo selecao)
        ctk.CTkLabel(f_campos, text="Opções (Seleção):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=6, column=0, sticky="w", pady=4)
        entry_opcoes = ctk.CTkEntry(f_campos, placeholder_text="Opção 1, Opção 2, Opção 3 (separadas por vírgula)")
        entry_opcoes.grid(row=6, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.opcoes:
            entry_opcoes.insert(0, ", ".join(campo_existente.opcoes))

        # 8. Obrigatório
        obrigatorio_var = ctk.BooleanVar(value=campo_existente.obrigatorio if campo_existente else True)
        check_obrig = ctk.CTkCheckBox(f_campos, text="Preenchimento Obrigatório", variable=obrigatorio_var)
        check_obrig.grid(row=7, column=0, columnspan=2, sticky="w", pady=(SPACING_SMALL, SPACING_SMALL))

        def _fechar():
            try:
                modal.destroy()
            except Exception:
                pass
            try:
                overlay.destroy()
            except Exception:
                pass
            self._modal_campo_fechar = None

        self._modal_campo_fechar = _fechar

        def _salvar_campo():
            rotulo = entry_rotulo.get().strip()
            cid = entry_id.get().strip()
            tipo = tipo_var.get().upper()
            escopo = escopo_var.get()
            aba = entry_aba.get().strip() or "Geral"
            placeholder = entry_placeholder.get().strip()
            obrig = obrigatorio_var.get()

            if not rotulo:
                AlertModal(modal, "Campo Inválido", "O rótulo do campo é obrigatório.")
                return
            if not cid:
                AlertModal(modal, "Campo Inválido", "O ID da variável é obrigatório.")
                return

            opcoes_lista = []
            if tipo == "selecao":
                opcoes_lista = [op.strip() for op in entry_opcoes.get().split(",") if op.strip()]

            novo_campo = CampoEntrada(
                id=cid,
                rotulo=rotulo,
                tipo=tipo,
                obrigatorio=obrig,
                placeholder=placeholder,
                escopo=escopo,
                opcoes=opcoes_lista,
                aba=aba,
            )

            if index is not None and 0 <= index < len(self._campos_entrada_editando):
                self._campos_entrada_editando[index] = novo_campo
            else:
                self._campos_entrada_editando.append(novo_campo)

            self._atualizar_lista_campos_editando()
            _fechar()

        # Botões de Ação
        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.pack(fill="x", padx=SPACING_LARGE, pady=(SPACING_MEDIUM, SPACING_LARGE), side="bottom")
        botoes.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            botoes, text="Cancelar", fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
            hover_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON, command=_fechar
        ).grid(row=0, column=0, padx=(0, SPACING_SMALL))

        ctk.CTkButton(
            botoes, text="Salvar Campo", fg_color=get_color_primary(), text_color="#FFFFFF",
            hover_color=get_color_primary_hover(), corner_radius=RADIUS_BUTTON, command=_salvar_campo
        ).grid(row=0, column=1, sticky="ew")

    def _adicionar_formulario(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar Formulário PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            try:
                campos = pdf_service.obter_campos_do_formulario(Path(caminho))
            except Exception as e:
                AlertModal(self.winfo_toplevel(), "Erro ao Ler PDF", "Falha ao analisar os campos do formulário.", [str(e)])
                return
                
            self._abrir_modal_mapeamento(Path(caminho).name, caminho, list(campos))

    def _editar_formulario(self, form: FormularioModelo, index: int) -> None:
        try:
            from utils.resource_path import caminho_recurso
            caminho_real = form.caminho
            if not caminho_real:
                if "PPE" in form.nome:
                    caminho_real = caminho_recurso("assets", "templates", "PPE.pdf")
                else:
                    caminho_real = caminho_recurso("assets", "templates", "1 IMOVEL.pdf")
            campos = pdf_service.obter_campos_do_formulario(Path(caminho_real))
        except Exception as e:
            AlertModal(self.winfo_toplevel(), "Erro ao Ler PDF", "Falha ao analisar os campos do formulário.", [str(e)])
            return
            
        self._abrir_modal_mapeamento(form.nome, str(form.caminho), list(campos), form, index)

    def _remover_formulario(self, index: int) -> None:
        if 0 <= index < len(self._formularios_editando):
            del self._formularios_editando[index]
            self._atualizar_lista_formularios_editando()

    def _adicionar_documento_extra(self) -> None:
        self._abrir_modal_documento()

    def _editar_documento_extra(self, doc, index: int) -> None:
        self._abrir_modal_documento(doc, index)

    def _remover_documento_extra(self, index: int) -> None:
        if 0 <= index < len(self._documentos_extras_editando):
            del self._documentos_extras_editando[index]
            self._atualizar_lista_documentos_editando()

    def _abrir_modal_documento(self, doc_existente=None, index=None) -> None:
        from utils.profile_manager import DocumentoExtra
        if hasattr(self, "_modal_doc_fechar") and self._modal_doc_fechar:
            try:
                self._modal_doc_fechar()
            except Exception:
                pass

        root = self.winfo_toplevel()
        w, h = 500, 370

        # 1. Overlay escuro translúcido
        overlay = ctk.CTkToplevel(root)
        # 2. Cartão centralizado
        modal = ctk.CTkToplevel(root)

        configurar_janela_modal(root, modal, overlay, w, h)

        frame = ctk.CTkFrame(
            modal,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        frame.grid_columnconfigure(1, weight=1)

        def _fechar():
            self._modal_doc_fechar = None
            try:
                modal.destroy()
            except Exception:
                pass
            try:
                overlay.destroy()
            except Exception:
                pass
            try:
                root.update_idletasks()
            except Exception:
                pass

        self._modal_doc_fechar = _fechar
        overlay.bind("<Button-1>", lambda e: _fechar())
        modal.bind("<Escape>", lambda e: _fechar())
        
        # Header com botão de fechar
        header_f = ctk.CTkFrame(frame, fg_color="transparent")
        header_f.grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_MEDIUM), sticky="ew")
        header_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_f, text=" Configurar Documento Extra",
            image=get_icon("contract", (20, 20)), compound="left",
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_f, text="✕", width=32, height=32, corner_radius=8,
            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
            hover_color=COLOR_SURFACE_VARIANT, font=get_font(16, "bold"),
            command=_fechar
        ).grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            frame, text=" Rótulo (Exibição):",
            image=get_icon("contract", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="w")
        
        entry_rotulo = ctk.CTkEntry(frame, placeholder_text="Ex: Cédula de Crédito", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        entry_rotulo.grid(row=1, column=1, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        
        ctk.CTkLabel(
            frame, text=" Nome Final:",
            image=get_icon("document", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="w")
        
        entry_nome = ctk.CTkEntry(frame, placeholder_text="Ex: CEDULA DE CREDITO", corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        entry_nome.grid(row=2, column=1, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        
        ctk.CTkLabel(
            frame, text="Exemplo: Se o Nome Final for 'CONTRATO', o arquivo\ngerado será 'CONTRATO MARIA E JOAO.pdf'", 
            text_color=COLOR_TEXT_SECONDARY, font=get_font(FONT_SIZE_CAPTION), justify="left"
        ).grid(row=3, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_MEDIUM), sticky="w")
                     
        if doc_existente:
            entry_rotulo.insert(0, doc_existente.rotulo)
            entry_nome.insert(0, doc_existente.nome_padrao)
            
        def _salvar(event=None):
            rotulo = entry_rotulo.get().strip()
            nome = entry_nome.get().strip()
            if not rotulo or not nome:
                AlertModal(self, "Campos Obrigatórios", "Por favor, preencha o Rótulo e o Nome Final.", [])
                return
                
            novo_doc = DocumentoExtra(rotulo, nome)
            if doc_existente and index is not None:
                self._documentos_extras_editando[index] = novo_doc
            else:
                self._documentos_extras_editando.append(novo_doc)
                
            self._atualizar_lista_documentos_editando()
            _fechar()
            
        btn_salvar = ctk.CTkButton(
            frame, text=" Salvar Documento",
            image=get_icon("save", (16, 16), light_only=True), compound="left",
            font=get_font(FONT_SIZE_BODY, "bold"),
            fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
            corner_radius=RADIUS_BUTTON, height=38,
            command=_salvar
        )
        btn_salvar.grid(row=4, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")

        # Keyboard navigation
        entry_rotulo.bind("<Return>", lambda e: entry_nome.focus_set())
        entry_nome.bind("<Return>", lambda e: _salvar())
        entry_rotulo.focus_set()

    def _abrir_modal_mapeamento(self, nome, caminho, campos, formulario_existente=None, index=None):
        if hasattr(self, "_modal_map_fechar") and self._modal_map_fechar:
            try:
                self._modal_map_fechar()
            except Exception:
                pass

        root = self.winfo_toplevel()
        w, h = 620, 660

        # 1. Overlay escuro translúcido
        overlay = ctk.CTkToplevel(root)
        # 2. Cartão centralizado
        modal = ctk.CTkToplevel(root)

        configurar_janela_modal(root, modal, overlay, w, h)

        frame = ctk.CTkFrame(
            modal,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1)

        def _fechar():
            self._modal_map_fechar = None
            try:
                modal.destroy()
            except Exception:
                pass
            try:
                overlay.destroy()
            except Exception:
                pass
            try:
                root.update_idletasks()
            except Exception:
                pass

        self._modal_map_fechar = _fechar
        overlay.bind("<Button-1>", lambda e: _fechar())
        modal.bind("<Escape>", lambda e: _fechar())
        
        # Header com botão de fechar
        header_f = ctk.CTkFrame(frame, fg_color="transparent")
        header_f.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="ew")
        header_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_f, text=" Mapeamento de Formulário",
            image=get_icon("form", (20, 20)), compound="left",
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_f, text="✕", width=32, height=32, corner_radius=8,
            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
            hover_color=COLOR_SURFACE_VARIANT, font=get_font(16, "bold"),
            command=_fechar
        ).grid(row=0, column=1, sticky="e")

        # Nome do Formulário
        frame_nome = ctk.CTkFrame(frame, fg_color="transparent")
        frame_nome.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        frame_nome.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_nome, text="Nome:").grid(row=0, column=0, sticky="w", padx=(0, SPACING_SMALL))
        entry_nome = ctk.CTkEntry(frame_nome)
        entry_nome.grid(row=0, column=1, sticky="ew")
        entry_nome.insert(0, formulario_existente.nome if formulario_existente else nome)
        
        # Tipo de Geração
        frame_geracao = ctk.CTkFrame(frame, fg_color="transparent")
        frame_geracao.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        
        ctk.CTkLabel(frame_geracao, text="Geração:").grid(row=0, column=0, sticky="w", padx=(0, SPACING_SMALL))
        combo_geracao = ctk.CTkComboBox(frame_geracao, values=["por_participante", "unico"])
        combo_geracao.grid(row=0, column=1, sticky="w")
        if formulario_existente:
            combo_geracao.set(formulario_existente.geracao)
        else:
            combo_geracao.set("por_participante")
            
        # Mapeamento
        ctk.CTkLabel(frame, text="Mapeamento de Campos", font=get_font(FONT_SIZE_H3, "bold")).grid(row=3, column=0, pady=SPACING_SMALL, padx=SPACING_LARGE, sticky="w")
        
        scroll_map = ctk.CTkScrollableFrame(frame)
        scroll_map.grid(row=4, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        scroll_map.grid_columnconfigure(1, weight=1)
        
        variaveis = ["", "participante.nome_completo", "participante.cpf", "participante.cpf_formatado", 
                     "participante.endereco", "participante.data_assinatura", "participante.local_assinatura", 
                     "data.dia", "data.mes", "data.ano"]
                     
        mapeamento_ui = {}
        mapeamento_atual = formulario_existente.mapeamento if formulario_existente else {}
        
        for i, campo in enumerate(campos):
            ctk.CTkLabel(scroll_map, text=campo).grid(row=i, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_SMALL)
            combo = ctk.CTkComboBox(scroll_map, values=variaveis, width=250)
            combo.grid(row=i, column=1, sticky="ew", padx=SPACING_SMALL, pady=SPACING_SMALL)
            combo.set(mapeamento_atual.get(campo, ""))
            mapeamento_ui[campo] = combo

        configurar_autoscroll(scroll_map)
            
        def salvar():
            novo_mapeamento = {campo: combo.get() for campo, combo in mapeamento_ui.items() if combo.get()}
            novo_form = FormularioModelo(
                nome=entry_nome.get(),
                caminho=caminho,
                geracao=combo_geracao.get(),
                mapeamento=novo_mapeamento
            )
            
            if formulario_existente and index is not None:
                self._formularios_editando[index] = novo_form
            else:
                self._formularios_editando.append(novo_form)
                
            self._atualizar_lista_formularios_editando()
            _fechar()
            
        btn_salvar = ctk.CTkButton(frame, text="Salvar Formulário", command=salvar)
        btn_salvar.grid(row=5, column=0, pady=SPACING_LARGE, padx=SPACING_LARGE, sticky="e")

    def _salvar_edicao(self) -> None:
        nome = self.edit_nome.get().strip()
        if not nome:
            AlertModal(self.winfo_toplevel(), "Nome Obrigatório", "Por favor, informe o nome do perfil.", ["O nome do perfil não pode ficar em branco."])
            return

        perfil = Perfil(
            nome=nome,
            formularios=self._formularios_editando.copy(),
            documentos_extras=self._documentos_extras_editando.copy(),
            campos_entrada=self._campos_entrada_editando.copy(),
            formato_saida=self.edit_formato.get(),
        )

        try:
            if self._perfil_editando and self._perfil_editando.nome:
                # Editando existente
                nome_antigo = self._perfil_editando.nome
                atualizar_perfil(nome_antigo, perfil)
                
                # Se era o ativo e mudou de nome, atualiza no config
                if nome_antigo != nome and config_manager.obter("perfil_ativo") == nome_antigo:
                    config_manager.definir("perfil_ativo", nome)
            else:
                # Criando novo
                adicionar_perfil(perfil)
        except ValueError as e:
            AlertModal(self.winfo_toplevel(), "Aviso", "Não foi possível salvar o perfil.", [str(e)])
            return

        self._fechar_editor()
        self._carregar_lista()

    def _excluir(self, nome: str) -> None:
        def _confirmar_exclusao():
            try:
                excluir_perfil(nome)
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

    def atualizar_cores(self) -> None:
        """Atualiza a tela de perfis ao mudar o tema, recarregando a lista."""
        self._fechar_editor()
        self._carregar_lista()
