"""
Tela de gerenciamento de perfis.

Similar ao sistema de perfis do PDFCreator, permite ao usuário
criar perfis pré-configurados com modelos e formato de saída.
"""

import copy
import json
import threading
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

from ui.alert_modal import AlertModal
from ui.confirm_modal import ConfirmModal
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
)
from utils import config_manager
from services import pdf_service

ROTULOS_TIPOS = {
    "TEXTO": "Texto", "TEXTO_LONGO": "Texto longo", "CPF": "CPF", "CNPJ": "CNPJ",
    "CPF_CNPJ": "CPF ou CNPJ", "PIS_PASEP": "PIS/PASEP", "DATA": "Data",
    "MOEDA": "Moeda", "AREA": "Área", "INTEIRO": "Número inteiro", "ANO": "Ano",
    "TELEFONE": "Telefone", "EMAIL": "E-mail", "SELECAO": "Lista de opções",
    "CHECKBOX": "Caixa de seleção",
}
TIPOS_POR_ROTULO = {rotulo: tipo for tipo, rotulo in ROTULOS_TIPOS.items()}
ROTULOS_GERACAO = {
    "por_participante": "Um por participante",
    "por_processo": "Um por processo",
    "unico": "Um por processo",
}


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

        # Modo de uso
        ctk.CTkLabel(
            self.scroll_editor, text=" Modo:",
            image=get_icon("grid_sections", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=3, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
        self.edit_modo = ctk.CTkSegmentedButton(
            self.scroll_editor, values=["Simples", "Avançado"],
            font=get_font(FONT_SIZE_BODY), corner_radius=RADIUS_BUTTON,
            selected_color=get_color_primary(), selected_hover_color=get_color_primary_hover(),
        )
        self.edit_modo.grid(row=3, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")

        # Máximo de Participantes
        ctk.CTkLabel(
            self.scroll_editor, text=" Participantes:",
            image=get_icon("person", (16, 16)), compound="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT
        ).grid(row=4, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
        self.edit_max_participantes = ctk.CTkSegmentedButton(
            self.scroll_editor, values=["1", "2", "3", "4"],
            font=get_font(FONT_SIZE_BODY),
            corner_radius=RADIUS_BUTTON,
            selected_color=get_color_primary(),
            selected_hover_color=get_color_primary_hover(),
        )
        self.edit_max_participantes.grid(row=4, column=1, padx=(0, SPACING_LARGE),
                                         pady=SPACING_SMALL, sticky="ew")

        self.edit_usar_paginacao = ctk.CTkCheckBox(
            self.scroll_editor,
            text="Dividir os campos em páginas",
            font=get_font(FONT_SIZE_BODY),
        )
        self.edit_usar_paginacao.grid(row=5, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="w")

        # Formulários Dinâmicos
        header_form = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_form.grid(row=6, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_form.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_form, text="Formulários PDF:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_form, text=" Adicionar Formulário PDF", image=get_icon("document", (14, 14)),
                      compound="left", width=190, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_formulario).grid(row=0, column=1, sticky="e")

        self.scroll_forms = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_forms.grid(row=7, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_forms.grid_columnconfigure(0, weight=1)

        # Documentos Extras (Etapa 2)
        header_extras = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_extras.grid(row=8, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_extras.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_extras, text="Documentos Extras (Etapa 2):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_extras, text=" Adicionar Documento", image=get_icon("contract", (14, 14)),
                      compound="left", width=175, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_documento_extra).grid(row=0, column=1, sticky="e")

        self.scroll_extras = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_extras.grid(row=9, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_extras.grid_columnconfigure(0, weight=1)

        # Campos preenchidos pelo usuário
        header_campos = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        header_campos.grid(row=10, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_campos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_campos, text="Campos para preenchimento:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_campos, text=" Adicionar Campo", image=get_icon("form", (14, 14)),
                      compound="left", width=160, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_campo_entrada).grid(row=0, column=1, sticky="e")

        self.scroll_campos = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        self.scroll_campos.grid(row=11, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        self.scroll_campos.grid_columnconfigure(0, weight=1)

        # Botões do editor
        frame_btns = ctk.CTkFrame(self.scroll_editor, fg_color="transparent")
        frame_btns.grid(row=12, column=0, columnspan=2, padx=SPACING_LARGE,
                        pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(frame_btns, text=" Cancelar", image=get_icon("back", (14, 14)), compound="left",
                      fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
                      border_width=1, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_VARIANT,
                      corner_radius=RADIUS_BUTTON, command=self._fechar_editor
                      ).grid(row=0, column=0, padx=(0, SPACING_SMALL))

        self.btn_salvar_perfil = ctk.CTkButton(
            frame_btns, text=" Salvar Perfil", image=get_icon("save", (16, 16), light_only=True), compound="left",
            fg_color=get_color_primary(), text_color="#FFFFFF",
            hover_color=get_color_primary_hover(), corner_radius=RADIUS_BUTTON,
            command=self._salvar_edicao
        )
        self.btn_salvar_perfil.grid(row=0, column=1, sticky="ew")

        configurar_autoscroll(self.scroll_editor)

    def _construir_botoes(self) -> None:
        pass

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

    def _criar_novo(self) -> None:
        self._perfil_editando = None
        self._abrir_editor(Perfil(nome="", formato_saida="PDF/A-2b", formularios=[]))
        self.edit_nome.configure(state="normal")

    def _abrir_editor(self, perfil: Perfil) -> None:
        from utils.profile_manager import DocumentoExtra, CampoEntrada
        self._perfil_editando = perfil
        self._formularios_editando = [FormularioModelo(f.nome, f.caminho, f.geracao, copy.deepcopy(f.mapeamento), f.identificador, f.recurso) for f in perfil.formularios]
        
        doc_extras_brutos = getattr(perfil, 'documentos_extras', [])
        self._documentos_extras_editando = []
        for d in doc_extras_brutos:
            if isinstance(d, DocumentoExtra):
                self._documentos_extras_editando.append(DocumentoExtra(d.rotulo, d.nome_padrao))
            elif isinstance(d, dict):
                self._documentos_extras_editando.append(DocumentoExtra(d.get('rotulo', ''), d.get('nome_padrao', '')))

        campos_brutos = getattr(perfil, 'campos_entrada', [])
        self._campos_entrada_editando = []
        for c in campos_brutos:
            if isinstance(c, CampoEntrada):
                self._campos_entrada_editando.append(
                    CampoEntrada(
                        c.id, c.rotulo, c.tipo, c.obrigatorio, c.placeholder, c.escopo,
                        list(c.opcoes), c.valor_padrao, c.icone, c.aba, c.ajuda,
                        c.minimo, c.maximo, [dict(condicao) for condicao in c.visivel_quando],
                        c.limpar_quando_oculto, c.calculo, c.ate_participante,
                    )
                )
            elif isinstance(c, dict):
                self._campos_entrada_editando.append(CampoEntrada(**c))

        self.edit_nome.configure(state="normal")
        self.edit_nome.delete(0, "end")
        self.edit_nome.insert(0, perfil.nome)

        self.edit_formato.set(perfil.formato_saida)
        self.edit_max_participantes.set(str(getattr(perfil, "max_participantes", 4) or 4))
        self.edit_modo.set("Simples" if perfil.modo_fluxo == "formulario_simples" else "Avançado")
        if getattr(perfil, "usar_paginacao", False):
            self.edit_usar_paginacao.select()
        else:
            self.edit_usar_paginacao.deselect()
        
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
        estava_visivel = self.scroll_forms.winfo_manager() == "grid"
        if estava_visivel:
            self.scroll_forms.grid_remove()
        for widget in self.scroll_forms.winfo_children():
            widget.destroy()
            
        for i, form in enumerate(self._formularios_editando):
            f_frame = ctk.CTkFrame(self.scroll_forms, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            f_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            f_frame.grid_columnconfigure(0, weight=1)
            
            nome_label = ctk.CTkLabel(
                f_frame, text=f"{form.nome} • {ROTULOS_GERACAO.get(form.geracao, form.geracao)}",
                font=get_font(FONT_SIZE_BODY, "bold"),
            )
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_XSMALL)
            
            ctk.CTkButton(f_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
                          command=lambda f=form, idx=i: self._editar_formulario(f, idx)).grid(row=0, column=1, padx=SPACING_SMALL)

            ctk.CTkButton(f_frame, text="Conferir", width=70, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                          command=lambda f=form: self._conferir_formulario(f)).grid(row=0, column=2, padx=SPACING_SMALL)

            ctk.CTkButton(f_frame, text="Trocar PDF", width=78, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                          command=lambda f=form, idx=i: self._substituir_pdf_formulario(f, idx)).grid(row=0, column=3, padx=SPACING_SMALL)
                          
            ctk.CTkButton(f_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_formulario(idx)).grid(row=0, column=4, padx=SPACING_SMALL)
        if estava_visivel:
            self.scroll_forms.grid()

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
        estava_visivel = self.scroll_extras.winfo_manager() == "grid"
        if estava_visivel:
            self.scroll_extras.grid_remove()
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
        if estava_visivel:
            self.scroll_extras.grid()

    def _atualizar_lista_campos_editando(self):
        estava_visivel = self.scroll_campos.winfo_manager() == "grid"
        if estava_visivel:
            self.scroll_campos.grid_remove()
        for widget in self.scroll_campos.winfo_children():
            widget.destroy()
            
        for i, campo in enumerate(self._campos_entrada_editando):
            c_frame = ctk.CTkFrame(self.scroll_campos, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            c_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_XSMALL, sticky="ew")
            c_frame.grid_columnconfigure(0, weight=1)
            
            obrig_str = " (Obrigatório)" if campo.obrigatorio else ""
            uso = "Por participante" if campo.escopo == "participante" else "Uma vez no formulário"
            desc = f"{campo.rotulo} [{ROTULOS_TIPOS.get(campo.tipo.upper(), campo.tipo)}] • {uso}{obrig_str}"
            nome_label = ctk.CTkLabel(c_frame, text=desc, font=get_font(FONT_SIZE_BODY, "bold"))
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_XSMALL)
            
            ctk.CTkButton(c_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=get_color_primary(), text_color="#FFFFFF", hover_color=get_color_primary_hover(),
                          command=lambda c=campo, idx=i: self._editar_campo_entrada(c, idx)).grid(row=0, column=1, padx=SPACING_SMALL)
                          
            ctk.CTkButton(c_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_campo_entrada(idx)).grid(row=0, column=2, padx=SPACING_SMALL)
        if estava_visivel:
            self.scroll_campos.grid()
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
        w, h = 650, 800

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

        # 2. Nome interno
        ctk.CTkLabel(f_campos, text="Nome interno:", font=get_font(FONT_SIZE_BODY, "bold"),
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
        ctk.CTkLabel(f_campos, text="Tipo do campo:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        tipos_disponiveis = [ROTULOS_TIPOS[tipo] for tipo in TIPOS_CAMPO_ENTRADA]
        tipo_inicial = ROTULOS_TIPOS.get(campo_existente.tipo.upper(), campo_existente.tipo) if campo_existente else ROTULOS_TIPOS["TEXTO"]
        tipo_var = ctk.StringVar(value=tipo_inicial)
        dropdown_tipo = ctk.CTkComboBox(f_campos, values=tipos_disponiveis, variable=tipo_var, state="readonly")
        dropdown_tipo.grid(row=2, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)

        # 4. Escopo
        ctk.CTkLabel(f_campos, text="Usado por:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=3, column=0, sticky="w", pady=4)
        escopo_inicial = "Por participante" if not campo_existente or campo_existente.escopo == "participante" else "Uma vez no formulário"
        escopo_var = ctk.StringVar(value=escopo_inicial)
        dropdown_escopo = ctk.CTkComboBox(
            f_campos, values=["Por participante", "Uma vez no formulário"],
            variable=escopo_var, state="readonly",
        )
        dropdown_escopo.grid(row=3, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)

        # 5. Página ou seção
        ctk.CTkLabel(f_campos, text="Página ou seção:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=4, column=0, sticky="w", pady=4)
        entry_aba = ctk.CTkEntry(f_campos, placeholder_text="Ex: Dados do Vendedor, Valores da Operação, etc.")
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

        ctk.CTkLabel(f_campos, text="Ajuda abaixo do campo:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=7, column=0, sticky="w", pady=4)
        entry_ajuda = ctk.CTkEntry(f_campos, placeholder_text="Orientação curta para o usuário")
        entry_ajuda.grid(row=7, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.ajuda:
            entry_ajuda.insert(0, campo_existente.ajuda)

        ctk.CTkLabel(f_campos, text="Valor padrão:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=8, column=0, sticky="w", pady=4)
        entry_padrao = ctk.CTkEntry(f_campos)
        entry_padrao.grid(row=8, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.valor_padrao:
            entry_padrao.insert(0, campo_existente.valor_padrao)

        ctk.CTkLabel(f_campos, text="Mínimo / Máximo:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=9, column=0, sticky="w", pady=4)
        frame_faixa = ctk.CTkFrame(f_campos, fg_color="transparent")
        frame_faixa.grid(row=9, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        entry_minimo = ctk.CTkEntry(frame_faixa, placeholder_text="mínimo", width=100)
        entry_maximo = ctk.CTkEntry(frame_faixa, placeholder_text="máximo", width=100)
        entry_minimo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        entry_maximo.pack(side="left", fill="x", expand=True, padx=(4, 0))
        if campo_existente and campo_existente.minimo is not None:
            entry_minimo.insert(0, str(campo_existente.minimo))
        if campo_existente and campo_existente.maximo is not None:
            entry_maximo.insert(0, str(campo_existente.maximo))

        ctk.CTkLabel(f_campos, text="Regra de exibição (avançado):", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=10, column=0, sticky="w", pady=4)
        entry_condicoes = ctk.CTkEntry(f_campos, placeholder_text='Ex: [{"possuiImovel": ["SIM"]}]')
        entry_condicoes.grid(row=10, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.visivel_quando:
            entry_condicoes.insert(0, json.dumps(campo_existente.visivel_quando, ensure_ascii=False))

        ctk.CTkLabel(f_campos, text="Cálculo automático:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=11, column=0, sticky="w", pady=4)
        entry_calculo = ctk.CTkEntry(
            f_campos,
            placeholder_text="Ex: valor_total - entrada + adicional",
        )
        entry_calculo.grid(row=11, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)
        if campo_existente and campo_existente.calculo:
            entry_calculo.insert(0, campo_existente.calculo)

        ctk.CTkLabel(f_campos, text="Exibir até:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=12, column=0, sticky="w", pady=4)
        limite_var = ctk.StringVar(
            value=(f"Participante {campo_existente.ate_participante}"
                   if campo_existente and campo_existente.ate_participante else "Todos os participantes")
        )
        limite_participante = ctk.CTkComboBox(
            f_campos,
            values=["Todos os participantes", "Participante 1", "Participante 2", "Participante 3", "Participante 4"],
            variable=limite_var,
            state="readonly",
        )
        limite_participante.grid(row=12, column=1, sticky="ew", padx=(SPACING_SMALL, 0), pady=4)

        # Obrigatório
        obrigatorio_var = ctk.BooleanVar(value=campo_existente.obrigatorio if campo_existente else True)
        check_obrig = ctk.CTkCheckBox(f_campos, text="Preenchimento Obrigatório", variable=obrigatorio_var)
        check_obrig.grid(row=13, column=0, columnspan=2, sticky="w", pady=(SPACING_SMALL, SPACING_SMALL))

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
            tipo = TIPOS_POR_ROTULO.get(tipo_var.get(), "TEXTO")
            escopo = "participante" if escopo_var.get() == "Por participante" else "global"
            aba = entry_aba.get().strip() or "Geral"
            placeholder = entry_placeholder.get().strip()
            obrig = obrigatorio_var.get()

            if not rotulo:
                AlertModal(modal, "Campo Inválido", "O rótulo do campo é obrigatório.")
                return
            if not cid:
                AlertModal(modal, "Campo Inválido", "O nome interno é obrigatório.")
                return
            import re
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", cid):
                AlertModal(modal, "Campo Inválido", "Use um ID estável com letras, números e sublinhado, sem espaços.")
                return
            if any(c.id == cid and pos != index for pos, c in enumerate(self._campos_entrada_editando)):
                AlertModal(modal, "Campo Duplicado", f"Já existe um campo com o ID '{cid}' neste perfil.")
                return

            from services.field_calculator import validar_calculo
            if not validar_calculo(entry_calculo.get()):
                AlertModal(
                    modal,
                    "Cálculo Inválido",
                    "Use somente nomes internos de campos ligados por + ou -.",
                )
                return

            opcoes_lista = []
            if tipo == "SELECAO":
                opcoes_lista = [op.strip() for op in entry_opcoes.get().split(",") if op.strip()]

            try:
                minimo = int(entry_minimo.get()) if entry_minimo.get().strip() else None
                maximo = int(entry_maximo.get()) if entry_maximo.get().strip() else None
                condicoes = json.loads(entry_condicoes.get()) if entry_condicoes.get().strip() else []
                if not isinstance(condicoes, list):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                AlertModal(modal, "Configuração Inválida", "Faixa numérica ou condição de visibilidade inválida.")
                return

            novo_campo = CampoEntrada(
                id=cid,
                rotulo=rotulo,
                tipo=tipo,
                obrigatorio=obrig,
                placeholder=placeholder,
                escopo=escopo,
                opcoes=opcoes_lista,
                valor_padrao=entry_padrao.get().strip(),
                aba=aba,
                ajuda=entry_ajuda.get().strip(),
                minimo=minimo,
                maximo=maximo,
                visivel_quando=condicoes,
                calculo=entry_calculo.get().strip(),
                ate_participante=(
                    int(limite_var.get().rsplit(" ", 1)[-1])
                    if limite_var.get().startswith("Participante ") else None
                ),
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
            self._ler_campos_pdf(
                Path(caminho),
                lambda campos: self._abrir_modal_mapeamento(Path(caminho).name, caminho, campos),
            )

    def _editar_formulario(self, form: FormularioModelo, index: int) -> None:
        from services.generator_service import resolver_caminho_formulario
        caminho_real = resolver_caminho_formulario(form)
        if not caminho_real:
            AlertModal(self.winfo_toplevel(), "PDF não encontrado", "O arquivo usado por este formulário não foi encontrado.")
            return
        self._ler_campos_pdf(
            Path(caminho_real),
            lambda campos: self._abrir_modal_mapeamento(form.nome, str(form.caminho), campos, form, index),
        )

    def _substituir_pdf_formulario(self, form: FormularioModelo, index: int) -> None:
        """Troca o arquivo do modelo e reaproveita regras dos campos ainda existentes."""
        caminho = filedialog.askopenfilename(
            title=f"Substituir PDF de {form.nome}",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return
        self._ler_campos_pdf(
            Path(caminho),
            lambda campos: self._abrir_modal_mapeamento(form.nome, caminho, campos, form, index),
        )

    def _conferir_formulario(self, form: FormularioModelo) -> None:
        from services.generator_service import resolver_caminho_formulario

        caminho = resolver_caminho_formulario(form)
        if not caminho:
            AlertModal(self.winfo_toplevel(), "PDF não encontrado", "O arquivo usado por este formulário não foi encontrado.")
            return
        self._ler_campos_pdf(
            Path(caminho),
            lambda campos: self._mostrar_conferencia_mapeamento(form, campos),
        )

    def _mostrar_conferencia_mapeamento(self, form: FormularioModelo, campos_pdf: dict) -> None:
        from services.generator_service import obter_mapeamento_formulario, resolver_caminho_formulario
        from services.mapping_audit import conferir_mapeamento, renderizar_pagina_destacada

        mapeamento = obter_mapeamento_formulario(form)
        conferencia = conferir_mapeamento(campos_pdf, mapeamento)

        overlay = ctk.CTkToplevel(self.winfo_toplevel())
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        configurar_janela_modal(self.winfo_toplevel(), modal, overlay, 1120, 760)
        painel = ctk.CTkFrame(modal, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER)
        painel.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            painel, text=f"Conferência do PDF - {form.nome}",
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(SPACING_LARGE, 3))
        resumo = (
            f"{len(conferencia.ligados)} ligados corretamente  •  "
            f"{len(conferencia.sem_ligacao)} sem ligação  •  "
            f"{len(conferencia.nao_encontrados) + len(conferencia.estados_invalidos)} incompatíveis"
        )
        ctk.CTkLabel(
            painel, text=resumo, font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=SPACING_LARGE, pady=(0, SPACING_MEDIUM))

        corpo = ctk.CTkFrame(painel, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=SPACING_LARGE, pady=(0, SPACING_MEDIUM))
        corpo.grid_columnconfigure(0, weight=3)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        quadro_previa = ctk.CTkFrame(corpo, fg_color=COLOR_SURFACE_VARIANT)
        quadro_previa.grid(row=0, column=0, padx=(0, SPACING_SMALL), sticky="nsew")
        quadro_previa.grid_columnconfigure(0, weight=1)
        quadro_previa.grid_rowconfigure(0, weight=1)
        label_previa = ctk.CTkLabel(
            quadro_previa, text="Preparando prévia...", text_color=COLOR_TEXT_SECONDARY,
        )
        label_previa.grid(row=0, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL)
        navegacao = ctk.CTkFrame(quadro_previa, fg_color="transparent")
        navegacao.grid(row=1, column=0, pady=(0, SPACING_SMALL))

        lista = ctk.CTkScrollableFrame(corpo, fg_color=COLOR_SURFACE_VARIANT)
        lista.grid(row=0, column=1, padx=(SPACING_SMALL, 0), sticky="nsew")
        lista.grid_columnconfigure(0, weight=1)
        linhas = []
        linhas.extend((nome, "Ligado", COLOR_SUCCESS) for nome in conferencia.ligados)
        linhas.extend((nome, "Sem ligação", COLOR_WARNING) for nome in conferencia.sem_ligacao)
        linhas.extend((nome, "Não encontrado no PDF", COLOR_ERROR) for nome in conferencia.nao_encontrados)
        linhas.extend((nome, "Estado não aceito pelo PDF", COLOR_ERROR) for nome in conferencia.estados_invalidos)
        for indice, (nome, situacao, cor) in enumerate(linhas):
            ctk.CTkLabel(
                lista, text=nome, anchor="w", font=get_font(FONT_SIZE_CAPTION),
                text_color=COLOR_TEXT,
            ).grid(row=indice, column=0, padx=SPACING_SMALL, pady=4, sticky="ew")
            ctk.CTkLabel(
                lista, text=situacao, font=get_font(FONT_SIZE_CAPTION, "bold"),
                text_color=cor,
            ).grid(row=indice, column=1, padx=SPACING_SMALL, pady=4, sticky="e")

        estado_previa = {"pagina": 0, "total": 1, "imagem": None, "carregando": False}

        def carregar_previa(indice_pagina: int) -> None:
            if estado_previa["carregando"]:
                return
            estado_previa["carregando"] = True
            label_previa.configure(text="Carregando página...", image=None)

            def trabalho_previa():
                try:
                    imagem, total = renderizar_pagina_destacada(
                        Path(resolver_caminho_formulario(form)), indice_pagina, conferencia,
                    )
                    erro = None
                except (OSError, ValueError, RuntimeError) as exc:
                    imagem, total, erro = None, 1, str(exc)

                def finalizar_previa():
                    if not modal.winfo_exists():
                        return
                    estado_previa["carregando"] = False
                    if erro:
                        label_previa.configure(text=f"Prévia indisponível: {erro}", image=None)
                        return
                    estado_previa["pagina"] = indice_pagina
                    estado_previa["total"] = total
                    imagem_ctk = ctk.CTkImage(
                        light_image=imagem, dark_image=imagem, size=imagem.size,
                    )
                    estado_previa["imagem"] = imagem_ctk
                    label_previa.configure(text="", image=imagem_ctk)
                    label_indice.configure(text=f"{indice_pagina + 1} de {total}")
                    btn_anterior.configure(state="normal" if indice_pagina > 0 else "disabled")
                    btn_proxima.configure(state="normal" if indice_pagina < total - 1 else "disabled")

                try:
                    self.after(0, finalizar_previa)
                except Exception:
                    pass

            threading.Thread(target=trabalho_previa, daemon=True).start()

        btn_anterior = ctk.CTkButton(
            navegacao, text="←", width=42,
            command=lambda: carregar_previa(estado_previa["pagina"] - 1),
        )
        btn_anterior.pack(side="left", padx=3)
        label_indice = ctk.CTkLabel(navegacao, text="1 de 1", width=70)
        label_indice.pack(side="left", padx=3)
        btn_proxima = ctk.CTkButton(
            navegacao, text="→", width=42,
            command=lambda: carregar_previa(estado_previa["pagina"] + 1),
        )
        btn_proxima.pack(side="left", padx=3)
        carregar_previa(0)

        def fechar():
            try:
                modal.destroy()
            except Exception:
                pass
            try:
                overlay.destroy()
            except Exception:
                pass

        ctk.CTkButton(painel, text="Fechar", command=fechar).pack(
            anchor="e", padx=SPACING_LARGE, pady=(0, SPACING_LARGE)
        )
        overlay.bind("<Button-1>", lambda _evento: fechar())
        modal.bind("<Escape>", lambda _evento: fechar())

    def _ler_campos_pdf(self, caminho: Path, ao_concluir) -> None:
        """Lê o PDF fora da interface para manter a tela respondendo."""
        carregando = LoadingModal(
            self.winfo_toplevel(),
            message="Lendo o formulário...",
            submessage="Preparando os campos para configuração.",
        )

        def trabalho():
            try:
                resultado = pdf_service.obter_detalhes_campos(caminho)
                erro = None
            except Exception as exc:
                resultado = None
                erro = str(exc)

            def finalizar():
                carregando.dismiss()
                if erro:
                    AlertModal(
                        self.winfo_toplevel(),
                        "Erro ao Ler PDF",
                        "Falha ao analisar os campos do formulário.",
                        [erro],
                    )
                else:
                    ao_concluir(resultado)

            try:
                self.after(0, finalizar)
            except Exception:
                pass

        threading.Thread(target=trabalho, daemon=True).start()

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
        carregamentos_pendentes = set()

        def _fechar():
            self._modal_map_fechar = None
            for timer in list(carregamentos_pendentes):
                try:
                    modal.after_cancel(timer)
                except Exception:
                    pass
            carregamentos_pendentes.clear()
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
        combo_geracao = ctk.CTkComboBox(frame_geracao, values=["Um por participante", "Um por processo"])
        combo_geracao.grid(row=0, column=1, sticky="w")
        if formulario_existente:
            combo_geracao.set(ROTULOS_GERACAO.get(formulario_existente.geracao, "Um por participante"))
        else:
            combo_geracao.set("Um por participante")
            
        # Mapeamento
        ctk.CTkLabel(frame, text="Mapeamento de Campos", font=get_font(FONT_SIZE_H3, "bold")).grid(row=3, column=0, pady=SPACING_SMALL, padx=SPACING_LARGE, sticky="w")
        
        scroll_map = ctk.CTkScrollableFrame(frame)
        scroll_map.grid(row=4, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        scroll_map.grid_columnconfigure(1, weight=1)
        
        variaveis = ["", "participante.nome_completo", "participante.cpf", "participante.endereco",
                     "participante.data_assinatura", "participante.local_assinatura",
                     "data.dia", "data.mes", "data.ano"]
        for campo_entrada in self._campos_entrada_editando:
            prefixo = "global" if campo_entrada.escopo == "global" else "participante"
            variaveis.append(f"{prefixo}.{campo_entrada.id}")
        for indice_part in range(1, 5):
            variaveis.extend([
                f"participante.{indice_part}.nome_completo",
                f"participante.{indice_part}.cpf",
            ])
            for campo_entrada in self._campos_entrada_editando:
                if campo_entrada.escopo == "participante":
                    variaveis.append(f"participante.{indice_part}.{campo_entrada.id}")
        variaveis = list(dict.fromkeys(variaveis))
                     
        mapeamento_ui = {}
        mapeamento_atual = copy.deepcopy(formulario_existente.mapeamento) if formulario_existente else {}
        regras_ui = {
            campo: (copy.deepcopy(regra) if isinstance(regra, dict) else {"origem": regra})
            for campo, regra in mapeamento_atual.items()
        }

        def editar_regra(campo_pdf: str):
            regra = copy.deepcopy(regras_ui.get(campo_pdf, {}))
            detalhe = campos.get(campo_pdf, {}) if isinstance(campos, dict) else {}
            estados = detalhe.get("estados", []) or []
            estado_marcado = next((estado for estado in estados if estado != "/Off"), "")
            if detalhe.get("tipo") == "/Btn":
                regra.setdefault("valor_verdadeiro", estado_marcado)
                regra.setdefault("valor_falso", "/Off")
            janela = ctk.CTkToplevel(modal)
            janela.title(f"Regra — {campo_pdf}")
            janela.geometry("680x610")
            janela.transient(modal)
            janela.grab_set()
            painel = ctk.CTkFrame(janela, fg_color=COLOR_SURFACE)
            painel.pack(fill="both", expand=True, padx=SPACING_LARGE, pady=SPACING_LARGE)
            painel.grid_columnconfigure(1, weight=1)

            def linha(rotulo, row, valor="", combo_values=None):
                ctk.CTkLabel(painel, text=rotulo, anchor="w").grid(row=row, column=0, padx=SPACING_SMALL, pady=5, sticky="w")
                if combo_values is not None:
                    controle = ctk.CTkComboBox(painel, values=combo_values)
                    controle.set(valor)
                else:
                    controle = ctk.CTkEntry(painel)
                    if valor:
                        controle.insert(0, valor)
                controle.grid(row=row, column=1, padx=SPACING_SMALL, pady=5, sticky="ew")
                return controle

            origem = linha("Origem:", 0, regra.get("origem", ""), variaveis)
            formato = linha("Formatação:", 1, regra.get("formato", "TEXTO"), ["TEXTO", "CPF", "PIS_PASEP", "DATA_EXTENSO", "MOEDA_SEM_SIMBOLO"])
            constante = linha("Valor constante:", 2, regra.get("constante", ""))
            valor_padrao = linha("Usar se estiver vazio:", 3, regra.get("valor_padrao", ""))
            condicoes_originais = copy.deepcopy(regra.get("condicoes") or [])
            grupo = (condicoes_originais or [{}])[0]
            itens_cond = list(grupo.items())
            c1_origem, c1_valores = itens_cond[0] if itens_cond else ("", [])
            c2_origem, c2_valores = itens_cond[1] if len(itens_cond) > 1 else ("", [])
            cond1 = linha("Condição 1 — campo:", 4, c1_origem, variaveis)
            vals1 = linha("Condição 1 — valores:", 5, ", ".join(c1_valores))
            cond2 = linha("Condição 2 — campo:", 6, c2_origem, variaveis)
            vals2 = linha("Condição 2 — valores:", 7, ", ".join(c2_valores))
            verdadeiro = linha("Valor quando atende:", 8, regra.get("valor_verdadeiro", ""))
            falso = linha("Valor quando não atende:", 9, regra.get("valor_falso", ""))
            ctk.CTkLabel(
                painel,
                text="Para checkboxes, use o estado de exportação do PDF (ex.: /Yes) e /Off.\n"
                     "Sem 'Valor quando atende', o conteúdo da Origem é usado.",
                text_color=COLOR_TEXT_SECONDARY, justify="left",
            ).grid(row=10, column=0, columnspan=2, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="w")

            def aplicar():
                nova = {}
                if origem.get().strip():
                    nova["origem"] = origem.get().strip()
                if formato.get().strip() and formato.get().strip() != "TEXTO":
                    nova["formato"] = formato.get().strip()
                if constante.get().strip():
                    nova["constante"] = constante.get().strip()
                if valor_padrao.get().strip():
                    nova["valor_padrao"] = valor_padrao.get().strip()
                condicao = {}
                for controle_origem, controle_valores in ((cond1, vals1), (cond2, vals2)):
                    chave = controle_origem.get().strip()
                    aceitos = [v.strip() for v in controle_valores.get().split(",") if v.strip()]
                    if chave and aceitos:
                        condicao[chave] = aceitos
                if condicao != grupo:
                    if condicao:
                        nova["condicoes"] = [condicao]
                elif condicoes_originais:
                    # Mantém alternativas adicionais que não cabem neste editor resumido.
                    nova["condicoes"] = condicoes_originais
                if verdadeiro.get().strip():
                    nova["valor_verdadeiro"] = verdadeiro.get().strip()
                if falso.get().strip() or nova.get("condicoes"):
                    nova["valor_falso"] = falso.get().strip()
                regras_ui[campo_pdf] = nova
                mapeamento_ui[campo_pdf].set(nova.get("origem", ""))
                janela.destroy()

            botoes_regra = ctk.CTkFrame(painel, fg_color="transparent")
            botoes_regra.grid(row=11, column=0, columnspan=2, padx=SPACING_SMALL, pady=SPACING_LARGE, sticky="ew")
            botoes_regra.grid_columnconfigure(1, weight=1)

            def remover_regra():
                regras_ui.pop(campo_pdf, None)
                mapeamento_ui[campo_pdf].set("")
                janela.destroy()

            ctk.CTkButton(
                botoes_regra, text="Remover mapeamento", fg_color=COLOR_SURFACE_VARIANT,
                text_color=COLOR_TEXT, command=remover_regra,
            ).grid(row=0, column=0, padx=(0, SPACING_SMALL), sticky="ew")
            ctk.CTkButton(botoes_regra, text="Aplicar regra", command=aplicar).grid(
                row=0, column=1, sticky="ew"
            )
        
        campos_lista = list(campos)

        def carregar_lote(inicio=0):
            if not modal.winfo_exists():
                return
            fim = min(inicio + 8, len(campos_lista))
            for i in range(inicio, fim):
                campo = campos_lista[i]
                detalhe = campos.get(campo, {}) if isinstance(campos, dict) else {}
                estados_txt = ", ".join(detalhe.get("estados", []) or [])
                descricao = f"{campo}\n{detalhe.get('tipo', '')} {estados_txt}".strip()
                ctk.CTkLabel(scroll_map, text=descricao, justify="left").grid(
                    row=i, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_SMALL,
                )
                combo = ctk.CTkComboBox(scroll_map, values=variaveis, width=250)
                combo.grid(row=i, column=1, sticky="ew", padx=SPACING_SMALL, pady=SPACING_SMALL)
                regra_atual = regras_ui.get(campo, {})
                combo.set(regra_atual.get("origem", ""))
                mapeamento_ui[campo] = combo
                ctk.CTkButton(
                    scroll_map, text="Regra…", width=72,
                    command=lambda nome_campo=campo: editar_regra(nome_campo),
                ).grid(row=i, column=2, padx=SPACING_SMALL, pady=SPACING_SMALL)
            if fim < len(campos_lista):
                carregamentos_pendentes.add(modal.after(1, lambda: carregar_lote(fim)))
            else:
                try:
                    btn_salvar.configure(state="normal", text="Salvar Formulário")
                except Exception:
                    pass

        configurar_autoscroll(scroll_map)
        carregamentos_pendentes.add(modal.after(0, carregar_lote))
            
        def salvar():
            novo_mapeamento = {}
            for campo, combo in mapeamento_ui.items():
                regra = copy.deepcopy(regras_ui.get(campo, {}))
                origem_selecionada = combo.get().strip()
                if origem_selecionada:
                    regra["origem"] = origem_selecionada
                elif "origem" in regra:
                    regra.pop("origem")
                if regra:
                    novo_mapeamento[campo] = regra
            novo_form = FormularioModelo(
                nome=entry_nome.get(),
                caminho=caminho,
                geracao="por_processo" if combo_geracao.get() == "Um por processo" else "por_participante",
                mapeamento=novo_mapeamento,
                identificador=getattr(formulario_existente, "identificador", "") if formulario_existente else "",
                recurso=getattr(formulario_existente, "recurso", "") if formulario_existente else "",
            )
            
            if formulario_existente and index is not None:
                self._formularios_editando[index] = novo_form
            else:
                self._formularios_editando.append(novo_form)
                
            self._atualizar_lista_formularios_editando()
            _fechar()
            
        btn_salvar = ctk.CTkButton(frame, text="Carregando campos...", state="disabled", command=salvar)
        btn_salvar.grid(row=5, column=0, pady=SPACING_LARGE, padx=SPACING_LARGE, sticky="e")

    def _salvar_edicao(self) -> None:
        nome = self.edit_nome.get().strip()
        if not nome:
            AlertModal(self.winfo_toplevel(), "Nome Obrigatório", "Por favor, informe o nome do perfil.", ["O nome do perfil não pode ficar em branco."])
            return

        max_part = int(self.edit_max_participantes.get() or "4")
        modo_fluxo = "formulario_simples" if self.edit_modo.get() == "Simples" else "contrato"

        perfil = Perfil(
            nome=nome,
            formularios=self._formularios_editando.copy(),
            documentos_extras=self._documentos_extras_editando.copy(),
            campos_entrada=self._campos_entrada_editando.copy(),
            formato_saida=self.edit_formato.get(),
            modo_fluxo=modo_fluxo,
            max_participantes=max_part,
            identificador=getattr(self._perfil_editando, "identificador", "") if self._perfil_editando else "",
            ordem=getattr(self._perfil_editando, "ordem", 100) if self._perfil_editando else 100,
            usar_paginacao=bool(self.edit_usar_paginacao.get()),
            correcoes_aplicadas=list(getattr(self._perfil_editando, "correcoes_aplicadas", [])),
            agrupamento_paginas=dict(getattr(self._perfil_editando, "agrupamento_paginas", {})),
        )

        try:
            if self._perfil_editando and self._perfil_editando.nome:
                # Editando existente
                nome_antigo = self._perfil_editando.nome
                atualizar_perfil(nome_antigo, perfil)
                
                # Se era o ativo e mudou de nome, atualiza no config
                if nome_antigo != nome and config_manager.obter("perfil_ativo") == nome_antigo:
                    config_manager.definir("perfil_ativo", nome)
                selecionados = config_manager.obter("formularios_basicos_selecionados") or []
                if nome_antigo != nome and nome_antigo in selecionados:
                    config_manager.definir(
                        "formularios_basicos_selecionados",
                        [nome if item == nome_antigo else item for item in selecionados],
                    )
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

    def atualizar_cores(self) -> None:
        """Atualiza a tela de perfis ao mudar o tema, recarregando a lista e controles."""
        if hasattr(self, 'btn_novo_perfil'):
            self.btn_novo_perfil.configure(
                text_color=get_color_primary_text(),
                border_color=get_color_primary_text()
            )
        if hasattr(self, 'edit_formato'):
            self.edit_formato.configure(
                selected_color=get_color_primary(),
                selected_hover_color=get_color_primary_hover()
            )
        if hasattr(self, 'edit_max_participantes'):
            self.edit_max_participantes.configure(
                selected_color=get_color_primary(),
                selected_hover_color=get_color_primary_hover()
            )
        if hasattr(self, 'btn_salvar_perfil'):
            self.btn_salvar_perfil.configure(
                fg_color=get_color_primary(),
                hover_color=get_color_primary_hover()
            )
        self._fechar_editor()
        self._carregar_lista()
