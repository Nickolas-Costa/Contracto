"""
Modal de carregamento dinâmico e profissional da aplicação Contracto.
Utiliza animações GIF rotativas em alta definição para proporcionar uma experiência fluida,
com suporte a cancelamento de processo e minimização para execução em segundo plano (fila).
"""

from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import *
from ui.animated_loader import CanvasSpinner
from ui.base_modal import BaseModal


class LoadingModal(BaseModal):
    """Modal de carregamento reutilizável com overlay escuro translúcido, indicação de etapas,
    spinner circular vetorial nativo e botões de controle (Parar / Minimizar para fila)."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        message: str = "Carregando...",
        submessage: str = "",
        on_cancel: Optional[Callable[[], None]] = None,
        on_minimize: Optional[Callable[[], None]] = None,
        titulo: Optional[str] = None,
        subtitulo: Optional[str] = None,
        **kwargs,
    ):
        if titulo is not None:
            message = titulo
        if subtitulo is not None:
            submessage = subtitulo

        self.on_cancel = on_cancel
        self.on_minimize = on_minimize
        self._cancel_requested = False
        self._is_dismissed = False

        # Dimensões limpas e compactas
        if on_cancel and on_minimize:
            w, h = 420, 225
        elif on_cancel or on_minimize:
            w, h = 380, 215
        else:
            w, h = 340, 175

        # Comportamento original preservado: sem trava de teclado nem
        # tecla Escape (o trabalho continua em segundo plano).
        super().__init__(
            master, w, h,
            fechar_no_overlay=False, tecla_escape=False, usar_grab=False,
        )

        # Spinner circular vetorial 100% nativo em Canvas
        self.spinner = CanvasSpinner(self.frame, size=38, line_width=3)
        self.spinner.pack(pady=(SPACING_LARGE, SPACING_SMALL))

        self.label = ctk.CTkLabel(
            self.frame,
            text=message,
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=COLOR_TEXT,
        )
        self.label.pack(padx=SPACING_LARGE, pady=(0, 2))

        self.sublabel = ctk.CTkLabel(
            self.frame,
            text=submessage,
            font=get_font(FONT_SIZE_CAPTION),
            text_color=COLOR_TEXT_SECONDARY,
        )
        if submessage:
            self.sublabel.pack(padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
        else:
            self.sublabel.pack_forget()

        # Barra de progresso nativa, ultraleve e responsiva (zero overhead de imagem)
        self.progress_bar = ctk.CTkProgressBar(
            self.frame,
            height=6,
            corner_radius=3,
            fg_color=COLOR_SURFACE_VARIANT,
            progress_color=get_color_primary(),
            mode="indeterminate",
        )
        self.progress_bar.pack(fill="x", padx=SPACING_XLARGE, pady=(SPACING_XSMALL, SPACING_SMALL))
        self.progress_bar.start()

        # Frame para botões de controle (Parar / Minimizar)
        if on_cancel is not None or on_minimize is not None:
            self.frame_botoes = ctk.CTkFrame(self.frame, fg_color="transparent")
            self.frame_botoes.pack(pady=(SPACING_XSMALL, SPACING_MEDIUM))

            if on_cancel is not None:
                self.btn_cancel = ctk.CTkButton(
                    self.frame_botoes,
                    text="⏹ Parar Processo",
                    width=140,
                    height=32,
                    corner_radius=RADIUS_BUTTON,
                    fg_color=COLOR_SURFACE_VARIANT,
                    text_color=COLOR_TEXT,
                    hover_color=COLOR_BORDER,
                    border_width=1,
                    border_color=COLOR_BORDER,
                    font=get_font(FONT_SIZE_CAPTION, "bold"),
                    command=self._ao_clicar_cancelar,
                )
                self.btn_cancel.pack(side="left", padx=SPACING_XSMALL)
            else:
                self.btn_cancel = None

            if on_minimize is not None:
                self.btn_minimize = ctk.CTkButton(
                    self.frame_botoes,
                    text=" Minimizar",
                    width=130,
                    height=32,
                    corner_radius=RADIUS_BUTTON,
                    fg_color=COLOR_SURFACE_VARIANT,
                    text_color=COLOR_TEXT,
                    hover_color=COLOR_BORDER,
                    border_width=1,
                    border_color=COLOR_BORDER,
                    font=get_font(FONT_SIZE_CAPTION, "bold"),
                    command=self._ao_clicar_minimizar,
                )
                self.btn_minimize.pack(side="left", padx=SPACING_SMALL)
                self.focar(self.btn_minimize)
            else:
                self.btn_minimize = None
        else:
            self.frame_botoes = None
            self.btn_cancel = None
            self.btn_minimize = None

    def _ao_clicar_cancelar(self) -> None:
        if self._cancel_requested:
            return
        self._cancel_requested = True
        if self.btn_cancel and self.btn_cancel.winfo_exists():
            self.btn_cancel.configure(text="Cancelando...", state="disabled")
        if self.on_cancel:
            self.on_cancel()

    def _ao_clicar_minimizar(self) -> None:
        if self._is_dismissed:
            return
        callback = self.on_minimize
        self.dismiss()
        if callback:
            callback()

    def update_message(self, message: str, submessage: str = "") -> None:
        try:
            if hasattr(self, "label") and self.label.winfo_exists():
                self.label.configure(text=message)
            if hasattr(self, "sublabel") and self.sublabel.winfo_exists():
                if submessage:
                    self.sublabel.configure(text=submessage)
                    if not self.sublabel.winfo_ismapped():
                        if hasattr(self, "progress_bar") and self.progress_bar.winfo_ismapped():
                            self.sublabel.pack(before=self.progress_bar, padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
                        else:
                            self.sublabel.pack(padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
                else:
                    self.sublabel.pack_forget()
        except Exception:
            pass

    def atualizar_etapa(self, etapa: int, total: int, descricao: str) -> None:
        """Atualiza a mensagem de progresso e ajusta a barra de progresso nativa."""
        sub = f"(Etapa {etapa}/{total}: {descricao})"
        self.update_message("Processando documentos...", sub)
        try:
            if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                if total > 0:
                    frac = min(1.0, max(0.0, etapa / total))
                    self.progress_bar.configure(mode="determinate")
                    self.progress_bar.set(frac)
        except Exception:
            pass

    def dismiss(self) -> None:
        self._is_dismissed = True
        try:
            if hasattr(self, "spinner") and self.spinner:
                self.spinner.stop_animation()
        except Exception:
            pass
        try:
            if hasattr(self, "progress_bar") and self.progress_bar and self.progress_bar.winfo_exists():
                self.progress_bar.stop()
        except Exception:
            pass
        super().dismiss()
