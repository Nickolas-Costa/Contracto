"""
Tela de gerenciamento de perfis.

Similar ao sistema de perfis do PDFCreator, permite ao usuário
criar perfis pré-configurados com modelos e formato de saída.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

from ui.theme import (
    COLOR_BORDER, COLOR_ERROR, COLOR_PRIMARY, COLOR_SURFACE, COLOR_SURFACE_VARIANT,
    COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_SUCCESS,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE,
    get_font, get_color_primary,
)
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil, FormularioModelo,
    carregar_perfis, salvar_perfis, adicionar_perfil,
    atualizar_perfil, excluir_perfil,
)
from utils import config_manager
from services import pdf_service


class ProfilesFrame(ctk.CTkFrame):
    """Frame da tela de gerenciamento de perfis."""

    def __init__(self, master, on_voltar=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_voltar = on_voltar

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

        ctk.CTkLabel(self.frame_editor, text="Editar Perfil",
                     font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT
                     ).grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE,
                            pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        self.frame_editor.grid_columnconfigure(1, weight=1)

        # Nome
        ctk.CTkLabel(self.frame_editor, text="Nome:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=1, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_nome = ctk.CTkEntry(self.frame_editor, corner_radius=RADIUS_INPUT)
        self.edit_nome.grid(row=1, column=1, padx=(0, SPACING_LARGE),
                            pady=SPACING_SMALL, sticky="ew")

        # Formato
        ctk.CTkLabel(self.frame_editor, text="Formato:", font=get_font(FONT_SIZE_BODY),
                     text_color=COLOR_TEXT).grid(row=2, column=0, padx=(SPACING_LARGE, SPACING_SMALL),
                                                  pady=SPACING_SMALL, sticky="w")
        self.edit_formato = ctk.CTkSegmentedButton(
            self.frame_editor, values=["PDF/A-2b", "PDF"],
            font=get_font(FONT_SIZE_BODY), corner_radius=RADIUS_BUTTON,
        )
        self.edit_formato.grid(row=2, column=1, padx=(0, SPACING_LARGE),
                               pady=SPACING_SMALL, sticky="ew")

        # Formulários Dinâmicos
        header_form = ctk.CTkFrame(self.frame_editor, fg_color="transparent")
        header_form.grid(row=3, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        header_form.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_form, text="Formulários Dinâmicos:", font=get_font(FONT_SIZE_BODY, "bold"),
                     text_color=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header_form, text="Adicionar Formulário PDF", width=160, corner_radius=RADIUS_BUTTON,
                      fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER,
                      command=self._adicionar_formulario).grid(row=0, column=1, sticky="e")

        self.scroll_forms = ctk.CTkScrollableFrame(self.frame_editor, fg_color="transparent", height=150)
        self.scroll_forms.grid(row=4, column=0, columnspan=2, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
        self.scroll_forms.grid_columnconfigure(0, weight=1)

        # Botões do editor
        frame_btns = ctk.CTkFrame(self.frame_editor, fg_color="transparent")
        frame_btns.grid(row=5, column=0, columnspan=2, padx=SPACING_LARGE,
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
        pass

    def _carregar_lista(self) -> None:
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

            icon_text = "★" if perfil.nome == perfil_ativo else "○"
            icon_color = get_color_primary() if perfil.nome == perfil_ativo else COLOR_TEXT_SECONDARY

            ctk.CTkLabel(card, text=icon_text, font=get_font(FONT_SIZE_H2),
                         text_color=icon_color).grid(row=0, column=0, rowspan=2,
                                                      padx=SPACING_LARGE, pady=SPACING_MEDIUM)

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
        self._abrir_editor(Perfil(nome="", formato_saida="PDF/A-2b", formularios=[]))
        self.edit_nome.configure(state="normal")

    def _abrir_editor(self, perfil: Perfil) -> None:
        self._perfil_editando = perfil
        self._formularios_editando = [FormularioModelo(f.nome, f.caminho, f.geracao, f.mapeamento.copy()) for f in perfil.formularios]

        self.edit_nome.configure(state="normal")
        self.edit_nome.delete(0, "end")
        self.edit_nome.insert(0, perfil.nome)
        if perfil.nome == PERFIL_PADRAO_NOME:
            self.edit_nome.configure(state="disabled")

        self.edit_formato.set(perfil.formato_saida)
        
        self._atualizar_lista_formularios_editando()

        self.frame_editor.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")

    def _atualizar_lista_formularios_editando(self):
        for widget in self.scroll_forms.winfo_children():
            widget.destroy()
            
        for i, form in enumerate(self._formularios_editando):
            f_frame = ctk.CTkFrame(self.scroll_forms, fg_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_CARD)
            f_frame.grid(row=i, column=0, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
            f_frame.grid_columnconfigure(0, weight=1)
            
            nome_label = ctk.CTkLabel(f_frame, text=f"{form.nome} ({form.geracao})", font=get_font(FONT_SIZE_BODY, "bold"))
            nome_label.grid(row=0, column=0, sticky="w", padx=SPACING_SMALL, pady=SPACING_SMALL)
            
            ctk.CTkButton(f_frame, text="Editar", width=60, corner_radius=RADIUS_BUTTON,
                          command=lambda f=form, idx=i: self._editar_formulario(f, idx)).grid(row=0, column=1, padx=SPACING_SMALL)
                          
            ctk.CTkButton(f_frame, text="Remover", width=60, corner_radius=RADIUS_BUTTON,
                          fg_color=COLOR_ERROR, hover_color="#8c1b1b",
                          command=lambda idx=i: self._remover_formulario(idx)).grid(row=0, column=2, padx=SPACING_SMALL)

    def _fechar_editor(self) -> None:
        self.frame_editor.grid_forget()
        self._perfil_editando = None
        self._formularios_editando = []

    def _adicionar_formulario(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar Formulário PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if caminho:
            try:
                campos = pdf_service.obter_campos_do_formulario(Path(caminho))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler PDF: {e}")
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
            messagebox.showerror("Erro", f"Erro ao ler PDF: {e}")
            return
            
        self._abrir_modal_mapeamento(form.nome, str(form.caminho), list(campos), form, index)

    def _remover_formulario(self, index: int) -> None:
        if 0 <= index < len(self._formularios_editando):
            del self._formularios_editando[index]
            self._atualizar_lista_formularios_editando()

    def _abrir_modal_mapeamento(self, nome, caminho, campos, formulario_existente=None, index=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Mapeamento de Formulário")
        modal.geometry("600x700")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_rowconfigure(3, weight=1)
        
        # Nome do Formulário
        frame_nome = ctk.CTkFrame(modal, fg_color="transparent")
        frame_nome.grid(row=0, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        frame_nome.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_nome, text="Nome:").grid(row=0, column=0, sticky="w", padx=(0, SPACING_SMALL))
        entry_nome = ctk.CTkEntry(frame_nome)
        entry_nome.grid(row=0, column=1, sticky="ew")
        entry_nome.insert(0, formulario_existente.nome if formulario_existente else nome)
        
        # Tipo de Geração
        frame_geracao = ctk.CTkFrame(modal, fg_color="transparent")
        frame_geracao.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        
        ctk.CTkLabel(frame_geracao, text="Geração:").grid(row=0, column=0, sticky="w", padx=(0, SPACING_SMALL))
        combo_geracao = ctk.CTkComboBox(frame_geracao, values=["por_participante", "unico"])
        combo_geracao.grid(row=0, column=1, sticky="w")
        if formulario_existente:
            combo_geracao.set(formulario_existente.geracao)
        else:
            combo_geracao.set("por_participante")
            
        # Mapeamento
        ctk.CTkLabel(modal, text="Mapeamento de Campos", font=get_font(FONT_SIZE_H3, "bold")).grid(row=2, column=0, pady=SPACING_SMALL, padx=SPACING_LARGE, sticky="w")
        
        scroll_map = ctk.CTkScrollableFrame(modal)
        scroll_map.grid(row=3, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="nsew")
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
            modal.destroy()
            
        btn_salvar = ctk.CTkButton(modal, text="Salvar Formulário", command=salvar)
        btn_salvar.grid(row=4, column=0, pady=SPACING_LARGE, padx=SPACING_LARGE, sticky="e")

    def _salvar_edicao(self) -> None:
        nome = self.edit_nome.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "O nome do perfil é obrigatório.")
            return

        perfil = Perfil(
            nome=nome,
            formularios=self._formularios_editando.copy(),
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
