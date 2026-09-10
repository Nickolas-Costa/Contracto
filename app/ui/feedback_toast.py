import customtkinter as ctk
from typing import Callable, Optional

from ui.theme import *

class FeedbackToast(ctk.CTkFrame):
    def __init__(
        self,
        master,
        message: str,
        type: str = 'success',
        on_dismiss: Optional[Callable[[], None]] = None,
        duration_ms: int = 4000,
    ):
        super().__init__(
            master,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self._on_dismiss = on_dismiss
        self._duration_ms = duration_ms
        self._dismiss_timer = None
        self._mensagem = message

        # Insígnia com glifo branco: o amarelo do tema (2.70:1) reprova o
        # contraste, por isso o aviso usa um âmbar escuro (5.02:1).
        # Demais pares medidos: success 5.13, error 4.98, primary 4.52.
        self.type_config = {
            'success': {'color': COLOR_SUCCESS, 'icon': '✓'},
            'info': {'color': get_color_primary(), 'icon': 'i'},
            'warning': {'color': "#B45309", 'icon': '!'},
            'error': {'color': COLOR_ERROR, 'icon': '✕'}
        }
        
        config = self.type_config.get(type, self.type_config['success'])
        
        self.toast_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=RADIUS_BUTTON)
        self.toast_frame.pack(padx=SPACING_SMALL, pady=SPACING_SMALL, fill="both", expand=True)
        
        self.icon_label = ctk.CTkLabel(
            self.toast_frame, text=config['icon'], width=32, height=32,
            fg_color=config['color'], corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_BODY, "bold"), text_color="#FFFFFF",
        )
        self.icon_label.pack(side="left", padx=(SPACING_XSMALL, SPACING_SMALL), pady=SPACING_XSMALL)
        
        self.msg_label = ctk.CTkLabel(
            self.toast_frame, text=message, wraplength=390, justify="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT,
        )
        self.msg_label.pack(side="left", padx=(0, SPACING_MEDIUM), pady=SPACING_SMALL)
        
    def show(self, parent_width, parent_height):
        self._limites = (parent_width, parent_height)
        self._posicionar()
        try:
            self.after_idle(self._posicionar)
        except Exception:
            pass
        self._dismiss_timer = self.after(self._duration_ms, self._dismiss)

    def _posicionar(self) -> None:
        # Borda direita presa à janela (relx + anchor): o X nunca depende
        # de medida. A largura vem de linha única exata (tk.Label oculto),
        # limitada, e forçada no rótulo (CTkLabel ignora wraplength).
        try:
            if not self.winfo_exists():
                return
            parent_width, _parent_height = self._limites
            margem = SPACING_LARGE
            alvo = max(200, parent_width - 2 * margem)
            try:
                import tkinter as tk

                familia, tamanho = get_font(FONT_SIZE_BODY)[:2]
                prova = tk.Label(
                    self, text=self._mensagem, font=(familia, tamanho)
                )
                linha_unica = prova.winfo_reqwidth()
                prova.destroy()
            except Exception:
                linha_unica = len(self._mensagem) * 8
            largura_texto = max(50, min(linha_unica, alvo - 120))
            self.msg_label.configure(wraplength=largura_texto, width=largura_texto)
            try:
                fator = max(1.0, float(self.winfo_fpixels("1i")) / 96.0)
            except Exception:
                fator = 1.0
            self.place(relx=1.0, x=-margem / fator, y=58 / fator, anchor="ne")
            self.lift()
        except Exception:
            pass

    def _dismiss(self):
        if not self.winfo_exists():
            return
        if self._dismiss_timer is not None:
            try:
                self.after_cancel(self._dismiss_timer)
            except Exception:
                pass
            self._dismiss_timer = None
        callback = self._on_dismiss
        self._on_dismiss = None
        if getattr(self.master, "_feedback_toast_ativo", None) is self:
            self.master._feedback_toast_ativo = None
        try:
            self.destroy()
        finally:
            if callback:
                callback()

def _dispensar_ativo(janela) -> None:
    """Dispensa o toast ativo da janela (Escape)."""
    try:
        ativo = getattr(janela, "_feedback_toast_ativo", None)
        if ativo is not None and ativo.winfo_exists():
            ativo._dismiss()
    except Exception:
        pass


def show_toast(
    parent,
    message: str,
    type: str = 'success',
    on_dismiss: Optional[Callable[[], None]] = None,
    duration_ms: int = 4000,
):
    anterior = getattr(parent, "_feedback_toast_ativo", None)
    if anterior is not None and anterior.winfo_exists():
        anterior._dismiss()
    if not getattr(parent, "_feedback_toast_escape_ligado", False):
        try:
            parent.bind("<Escape>", lambda e, alvo=parent: _dispensar_ativo(alvo), add="+")
            parent._feedback_toast_escape_ligado = True
        except Exception:
            pass
    toast = FeedbackToast(parent, message, type, on_dismiss, duration_ms)
    parent._feedback_toast_ativo = toast
    parent.update_idletasks()
    toast.show(parent.winfo_width(), parent.winfo_height())
    return toast
