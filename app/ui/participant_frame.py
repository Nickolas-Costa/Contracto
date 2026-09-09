"""
Frame reutilizável que representa os campos de um único participante na interface,
com suporte a campos dinâmicos e modulares configurados por perfil.
"""

from typing import Callable, Optional
import customtkinter as ctk

from models.participant import Participant
from ui.campo_dinamico_widget import CampoDinamicoWidget
from ui.theme import *
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.document_validator import formatar_cpf_progressivo
from utils.profile_manager import CampoEntrada


class ParticipantFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        indice: int,
        principal: bool = False,
        on_remover: Optional[Callable[["ParticipantFrame"], None]] = None,
        campos_customizados: Optional[list[CampoEntrada]] = None,
        on_open_datepicker: Optional[Callable[[ctk.CTkEntry], None]] = None,
        on_change: Optional[Callable[[], None]] = None,
        local_padrao: str = "CAMOCIM-CE",
        agrupamento_paginas: Optional[dict[str, str]] = None,
        **kwargs,
    ):
        kwargs.pop("local_padrao", None)
        super().__init__(
            master, 
            corner_radius=RADIUS_CARD, 
            fg_color=COLOR_SURFACE, 
            border_width=1, 
            border_color=COLOR_BORDER,
            **kwargs
        )

        self.indice = indice
        self.principal = principal
        self.on_remover = on_remover
        self.campos_customizados = campos_customizados or []
        self.on_open_datepicker = on_open_datepicker
        self.on_change = on_change
        self._local_padrao = local_padrao
        self.agrupamento_paginas = dict(agrupamento_paginas or {})
        self.widgets_dinamicos: dict[str, CampoDinamicoWidget] = {}
        self._paginas_widgets: dict[str, list[CampoDinamicoWidget]] = {}
        self._paginas_secoes: dict[str, list[ctk.CTkFrame]] = {}
        self._controles_campos_padrao: list[ctk.CTkBaseClass] = []

        self.grid_columnconfigure(0, minsize=145)
        self.grid_columnconfigure(1, weight=1)

        self.label_titulo = ctk.CTkLabel(
            self,
            text=f" {self._titulo(indice)}",
            image=get_icon("person", (18, 18)),
            compound="left",
            font=get_font(FONT_SIZE_H3, "bold"),
            text_color=get_color_primary_text(),
        )
        self.label_titulo.grid(row=0, column=0, columnspan=2, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        if on_remover is not None:
            botao_remover = ctk.CTkButton(
                self,
                text="",
                image=get_icon("trash", (16, 16)),
                width=36,
                height=28,
                fg_color=COLOR_BORDER,
                text_color=COLOR_TEXT,
                hover_color=COLOR_TEXT_DISABLED,
                corner_radius=RADIUS_BUTTON,
                command=lambda: self.on_remover(self),
            )
            botao_remover.grid(row=0, column=2, padx=SPACING_MEDIUM, pady=(SPACING_SMALL, 0), sticky="e")

        linha = 1
        self.entry_nome = self._criar_campo_padrao("Nome Completo", linha, tipo="nome")
        linha += 1
        self.entry_cpf = self._criar_campo_padrao("CPF", linha, tipo="cpf")
        linha += 1

        self.entry_endereco: ctk.CTkEntry | None = None
        self._frames_subtitulos_part = []
        self._labels_subtitulos_part = []
        secao_anterior = None

        # Renderização modular de campos do participante
        if self.campos_customizados:
            for campo in self.campos_customizados:
                if campo.id in ("nome_completo", "nome", "cpf"):
                    continue
                if campo.ate_participante and self.indice > campo.ate_participante:
                    continue
                # Em perfis normais, se for endereço e não for o principal, só exibe se o perfil exigir por participante
                if campo.id == "endereco" and not principal and campo.escopo != "participante":
                    continue

                nome_secao = campo.aba.strip() if campo.aba else ""
                if nome_secao and nome_secao != "Geral" and nome_secao != secao_anterior:
                    frame_sub = self._criar_subtitulo_secao(nome_secao)
                    frame_sub.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=(SPACING_SMALL, 0))
                    self._frames_subtitulos_part.append(frame_sub)
                    pagina = self.agrupamento_paginas.get(nome_secao, nome_secao)
                    self._paginas_secoes.setdefault(pagina, []).append(frame_sub)
                    linha += 1
                    secao_anterior = nome_secao

                widget_campo = CampoDinamicoWidget(
                    self,
                    campo=campo,
                    on_change=lambda valor, campo_id=campo.id: self._ao_alterar_campo_dinamico(campo_id, valor),
                    on_open_datepicker=self.on_open_datepicker,
                )
                widget_campo.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=0)
                self.widgets_dinamicos[campo.id] = widget_campo
                pagina = self.agrupamento_paginas.get(campo.aba or "Geral", campo.aba or "Geral")
                self._paginas_widgets.setdefault(pagina, []).append(widget_campo)
                if campo.id == "endereco" and hasattr(widget_campo, "entry"):
                    self.entry_endereco = widget_campo.entry
                linha += 1

        self._atualizar_campos_condicionais()

        # Pequeno respiro na última linha do frame
        self._label_respiro = ctk.CTkLabel(self, text="", height=2)
        self._label_respiro.grid(row=linha, column=0, pady=(0, SPACING_SMALL))

    def _criar_subtitulo_secao(self, titulo: str) -> ctk.CTkFrame:
        """Cria um cabeçalho/subtítulo elegante dentro do quadro do participante."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        icone = icone_para_secao(titulo)

        header_box = ctk.CTkFrame(frame, fg_color="transparent")
        header_box.grid(row=0, column=0, sticky="ew", padx=SPACING_LARGE, pady=(SPACING_SMALL, 2))

        lbl = ctk.CTkLabel(
            header_box,
            text=f" {titulo}",
            image=get_icon(icone, (15, 15)),
            compound="left",
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=get_color_primary_text(),
        )
        lbl.pack(side="left")
        self._labels_subtitulos_part.append(lbl)

        linha = ctk.CTkFrame(frame, height=1, fg_color=COLOR_BORDER)
        linha.grid(row=1, column=0, sticky="ew", padx=SPACING_LARGE, pady=(2, SPACING_XSMALL))

        return frame

    def reconstruir_campos_customizados(
        self,
        novos_campos: Optional[list[CampoEntrada]],
        agrupamento_paginas: Optional[dict[str, str]] = None,
    ) -> None:
        """Reconstrói dinamicamente os campos customizados mantendo os valores já preenchidos."""
        valores_atuais = {cid: widget.obter_valor() for cid, widget in self.widgets_dinamicos.items()}
        if self.entry_endereco is not None:
            valores_atuais["endereco"] = self.entry_endereco.get().strip()

        for widget in self.widgets_dinamicos.values():
            try:
                widget.destroy()
            except Exception:
                pass
        self.widgets_dinamicos.clear()
        self._paginas_widgets.clear()
        self._paginas_secoes.clear()
        self.entry_endereco = None

        if hasattr(self, "_frames_subtitulos_part"):
            for f in self._frames_subtitulos_part:
                try:
                    f.destroy()
                except Exception:
                    pass
        self._frames_subtitulos_part = []
        self._labels_subtitulos_part = []

        if hasattr(self, "_label_respiro") and self._label_respiro:
            try:
                self._label_respiro.destroy()
            except Exception:
                pass

        self.campos_customizados = novos_campos or []
        self.agrupamento_paginas = dict(agrupamento_paginas or {})
        linha = 3  # Linha 0: Título, Linha 1: Nome, Linha 2: CPF
        secao_anterior = None

        if self.campos_customizados:
            for campo in self.campos_customizados:
                if campo.id in ("nome_completo", "nome", "cpf"):
                    continue
                if campo.ate_participante and self.indice > campo.ate_participante:
                    continue
                if campo.id == "endereco" and not self.principal and campo.escopo != "participante":
                    continue

                nome_secao = campo.aba.strip() if campo.aba else ""
                if nome_secao and nome_secao != "Geral" and nome_secao != secao_anterior:
                    frame_sub = self._criar_subtitulo_secao(nome_secao)
                    frame_sub.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=(SPACING_SMALL, 0))
                    self._frames_subtitulos_part.append(frame_sub)
                    pagina = self.agrupamento_paginas.get(nome_secao, nome_secao)
                    self._paginas_secoes.setdefault(pagina, []).append(frame_sub)
                    linha += 1
                    secao_anterior = nome_secao

                widget_campo = CampoDinamicoWidget(
                    self,
                    campo=campo,
                    on_change=lambda valor, campo_id=campo.id: self._ao_alterar_campo_dinamico(campo_id, valor),
                    on_open_datepicker=self.on_open_datepicker,
                )
                widget_campo.grid(row=linha, column=0, columnspan=3, sticky="ew", padx=2, pady=0)
                self.widgets_dinamicos[campo.id] = widget_campo
                pagina = self.agrupamento_paginas.get(campo.aba or "Geral", campo.aba or "Geral")
                self._paginas_widgets.setdefault(pagina, []).append(widget_campo)

                if campo.id in valores_atuais:
                    widget_campo.definir_valor(valores_atuais[campo.id])

                if campo.id == "endereco" and hasattr(widget_campo, "entry"):
                    self.entry_endereco = widget_campo.entry
                linha += 1

        self._atualizar_campos_condicionais()

        self._label_respiro = ctk.CTkLabel(self, text="", height=2)
        self._label_respiro.grid(row=linha, column=0, pady=(0, SPACING_SMALL))

    def _ao_alterar_campo_dinamico(self, campo_id: str, valor: str) -> None:
        """Reavalia campos condicionais e avisa a janela (contador de pendências)."""
        self._atualizar_campos_condicionais()
        if self.on_change:
            self.on_change()

    def aplicar_pagina(self, pagina: str | None, primeira: bool = False) -> bool:
        """Mostra somente os campos da página e oculta o cartão quando ele fica vazio."""
        for nome, widgets in self._paginas_widgets.items():
            mostrar = pagina is None or nome == pagina
            for widget in widgets:
                widget.definir_pagina_visivel(mostrar)
        for nome, secoes in self._paginas_secoes.items():
            for secao in secoes:
                if pagina is None or nome == pagina:
                    secao.grid()
                else:
                    secao.grid_remove()
        for controle in self._controles_campos_padrao:
            if pagina is None or primeira:
                controle.grid()
            else:
                controle.grid_remove()

        possui_conteudo = pagina is None or primeira or any(
            widget.ativo and widget.pagina_visivel
            for widget in self.widgets_dinamicos.values()
        )
        if possui_conteudo:
            self.grid()
        else:
            self.grid_remove()
        return possui_conteudo

    def _atualizar_campos_condicionais(self) -> None:
        """Aplica condições declarativas e limpa valores que deixaram de valer."""
        valores = {campo_id: widget.obter_valor() for campo_id, widget in self.widgets_dinamicos.items()}
        for widget in self.widgets_dinamicos.values():
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

    def _titulo(self, indice: int) -> str:
        return f"Participante {indice}" + ("  (Principal)" if self.principal else "")

    def _criar_campo_padrao(self, rotulo: str, linha: int, tipo: str) -> ctk.CTkEntry:
        icone_nome = "attribution" if tipo == "nome" else ("document" if tipo in ("cpf", "cnpj") else "location")
        placeholder = (
            "Ex: João da Silva" if tipo == "nome"
            else ("123.456.789-10" if tipo == "cpf"
                  else ("12.345.678/0001-90" if tipo == "cnpj"
                        else "Ex: Rua das Flores, 123 - Centro, Camocim - CE"))
        )
        label = ctk.CTkLabel(
            self,
            text=f" {rotulo}",
            image=get_icon(icone_nome, (16, 16)),
            compound="left",
            width=145,
            anchor="w",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT,
        )
        label.grid(
            row=linha, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w"
        )
        entry = ctk.CTkEntry(self, placeholder_text=placeholder, corner_radius=RADIUS_INPUT, border_color=COLOR_BORDER)
        entry.grid(row=linha, column=1, columnspan=2, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
        self._controles_campos_padrao.extend((label, entry))
        
        entry.bind("<KeyRelease>", lambda e: self._ao_digitar_campo_padrao(entry, tipo, e))
        entry.bind("<FocusIn>", lambda e: self._ao_foco_campo_padrao(entry))
        entry.bind("<FocusOut>", lambda e: self._ao_desfoco_campo_padrao(entry, tipo))
            
        return entry

    def _encontrar_scrollable_parent(self) -> Optional[ctk.CTkScrollableFrame]:
        """Procura o CTkScrollableFrame ancestral mais próximo."""
        p = self.master
        while p:
            if isinstance(p, ctk.CTkScrollableFrame):
                return p
            p = getattr(p, "master", None)
        return None

    def _ao_foco_campo_padrao(self, entry: ctk.CTkEntry) -> None:
        entry.configure(border_color=get_color_primary(), border_width=2)
        scroll = self._encontrar_scrollable_parent()
        if scroll:
            self.after(50, lambda: rolar_para_widget_se_necessario(entry, scroll))

    def _ao_desfoco_campo_padrao(self, entry: ctk.CTkEntry, tipo: str) -> None:
        entry.configure(border_width=1)
        self._validar_campo_especifico(entry, tipo)

    def _ao_digitar_campo_padrao(self, entry: ctk.CTkEntry, tipo: str, event=None) -> None:
        if event and event.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down", "Return"):
            return

        val = entry.get()
        if tipo == "cpf" and event and event.keysym != "BackSpace":
            novo_val = formatar_cpf_progressivo(val)
            if novo_val != val:
                entry.delete(0, "end")
                entry.insert(0, novo_val)

        self._validar_campo_especifico(entry, tipo, mostrar_erro=False)
        if self.on_change:
            self.on_change()

    def _validar_campo_especifico(self, entry: ctk.CTkEntry, tipo: str, mostrar_erro: bool = True) -> bool:
        val = entry.get().strip()
        is_valid = True

        if tipo == "nome":
            is_valid = bool(val)
        elif tipo == "cpf":
            is_valid = bool(val) and validar_cpf(val)
        elif tipo == "cnpj":
            from utils.cnpj_validator import validar_cnpj
            is_valid = bool(val) and validar_cnpj(val)
        elif tipo == "endereco":
            is_valid = bool(val)

        if is_valid or not mostrar_erro:
            entry.configure(border_color=COLOR_BORDER)
        else:
            entry.configure(border_color=COLOR_BORDER_ERROR)

        return is_valid

    def validar_campos(self) -> list[str]:
        """Valida todos os campos deste frame e retorna lista de erros."""
        erros = []
        prefixo = f"Participante {self.indice}" + (" (Principal)" if self.principal else "")
        
        nome_val = self.entry_nome.get().strip()
        if not nome_val:
            self.entry_nome.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: Nome Completo é obrigatório.")
        else:
            self.entry_nome.configure(border_color=COLOR_BORDER)

        cpf_val = self.entry_cpf.get().strip()
        if not cpf_val:
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: CPF é obrigatório.")
        elif not validar_cpf(cpf_val):
            self.entry_cpf.configure(border_color=COLOR_BORDER_ERROR)
            erros.append(f"{prefixo}: O CPF informado é inválido.")
        else:
            self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            end_val = self.entry_endereco.get().strip()
            if not end_val:
                self.entry_endereco.configure(border_color=COLOR_BORDER_ERROR)
                erros.append(f"{prefixo}: Endereço é obrigatório.")
            else:
                self.entry_endereco.configure(border_color=COLOR_BORDER)

        # Validação dos campos modulares adicionais
        for campo_id, widget in self.widgets_dinamicos.items():
            erros_widget = widget.validar(prefixo=prefixo)
            erros.extend(erros_widget)

        return erros

    def listar_pendencias(self) -> list[str]:
        """Lista pendências sem trocar a página atual nem acender todos os campos."""
        erros: list[str] = []
        prefixo = f"Participante {self.indice}" + (" (Principal)" if self.principal else "")
        if not self.entry_nome.get().strip():
            erros.append(f"{prefixo}: Nome Completo é obrigatório.")
        cpf = self.entry_cpf.get().strip()
        if not cpf:
            erros.append(f"{prefixo}: CPF é obrigatório.")
        elif not validar_cpf(cpf):
            erros.append(f"{prefixo}: CPF inválido.")
        for widget in self.widgets_dinamicos.values():
            if widget.ativo and not widget.validar_campo(mostrar_erro=False):
                valor = widget.obter_valor()
                if widget.campo.obrigatorio and not valor:
                    erros.append(f"{prefixo}: {widget.campo.rotulo} é obrigatório.")
                else:
                    erros.append(f"{prefixo}: {widget.campo.rotulo} é inválido.")
        return erros

    def limpar_campos(self) -> None:
        """Limpa todos os campos deste quadro."""
        self.entry_nome.delete(0, "end")
        self.entry_nome.configure(border_color=COLOR_BORDER)

        self.entry_cpf.delete(0, "end")
        self.entry_cpf.configure(border_color=COLOR_BORDER)

        if self.entry_endereco is not None:
            self.entry_endereco.delete(0, "end")
            self.entry_endereco.configure(border_color=COLOR_BORDER)

        for widget in self.widgets_dinamicos.values():
            widget.limpar()

    def atualizar_indice(self, indice: int) -> None:
        self.indice = indice
        self.label_titulo.configure(text=self._titulo(indice))

    def atualizar_cores(self) -> None:
        """Atualiza as cores dinâmicas deste frame."""
        self.label_titulo.configure(text_color=get_color_primary_text())
        if hasattr(self, "_labels_subtitulos_part"):
            for lbl in self._labels_subtitulos_part:
                try:
                    lbl.configure(text_color=get_color_primary_text())
                except Exception:
                    pass
        for w in self.widgets_dinamicos.values():
            if hasattr(w, "atualizar_cores"):
                w.atualizar_cores()

    def piscar_destaque(self) -> None:
        """Faz o quadro 'piscar' visualmente ao ser adicionado."""
        try:
            self.configure(
                border_color=get_color_primary(),
                border_width=2,
                fg_color=get_color_primary_light()
            )
            def _restaurar_fg():
                try:
                    self.configure(fg_color=COLOR_SURFACE)
                    self.after(250, _restaurar_border)
                except Exception:
                    pass

            def _restaurar_border():
                try:
                    self.configure(border_color=COLOR_BORDER, border_width=1)
                except Exception:
                    pass

            self.after(200, _restaurar_fg)
        except Exception:
            pass

    def obter_participante(self) -> Participant:
        p = Participant(
            nome_completo=self.entry_nome.get().strip(),
            cpf=self.entry_cpf.get().strip(),
        )
        if self.entry_endereco is not None:
            p.endereco = self.entry_endereco.get().strip()

        for campo_id, widget in self.widgets_dinamicos.items():
            val = widget.obter_valor()
            p.definir_campo(campo_id, val)

        return p
