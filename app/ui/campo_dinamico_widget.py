"""
Widget reutilizável e modular para renderização de campos dinâmicos na Etapa 1.

Suporta os tipos: TEXTO, CPF, CNPJ, DATA, MOEDA, SELECAO e CHECKBOX, com validação
em tempo real, auto-formatação e suporte estrito ao alinhamento do Design System do Contracto.
"""

from typing import Callable, Optional
import customtkinter as ctk

from ui.theme import (
    COLOR_BORDER,
    COLOR_BORDER_ERROR,
    COLOR_SURFACE,
    COLOR_SURFACE_VARIANT,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    FONT_SIZE_BODY,
    RADIUS_BUTTON,
    RADIUS_INPUT,
    SPACING_LARGE,
    SPACING_MEDIUM,
    SPACING_SMALL,
    SPACING_XSMALL,
    adicionar_tooltip,
    get_color_primary,
    get_color_primary_hover,
    get_font,
    get_icon,
    rolar_para_widget_se_necessario,
)
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.cnpj_validator import formatar_cnpj, validar_cnpj, limpar_cnpj
from utils.date_formatter import validar_data
from utils.document_validator import (
    formatar_area_progressiva,
    formatar_cnpj_progressivo,
    formatar_cpf_ou_cnpj_progressivo,
    formatar_cpf_progressivo,
    formatar_data_progressiva,
    formatar_moeda_progressiva,
    formatar_telefone_progressivo,
    validar_cpf_ou_cnpj,
    validar_email,
    validar_telefone,
)
from utils.profile_manager import CampoEntrada
from utils.pis_pasep_validator import formatar_pis_pasep, validar_pis_pasep

LARGURA_PADRAO_ROTULO = 145


