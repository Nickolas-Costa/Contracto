"""
Módulo gerenciador de loaders animados e animações GIF da aplicação Contracto.

Implementa um player de GIF nativo em alta qualidade integrado ao CustomTkinter
e um sistema circular de rotação entre 10 modelos distintos de loaders para cada
nova ação de carregamento do sistema.
"""

from pathlib import Path
from typing import Optional
from PIL import Image, ImageSequence
import customtkinter as ctk

from utils.resource_path import caminho_recurso

# Lista sequencial dos 10 loaders oficiais da aplicação
LOADER_FILENAMES = [
    "spinner_expand.gif",
    "spinner_dots_spin.gif",
    "spinner_snake.gif",
    "spinner_dots_juggle.gif",
    "spinner_spiral.gif",
    "spinner_turbine.gif",
    "spinner_dots_queue.gif",
    "spinner_half_circles.gif",
    "spinner_transparency.gif",
    "spinner_dots_line.gif",
]

_CURRENT_LOADER_INDEX = 0


def get_next_loader_path() -> Path:
    """Retorna o caminho do próximo loader GIF na rotação e avança o índice circularmente."""
    global _CURRENT_LOADER_INDEX
    nome = LOADER_FILENAMES[_CURRENT_LOADER_INDEX % len(LOADER_FILENAMES)]
    _CURRENT_LOADER_INDEX = (_CURRENT_LOADER_INDEX + 1) % len(LOADER_FILENAMES)
    return caminho_recurso("assets", "loaders", nome)


def reset_loader_cycle() -> None:
    """Reinicia o índice da rotação de loaders para o início."""
    global _CURRENT_LOADER_INDEX
    _CURRENT_LOADER_INDEX = 0


_LOADER_FRAMES_CACHE = {}


class AnimatedGifLabel(ctk.CTkLabel):
    """Widget de Label animado para exibição fluida de frames de GIF em tempo real."""

    def __init__(
        self,
        master,
        gif_path: Optional[Path] = None,
        size: tuple[int, int] = (44, 44),
        **kwargs,
    ):
        super().__init__(master, text="", **kwargs)
        self.gif_path = gif_path or get_next_loader_path()
        self.size = size
        self._frames = []
        self._delays = []
        self._frame_index = 0
        self._timer_id = None
        self._is_running = False

        self._load_gif()
        if self._frames:
            self.configure(image=self._frames[0])
            self.start_animation()

    def _load_gif(self) -> None:
        try:
            if not self.gif_path or not self.gif_path.exists():
                return

            cache_key = (str(self.gif_path), self.size)
            if cache_key in _LOADER_FRAMES_CACHE:
                cached_frames, cached_delays = _LOADER_FRAMES_CACHE[cache_key]
                self._frames = list(cached_frames)
                self._delays = list(cached_delays)
                return

            im = Image.open(self.gif_path)
            for frame in ImageSequence.Iterator(im):
                f_resized = frame.copy().convert("RGBA").resize(self.size, Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=f_resized, dark_image=f_resized, size=self.size)
                self._frames.append(ctk_img)
                delay = frame.info.get("duration", 50)
                if delay < 20:
                    delay = 50
                self._delays.append(delay)

            _LOADER_FRAMES_CACHE[cache_key] = (list(self._frames), list(self._delays))
        except Exception:
            pass

    def start_animation(self) -> None:
        self._is_running = True
        self._animate()

    def _animate(self) -> None:
        if not self._is_running or not self.winfo_exists() or not self._frames:
            return

        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self.configure(image=self._frames[self._frame_index])

        delay = (
            self._delays[self._frame_index]
            if self._frame_index < len(self._delays)
            else 50
        )
        self._timer_id = self.after(delay, self._animate)

    def stop_animation(self) -> None:
        self._is_running = False
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def destroy(self) -> None:
        self.stop_animation()
        super().destroy()
