"""
Widget reutilizável e modular para renderização de campos dinâmicos na Etapa 1.

Suporta os tipos: texto, cpf, data, moeda, selecao e checkbox, com validação
em tempo real, formatação e suporte ao Design System do Contracto.
"""

from typing import Callable, Optional
import customtkinter as ctk

from ui.theme import (
    COLOR_BORDER,
    COLOR_BORDER_ERROR,
    COLOR_SURFACE,
    COLOR_TEXT,
    FONT_SIZE_BODY,
    RADIUS_INPUT,
    SPACING_LARGE,
    SPACING_MEDIUM,
    SPACING_SMALL,
    SPACING_XSMALL,
    get_color_primary,
    get_font,
    get_icon,
)
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.date_formatter import validar_data
from utils.profile_manager import CampoEntrada


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
        super().__init__(master, fg_color="transparent", **kwargs)
        self.campo = campo
        self.on_change = on_change
        self.on_open_datepicker = on_open_datepicker

        self.grid_columnconfigure(1, weight=1)

        self._construir_widget()

    def _construir_widget(self) -> None:
        tipo = self.campo.tipo.lower()
        icone_nome = self.campo.icone or ("calendar" if tipo == "data" else ("document" if tipo == "cpf" else "form"))

        # Label do campo
        obrigatorio_sufixo = " *" if self.campo.obrigatorio else ""
        self.label = ctk.CTkLabel(
            self,
            text=f" {self.campo.rotulo}{obrigatorio_sufixo}",
            image=get_icon(icone_nome, (16, 16)),
            compound="left",
            anchor="w",
            font=get_font(FONT_SIZE_BODY),
            text_color=COLOR_TEXT,
        )
        self.label.grid(row=0, column=0, padx=(SPACING_LARGE, SPACING_MEDIUM), pady=SPACING_SMALL, sticky="w")

        # Container do controle (coluna 1)
        if tipo == "checkbox":
            self.var_check = ctk.BooleanVar(value=(self.campo.valor_padrao.lower() in ("true", "1", "sim", "yes")))
            self.widget_input = ctk.CTkCheckBox(
                self,
                text="",
                variable=self.var_check,
                command=self._ao_alterar_checkbox,
                fg_color=get_color_primary(),
            )
            self.widget_input.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="w")

        elif tipo == "selecao":
            valores = self.campo.opcoes if self.campo.opcoes else ["Padrão"]
            valor_inicial = self.campo.valor_padrao if self.campo.valor_padrao in valores else valores[0]
            self.widget_input = ctk.CTkComboBox(
                self,
                values=valores,
                corner_radius=RADIUS_INPUT,
                border_color=COLOR_BORDER,
                command=self._ao_alterar_combobox,
            )
            self.widget_input.set(valor_inicial)
            self.widget_input.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")

        elif tipo == "data":
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
                corner_radius=RADIUS_INPUT,
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
            # Tipos texto, cpf, moeda
            placeholder = self.campo.placeholder
            if not placeholder:
                if tipo == "cpf":
                    placeholder = "123.456.789-10"
                elif tipo == "moeda":
                    placeholder = "R$ 0,00"
                else:
                    placeholder = f"Digite {self.campo.rotulo.lower()}"

            self.entry = ctk.CTkEntry(
                self,
                placeholder_text=placeholder,
                corner_radius=RADIUS_INPUT,
                border_color=COLOR_BORDER,
            )
            if self.campo.valor_padrao:
                self.entry.insert(0, self.campo.valor_padrao)
            self.entry.grid(row=0, column=1, padx=(0, SPACING_LARGE), pady=SPACING_SMALL, sticky="ew")

            self.entry.bind("<KeyRelease>", self._ao_digitar)
            self.entry.bind("<FocusOut>", self._ao_perder_foco)
            self.widget_input = self.entry

    def _ao_digitar(self, event=None) -> None:
        val = self.obter_valor()
        tipo = self.campo.tipo.lower()

        # Validação visual não intrusiva ao digitar
        if tipo == "cpf":
            # Auto-formatação quando atinge 11 dígitos numéricos
            apenas_nums = "".join(c for c in val if c.isdigit())
            if len(apenas_nums) == 11 and ("." not in val or "-" not in val):
                fmt = formatar_cpf(apenas_nums)
                if fmt != val:
                    self.definir_valor(fmt)
                    val = fmt

        self.validar_campo(mostrar_erro=False)
        if self.on_change:
            self.on_change(val)

    def _ao_perder_foco(self, event=None) -> None:
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
        tipo = self.campo.tipo.lower()
        if tipo == "checkbox":
            return "Sim" if getattr(self, "var_check", None) and self.var_check.get() else "Não"
        elif tipo == "selecao":
            return self.widget_input.get() if hasattr(self, "widget_input") else ""
        elif hasattr(self, "entry"):
            return self.entry.get().strip()
        return ""

    def definir_valor(self, valor: str) -> None:
        tipo = self.campo.tipo.lower()
        if tipo == "checkbox":
            if hasattr(self, "var_check"):
                self.var_check.set(valor.lower() in ("sim", "true", "1", "yes"))
        elif tipo == "selecao":
            if hasattr(self, "widget_input"):
                self.widget_input.set(valor)
        elif hasattr(self, "entry"):
            self.entry.delete(0, "end")
            self.entry.insert(0, valor)

    def validar_campo(self, mostrar_erro: bool = True) -> bool:
        """Valida o valor atual do campo e retorna True se válido."""
        val = self.obter_valor()
        tipo = self.campo.tipo.lower()
        is_valid = True

        if self.campo.obrigatorio and not val and tipo != "checkbox":
            is_valid = False
        elif val:
            if tipo == "cpf":
                is_valid = validar_cpf(val)
            elif tipo == "data":
                is_valid = validar_data(val)

        if hasattr(self, "entry"):
            if is_valid or not mostrar_erro:
                self.entry.configure(border_color=COLOR_BORDER)
            else:
                self.entry.configure(border_color=COLOR_BORDER_ERROR)

        return is_valid

    def validar(self, prefixo: str = "") -> list[str]:
        """Retorna lista de mensagens de erro se o campo for inválido."""
        erros = []
        val = self.obter_valor()
        tipo = self.campo.tipo.lower()
        rotulo_completo = f"{prefixo}: {self.campo.rotulo}" if prefixo else self.campo.rotulo

        if self.campo.obrigatorio and not val and tipo != "checkbox":
            erros.append(f"{rotulo_completo} é obrigatório.")
            if hasattr(self, "entry"):
                self.entry.configure(border_color=COLOR_BORDER_ERROR)
        elif val:
            if tipo == "cpf" and not validar_cpf(val):
                erros.append(f"{rotulo_completo}: O CPF informado é inválido.")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            elif tipo == "data" and not validar_data(val):
                erros.append(f"{rotulo_completo}: Data inválida (use o formato DD/MM/AAAA).")
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER_ERROR)
            else:
                if hasattr(self, "entry"):
                    self.entry.configure(border_color=COLOR_BORDER)

        return erros

    def limpar(self) -> None:
        """Limpa o campo restaurando o valor padrão neutro."""
        tipo = self.campo.tipo.lower()
        if tipo == "checkbox":
            if hasattr(self, "var_check"):
                self.var_check.set(self.campo.valor_padrao.lower() in ("true", "1", "sim"))
        elif tipo == "selecao":
            if hasattr(self, "widget_input") and self.campo.opcoes:
                self.widget_input.set(self.campo.valor_padrao or self.campo.opcoes[0])
        elif hasattr(self, "entry"):
            self.entry.delete(0, "end")
            if self.campo.valor_padrao:
                self.entry.insert(0, self.campo.valor_padrao)
            self.entry.configure(border_color=COLOR_BORDER)
