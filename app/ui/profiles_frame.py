"""
Tela de gerenciamento de perfis.

Similar ao sistema de perfis do PDFCreator, permite ao usuário
criar perfis pré-configurados com modelos e formato de saída.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.theme import (
    COLOR_BORDER, COLOR_ERROR, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE,
    get_font, get_color_primary,
)
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil,
    carregar_perfis, salvar_perfis, adicionar_perfil,
    atualizar_perfil, excluir_perfil,
)
from utils import config_manager


class ProfilesFrame(ctk.CTkFrame):
    """Frame da tela de gerenciamento de perfis."""

    def __init__(self, master, on_voltar=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_voltar = on_voltar

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._perfil_editando: Perfil | None = None

        self._construir_header()
        self._construir_lista_perfis()
        self._construir_editor()
        self._construir_botoes()
        self._carregar_lista()

    def _construir_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Perfis",
            font=get_font(FONT_SIZE_H2, "bold"),
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Configure modelos e formato de saída para diferentes cenários.",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", pady=(SPACING_SMALL, 0))

        ctk.CTkButton(
            header, text="+ Novo Perfil", width=120,
            fg_color=COLOR_SURFACE, text_color=get_color_primary(),
            border_width=1, border_color=get_color_primary(),
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
        self.frame_editor = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                                          border_width=1, border_color=COLOR_BORDER)
        # Não mostra inicialmente

        ctk.CTkLabel(self.frame_editor, text="Editar Perfil",
                     font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT
                     ).grid(row=0, column=0, columnspan=3, padx=SPACING_LARGE,
                            pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        self.frame_editor.grid_columnconfigure(1, weight=1)

        # Nome
        ctk.CTkLabel(self.frame_editor, text="Nome:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=1, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_nome = ctk.CTkEntry(self.frame_editor, corner_radius=RADIUS_INPUT)
        self.edit_nome.grid(row=1, column=1, columnspan=2, padx=(0, SPACING_LARGE),
                            pady=SPACING_SMALL, sticky="ew")

        # Modelo PPE
        ctk.CTkLabel(self.frame_editor, text="Modelo PPE:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=2, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_ppe = ctk.CTkEntry(self.frame_editor, corner_radius=RADIUS_INPUT,
                                      placeholder_text="(Embutido padrão)")
        self.edit_ppe.grid(row=2, column=1, padx=(0, SPACING_SMALL), pady=SPACING_SMALL, sticky="ew")
        ctk.CTkButton(self.frame_editor, text="...", width=36, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._selecionar_ppe).grid(row=2, column=2, padx=(0, SPACING_LARGE),
                                                          pady=SPACING_SMALL)

        # Modelo Primeiro Imóvel
        ctk.CTkLabel(self.frame_editor, text="Modelo Imóvel:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=3, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_imovel = ctk.CTkEntry(self.frame_editor, corner_radius=RADIUS_INPUT,
                                         placeholder_text="(Embutido padrão)")
        self.edit_imovel.grid(row=3, column=1, padx=(0, SPACING_SMALL), pady=SPACING_SMALL, sticky="ew")
        ctk.CTkButton(self.frame_editor, text="...", width=36, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._selecionar_imovel).grid(row=3, column=2, padx=(0, SPACING_LARGE),
                                                             pady=SPACING_SMALL)

        # Formato
        ctk.CTkLabel(self.frame_editor, text="Formato:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=4, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_formato = ctk.CTkSegmentedButton(
            self.frame_editor, values=["PDF/A-2b", "PDF"],
            font=get_font(FONT_SIZE_BODY), corner_radius=RADIUS_BUTTON,
        )
        self.edit_formato.grid(row=4, column=1, columnspan=2, padx=(0, SPACING_LARGE),
                               pady=SPACING_SMALL, sticky="ew")

        # Botões do editor
        frame_btns = ctk.CTkFrame(self.frame_editor, fg_color="transparent")
        frame_btns.grid(row=5, column=0, columnspan=3, padx=SPACING_LARGE,
                        pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        frame_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(frame_btns, text="Cancelar", fg_color=COLOR_SURFACE, text_color=COLOR_TEXT,
                      border_width=1, border_color=COLOR_BORDER, hover_color=COLOR_SURFACE_VARIANT,
                      corner_radius=RADIUS_BUTTON, command=self._fechar_editor
                      ).grid(row=0, column=0, padx=(0, SPACING_SMALL))

        ctk.CTkButton(frame_btns, text="Salvar Perfil", fg_color=get_color_primary(),
                      hover_color="#004785", corner_radius=RADIUS_BUTTON,
                      command=self._salvar_edicao
                      ).grid(row=0, column=1, sticky="ew")

    def _construir_botoes(self) -> None:
        pass  # Navegação fica na toolbar da janela principal

    def _carregar_lista(self) -> None:
        """Reconstrói a lista de perfis."""
        for widget in self.scroll_perfis.winfo_children():
            widget.destroy()

        perfis = carregar_perfis()
        perfil_ativo = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME

        for i, perfil in enumerate(perfis):
            card = ctk.CTkFrame(self.scroll_perfis, fg_color=COLOR_SURFACE,
                                corner_radius=RADIUS_CARD, border_width=1,
                                border_color=get_color_primary() if perfil.nome == perfil_ativo else COLOR_BORDER)
            card.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            # Ícone de perfil
            icon_text = "★" if perfil.nome == perfil_ativo else "○"
            icon_color = get_color_primary() if perfil.nome == perfil_ativo else COLOR_TEXT_DISABLED
            ctk.CTkLabel(card, text=icon_text, font=get_font(FONT_SIZE_H2),
                         text_color=icon_color).grid(row=0, column=0, rowspan=2,
                                                      padx=SPACING_LARGE, pady=SPACING_MEDIUM)

            # Nome e detalhes
            ctk.CTkLabel(card, text=perfil.nome, font=get_font(FONT_SIZE_H3, "bold"),
                         text_color=COLOR_TEXT).grid(row=0, column=1, sticky="w", pady=(SPACING_MEDIUM, 0))

            detalhes = f"Formato: {perfil.formato_saida}"
            if perfil.usa_modelos_embutidos():
                detalhes += "  •  Modelos embutidos"
            else:
                detalhes += "  •  Modelos personalizados"

            ctk.CTkLabel(card, text=detalhes, font=get_font(FONT_SIZE_CAPTION),
                         text_color=COLOR_TEXT_SECONDARY).grid(row=1, column=1, sticky="w",
                                                                 pady=(0, SPACING_MEDIUM))

            # Botões de ação
            frame_acoes = ctk.CTkFrame(card, fg_color="transparent")
            frame_acoes.grid(row=0, column=2, rowspan=2, padx=SPACING_LARGE, pady=SPACING_MEDIUM)

            if perfil.nome != perfil_ativo:
                ctk.CTkButton(frame_acoes, text="Ativar", width=60,
                              fg_color=get_color_primary(), hover_color="#004785",
                              corner_radius=RADIUS_BUTTON, font=get_font(FONT_SIZE_CAPTION),
                              command=lambda n=perfil.nome: self._ativar_perfil(n)
                              ).pack(side="left", padx=2)

            ctk.CTkButton(frame_acoes, text="Editar", width=60,
                          fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT,
                          hover_color=COLOR_BORDER, corner_radius=RADIUS_BUTTON,
                          font=get_font(FONT_SIZE_CAPTION),
                          command=lambda p=perfil: self._abrir_editor(p)
                          ).pack(side="left", padx=2)

            if perfil.nome != PERFIL_PADRAO_NOME:
                ctk.CTkButton(frame_acoes, text="✕", width=30,
                              fg_color="transparent", text_color=COLOR_ERROR,
                              hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
                              command=lambda n=perfil.nome: self._excluir(n)
                              ).pack(side="left", padx=2)

    def _ativar_perfil(self, nome: str) -> None:
        config_manager.definir("perfil_ativo", nome)
        self._carregar_lista()

    def _criar_novo(self) -> None:
        self._perfil_editando = None
        self._abrir_editor(Perfil(nome="", formato_saida="PDF/A-2b"))
        self.edit_nome.configure(state="normal")

    def _abrir_editor(self, perfil: Perfil) -> None:
        self._perfil_editando = perfil

        self.edit_nome.configure(state="normal")
        self.edit_nome.delete(0, "end")
        self.edit_nome.insert(0, perfil.nome)
        if perfil.nome == PERFIL_PADRAO_NOME:
            self.edit_nome.configure(state="disabled")

        self.edit_ppe.delete(0, "end")
        if perfil.caminho_modelo_ppe:
            self.edit_ppe.insert(0, perfil.caminho_modelo_ppe)

        self.edit_imovel.delete(0, "end")
        if perfil.caminho_modelo_imovel:
            self.edit_imovel.insert(0, perfil.caminho_modelo_imovel)

        self.edit_formato.set(perfil.formato_saida)

        self.frame_editor.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

    def _fechar_editor(self) -> None:
        self.frame_editor.grid_forget()
        self._perfil_editando = None

    def _selecionar_ppe(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar modelo PPE",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.edit_ppe.delete(0, "end")
            self.edit_ppe.insert(0, caminho)

    def _selecionar_imovel(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar modelo Primeiro Imóvel",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            self.edit_imovel.delete(0, "end")
            self.edit_imovel.insert(0, caminho)

    def _salvar_edicao(self) -> None:
        nome = self.edit_nome.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "O nome do perfil é obrigatório.")
            return

        perfil = Perfil(
            nome=nome,
            caminho_modelo_ppe=self.edit_ppe.get().strip(),
            caminho_modelo_imovel=self.edit_imovel.get().strip(),
            formato_saida=self.edit_formato.get(),
        )

        try:
            if self._perfil_editando and self._perfil_editando.nome:
                # Editando existente
                atualizar_perfil(perfil)
            else:
                # Criando novo
                adicionar_perfil(perfil)
        except ValueError as e:
            messagebox.showwarning("Aviso", str(e))
            return

        self._fechar_editor()
        self._carregar_lista()

    def _excluir(self, nome: str) -> None:
        if messagebox.askyesno("Confirmar", f"Deseja excluir o perfil '{nome}'?"):
            try:
                excluir_perfil(nome)
                # Se era o ativo, voltar ao padrão
                if config_manager.obter("perfil_ativo") == nome:
                    config_manager.definir("perfil_ativo", PERFIL_PADRAO_NOME)
                self._carregar_lista()
            except ValueError as e:
                messagebox.showwarning("Aviso", str(e))