class CampoDinamicoWidget(ctk.CTkFrame):
    """Renderiza um campo de formulário modular baseado na especificação CampoEntrada."""

    def __init__(
        self,
        master,
        campo: CampoEntrada,
        on_change: Optional[Callable[[str], None]] = None,
        on_open_datepicker: Optional[Callable[[ctk.CTkEntry], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", corner_radius=0, border_width=0, **kwargs)
        self.campo = campo
        self.on_change = on_change
        self.on_open_datepicker = on_open_datepicker
        self.ativo = True
        self.pagina_visivel = True

        self.grid_columnconfigure(0, minsize=LARGURA_PADRAO_ROTULO)
        self.grid_columnconfigure(1, weight=1)

        self._construir_widget()

    def _construir_widget(self) -> None:
        tipo = self.campo.tipo.upper()
        
        if self.campo.icone:
            icone_nome = self.campo.icone
        elif tipo == "DATA":
            icone_nome = "calendar"
        elif tipo in ("CPF", "CNPJ", "CPF_CNPJ"):
            icone_nome = "document"
        elif tipo == "MOEDA":
            icone_nome = "form"
        else:
            icone_nome = "location" if self.campo.id == "endereco" else "form"

        # Label do campo com largura fixa padronizada
        obrigatorio_sufixo = " *" if self.campo.obrigatorio else ""
        area_rotulo = ctk.CTkFrame(self, fg_color="transparent", width=LARGURA_PADRAO_ROTULO)
        area_rotulo.grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")
        self.label = ctk.CTkLabel(
            area_rotulo,
            text=f" {self.campo.rotulo}{obrigatorio_sufixo}",
            image=get_icon(icone_nome, (16, 16)),
            compound="left",
            width=LARGURA_PADRAO_ROTULO,
            anchor="w",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT,
        )
        self.label.pack(side="left")
        if self.campo.ajuda:
            info = ctk.CTkLabel(
                area_rotulo, text=" ⓘ", width=20,
                font=get_font(14), text_color=COLOR_TEXT_SECONDARY,
                cursor="hand2",
            )
            info.pack(side="left")
            adicionar_tooltip(info, self.campo.ajuda)

        # Container do controle (coluna 1)
        if tipo == "CHECKBOX":
            self.var_check = ctk.BooleanVar(value=(self.campo.valor_padrao.lower() in ("true", "1", "sim", "yes")))
            self.widget_input = ctk.CTkCheckBox(
                self,
                text="",
                variable=self.var_check,
                command=self._ao_alterar_checkbox,
                fg_color=get_color_primary(),
            )
            self.widget_input.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="w")

        elif tipo == "SELECAO":
            opcoes = self.campo.opcoes if self.campo.opcoes else ["Padrão"]
            valores = [self._rotulo_opcao(opcao) for opcao in opcoes]
            self._rotulo_para_opcao = dict(zip(valores, opcoes))
            self._opcao_para_rotulo = dict(zip(opcoes, valores))
            valor_inicial = self._opcao_para_rotulo.get(self.campo.valor_padrao, "")
            self.widget_input = ctk.CTkComboBox(
                self,
                values=valores,
                corner_radius=RADIUS_INPUT,
                border_color=COLOR_BORDER,
                command=self._ao_alterar_combobox,
            )
            self.widget_input.set(valor_inicial)
            self.widget_input.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")

        elif tipo == "TEXTO_LONGO":
            self.textbox = ctk.CTkTextbox(
                self, height=66, corner_radius=RADIUS_INPUT,
                border_width=1, border_color=COLOR_BORDER, wrap="word",
            )
            if self.campo.valor_padrao:
                self.textbox.insert("1.0", self.campo.valor_padrao)
            self.textbox.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
            self.textbox.bind("<KeyRelease>", self._ao_digitar_texto_longo)
            self.textbox.bind("<FocusOut>", self._ao_perder_foco)
            self.widget_input = self.textbox

        elif tipo == "DATA":
            # Frame horizontal com Entry + botão do DatePicker
            frame_data = ctk.CTkFrame(self, fg_color="transparent")
            frame_data.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")
            frame_data.grid_columnconfigure(0, weight=1)

            placeholder = self.campo.placeholder or "DD/MM/AAAA"
            self.entry = ctk.CTkEntry(
                frame_data,
                placeholder_text=placeholder,
                corner_radius=RADIUS_INPUT,
                border_color=COLOR_BORDER,
            )
            if self.campo.valor_padrao:
                self.entry.insert(0, self.campo.valor_padrao)
            self.entry.grid(row=0, column=0, sticky="ew", padx=(0, SPACING_XSMALL))

            self.entry.bind("<KeyRelease>", self._ao_digitar)
            self.entry.bind("<FocusOut>", self._ao_perder_foco)

            btn_calendar = ctk.CTkButton(
                frame_data,
                text="",
                image=get_icon("calendar", (16, 16)),
                width=36,
                height=32,
                corner_radius=RADIUS_BUTTON,
                fg_color=COLOR_SURFACE,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                border_width=1,
                border_color=COLOR_BORDER,
                command=self._abrir_datepicker,
            )
            btn_calendar.grid(row=0, column=1, sticky="e")
            self.widget_input = self.entry

        else:
            # Tipos TEXTO, CPF, CNPJ, CPF_CNPJ, MOEDA
            placeholder = self.campo.placeholder
            if not placeholder:
                if tipo == "CPF":
                    placeholder = "123.456.789-10"
                elif tipo == "CNPJ":
                    placeholder = "12.345.678/0001-90"
                elif tipo == "CPF_CNPJ":
                    placeholder = "CPF ou CNPJ (ex: 000.000.000-00)"
                elif tipo == "MOEDA":
                    placeholder = "0,00"
                elif tipo == "PIS_PASEP":
                    placeholder = "000.00000.00-0"
                elif tipo == "ANO":
                    placeholder = "AAAA"
                elif tipo == "AREA" or ("area" in self.campo.id.lower() or "área" in self.campo.rotulo.lower()):
                    placeholder = "Ex: 200,00"
                elif tipo == "TELEFONE" or ("telefone" in self.campo.id.lower()):
                    placeholder = "Ex: (88) 99999-9999"
                elif tipo == "EMAIL" or ("email" in self.campo.id.lower()):
                    placeholder = "Ex: comprador@email.com"
                elif self.campo.id == "endereco" or "endereço" in self.campo.rotulo.lower():
                    placeholder = "Ex: Rua das Flores, 123 - Centro, Camocim - CE"
                else:
                    placeholder = f"Digite {self.campo.rotulo.lower()}"

            self.entry = ctk.CTkEntry(
                self,
                placeholder_text=placeholder,
                corner_radius=RADIUS_INPUT,
                border_color=COLOR_BORDER,
            )
            if self.campo.valor_padrao and self.campo.valor_padrao.strip():
                self.entry.insert(0, self.campo.valor_padrao)
            self.entry.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")

            self.entry.bind("<KeyRelease>", self._ao_digitar)
            self.entry.bind("<FocusIn>", self._ao_receber_foco)
            self.entry.bind("<FocusOut>", self._ao_perder_foco)
            self.widget_input = self.entry

    @staticmethod
    def _rotulo_opcao(valor: str) -> str:
        """Transforma valores internos em textos mais fáceis de ler."""
        if "_" not in valor:
            return valor
        ajustes = {
            "NAO": "Não", "OU": "ou", "DE": "de", "DO": "do", "DA": "da",
            "E": "e", "A": "a", "COM": "com", "EM": "em",
            "DECLARACAO": "Declaração", "AQUISICAO": "Aquisição",
            "CONSTRUCAO": "Construção", "IMOVEL": "Imóvel",
            "AMPLIACAO": "Ampliação", "OPERACOES": "Operações",
            "CONJUGE": "Cônjuge", "PRO": "Pró", "COTISTA": "Cotista",
        }
        siglas = {"FGTS", "CCFGTS", "PMCMV", "SBPE", "AMC"}
        partes = [token if token in siglas else ajustes.get(token, token.lower()) for token in valor.split("_")]
        texto = " ".join(partes)
        return texto[:1].upper() + texto[1:]

    def _encontrar_scrollable_parent(self) -> Optional[ctk.CTkScrollableFrame]:
        """Procura o CTkScrollableFrame ancestral mais próximo."""
        p = self.master
        while p:
            if isinstance(p, ctk.CTkScrollableFrame):
                return p
            p = getattr(p, "master", None)
        return None

    def _ao_receber_foco(self, event=None) -> None:
        if hasattr(self, "entry"):
            self.entry.configure(border_color=get_color_primary(), border_width=2)
            scroll = self._encontrar_scrollable_parent()
            if scroll:
                self.after(50, lambda: rolar_para_widget_se_necessario(self.entry, scroll))

    def _ao_digitar(self, event=None) -> None:
        if not hasattr(self, "entry"):
            return

        # Ignorar teclas de controle como Tab, setas, Shift, etc.
        if event and event.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down", "Return"):
            return

        val = self.entry.get()
        tipo = self.campo.tipo.upper()

        # Auto-formatação progressiva em tempo real
        if event and event.keysym != "BackSpace":
            if tipo == "CPF":
                novo_val = formatar_cpf_progressivo(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "CNPJ":
                novo_val = formatar_cnpj_progressivo(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "CPF_CNPJ":
                novo_val = formatar_cpf_ou_cnpj_progressivo(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "DATA":
                novo_val = formatar_data_progressiva(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "MOEDA":
                novo_val = formatar_moeda_progressiva(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "PIS_PASEP":
                novo_val = formatar_pis_pasep(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo in ("INTEIRO", "ANO"):
                limite = 4 if tipo == "ANO" else None
                novo_val = "".join(ch for ch in val if ch.isdigit())
                if limite:
                    novo_val = novo_val[:limite]
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "AREA" or ("area" in self.campo.id.lower() or "área" in self.campo.rotulo.lower()):
                novo_val = formatar_area_progressiva(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val
            elif tipo == "TELEFONE" or ("telefone" in self.campo.id.lower()):
                novo_val = formatar_telefone_progressivo(val)
                if novo_val != val:
                    self.entry.delete(0, "end")
                    self.entry.insert(0, novo_val)
                    val = novo_val

        self.validar_campo(mostrar_erro=False)
        if self.on_change:
            self.on_change(val)

    def _ao_digitar_texto_longo(self, event=None) -> None:
        valor = self.obter_valor()
        self.validar_campo(mostrar_erro=False)
        if self.on_change:
            self.on_change(valor)

    def _ao_perder_foco(self, event=None) -> None:
        if hasattr(self, "entry"):
            self.entry.configure(border_width=1)
        elif hasattr(self, "textbox"):
            self.textbox.configure(border_width=1)
        self.validar_campo(mostrar_erro=True)

    def _ao_alterar_combobox(self, escolha: str) -> None:
        if self.on_change:
            self.on_change(escolha)

    def _ao_alterar_checkbox(self) -> None:
        val = "Sim" if self.var_check.get() else "Não"
        if self.on_change:
            self.on_change(val)

    def _abrir_datepicker(self) -> None:
        if self.on_open_datepicker and hasattr(self, "entry"):
            self.on_open_datepicker(self.entry)

    def obter_valor(self) -> str:
        tipo = self.campo.tipo.upper()
        if tipo == "CHECKBOX":
            return "Sim" if getattr(self, "var_check", None) and self.var_check.get() else "Não"
        elif tipo == "SELECAO":
            exibido = self.widget_input.get() if hasattr(self, "widget_input") else ""
            return getattr(self, "_rotulo_para_opcao", {}).get(exibido, exibido)
        elif hasattr(self, "textbox"):
            return self.textbox.get("1.0", "end-1c").strip()
        elif hasattr(self, "entry"):
            return self.entry.get().strip()
        return ""

    def definir_valor(self, valor: str) -> None:
        tipo = self.campo.tipo.upper()
        if tipo == "CHECKBOX":
            if hasattr(self, "var_check"):
                self.var_check.set(valor.lower() in ("sim", "true", "1", "yes"))
        elif tipo == "SELECAO":
            if hasattr(self, "widget_input"):
                self.widget_input.set(getattr(self, "_opcao_para_rotulo", {}).get(valor, valor))
        elif hasattr(self, "textbox"):
            self.textbox.delete("1.0", "end")
            if valor is not None and str(valor).strip():
                self.textbox.insert("1.0", str(valor).strip())
        elif hasattr(self, "entry"):
            val_str = str(valor).strip() if valor is not None else ""
            self.entry.delete(0, "end")
            if val_str:
                self.entry.insert(0, val_str)

    def validar_campo(self, mostrar_erro: bool = True) -> bool:
        """Valida o valor atual do campo e retorna True se válido."""
        val = self.obter_valor()
        tipo = self.campo.tipo.upper()
        is_valid = True

        if not self.ativo:
            return True
        if self.campo.obrigatorio and not val and tipo != "CHECKBOX":
            is_valid = False
        elif val:
            if tipo == "CPF":
                is_valid = validar_cpf(val)
            elif tipo == "CNPJ":
                is_valid = validar_cnpj(val)
            elif tipo == "CPF_CNPJ":
                is_valid, _ = validar_cpf_ou_cnpj(val)
            elif tipo == "DATA":
                is_valid = validar_data(val)
            elif tipo == "PIS_PASEP":
                is_valid = validar_pis_pasep(val)
            elif tipo == "ANO":
                is_valid = len(val) == 4 and val.isdigit()
            elif tipo == "INTEIRO":
                is_valid = val.isdigit()
                if is_valid and self.campo.minimo is not None:
                    is_valid = int(val) >= self.campo.minimo
                if is_valid and self.campo.maximo is not None:
                    is_valid = int(val) <= self.campo.maximo
            elif tipo == "TELEFONE" or ("telefone" in self.campo.id.lower()):
                is_valid = validar_telefone(val)
            elif tipo == "EMAIL" or ("email" in self.campo.id.lower()):
                is_valid = validar_email(val)

        if hasattr(self, "entry"):
            if is_valid or not mostrar_erro:
                self.entry.configure(border_color=COLOR_BORDER)
            else:
                self.entry.configure(border_color=COLOR_BORDER_ERROR)
        elif hasattr(self, "textbox"):
            self.textbox.configure(border_color=COLOR_BORDER if is_valid or not mostrar_erro else COLOR_BORDER_ERROR)

        return is_valid

    def validar(self, prefixo: str = "") -> list[str]:
        """Retorna lista de mensagens de erro se o campo for inválido."""
        erros = []
        if not self.ativo:
            return erros
        val = self.obter_valor()
        tipo = self.campo.tipo.upper()
        rotulo_completo = f"{prefixo}: {self.campo.rotulo}" if prefixo else self.campo.rotulo

        if self.campo.obrigatorio and not val and tipo != "CHECKBOX":
            erros.append(f"{rotulo_completo} é obrigatório.")
            if hasattr(self, "entry"):
                self.entry.configure(border_color=COLOR_BORDER_ERROR)
        elif val:
            if tipo == "CPF" and not validar_cpf(val):
                erros.append(f"{rotulo_completo}: O CPF informado é inválido.")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif tipo == "CNPJ" and not validar_cnpj(val):
                erros.append(f"{rotulo_completo}: O CNPJ informado é inválido.")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif tipo == "CPF_CNPJ":
                valido, msg = validar_cpf_ou_cnpj(val)
                if not valido:
                    erros.append(f"{rotulo_completo}: {msg}")
                    if hasattr(self, "entry"):
                        self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif tipo == "DATA" and not validar_data(val):
                erros.append(f"{rotulo_completo}: Data inválida (use o formato DD/MM/AAAA).")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif tipo == "PIS_PASEP" and not validar_pis_pasep(val):
                erros.append(f"{rotulo_completo}: PIS/PASEP inválido.")
            elif tipo == "ANO" and (len(val) != 4 or not val.isdigit()):
                erros.append(f"{rotulo_completo}: informe quatro dígitos.")
            elif tipo == "INTEIRO" and not self.validar_campo(mostrar_erro=True):
                faixa = ""
                if self.campo.minimo is not None or self.campo.maximo is not None:
                    faixa = f" ({self.campo.minimo if self.campo.minimo is not None else 0} a {self.campo.maximo if self.campo.maximo is not None else '∞'})"
                erros.append(f"{rotulo_completo}: informe um número inteiro válido{faixa}.")
            elif (tipo == "TELEFONE" or "telefone" in self.campo.id.lower()) and not validar_telefone(val):
                erros.append(f"{rotulo_completo}: Telefone inválido (use o formato (00) 00000-0000).")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif (tipo == "EMAIL" or "email" in self.campo.id.lower()) and not validar_email(val):
                erros.append(f"{rotulo_completo}: E-mail inválido (exemplo: usuario@email.com).")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            else:
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER)

        cor = COLOR_BORDER_ERROR if erros else COLOR_BORDER
        if hasattr(self, "entry"):
            self.entry.configure(border_color=cor)
        elif hasattr(self, "textbox"):
            self.textbox.configure(border_color=cor)
        return erros

    def limpar(self) -> None:
        """Limpa o campo restaurando o valor padrão neutro."""
        tipo = self.campo.tipo.upper()
        if tipo == "CHECKBOX":
            if hasattr(self, "var_check"):
                self.var_check.set(self.campo.valor_padrao.lower() in ("true", "1", "sim"))
        elif tipo == "SELECAO":
            if hasattr(self, "widget_input") and self.campo.opcoes:
                self.widget_input.set(self.campo.valor_padrao or "")
        elif hasattr(self, "textbox"):
            self.textbox.delete("1.0", "end")
            if self.campo.valor_padrao:
                self.textbox.insert("1.0", self.campo.valor_padrao)
        elif hasattr(self, "entry"):
            self.entry.delete(0, "end")
            if self.campo.valor_padrao and self.campo.valor_padrao.strip():
                self.entry.insert(0, self.campo.valor_padrao)
            self.entry.configure(border_color=COLOR_BORDER)

    def definir_ativo(self, ativo: bool, limpar: bool = False) -> None:
        """Mostra/oculta o campo e o exclui da validação quando não aplicável."""
        self.ativo = ativo
        if ativo and self.pagina_visivel:
            self.grid()
        else:
            if limpar:
                self.definir_valor("")
            self.grid_remove()

    def definir_pagina_visivel(self, visivel: bool) -> None:
        """Troca a página sem limpar o valor e sem alterar a validação."""
        self.pagina_visivel = visivel
        if visivel and self.ativo:
            self.grid()
        else:
            self.grid_remove()

    def atualizar_cores(self) -> None:
        """Atualiza cores dinâmicas dos controles internos."""
        tipo = self.campo.tipo.upper()
        if tipo == "CHECKBOX" and hasattr(self, "widget_input"):
            self.widget_input.configure(
                fg_color=get_color_primary(),
                hover_color=get_color_primary_hover()
            )
