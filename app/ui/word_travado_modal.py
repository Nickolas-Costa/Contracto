import customtkinter as ctk
from ui import theme
from ui.base_modal import BaseModal


class WordTravadoModal(BaseModal):
    """Aviso de Word sem resposta com contagem regressiva visível.

    Exibe o prazo antes do encerramento automático da instância travada.
    "Fechar agora" encerra de imediato; fechar a janela apenas dispensa
    o aviso (o prazo do serviço continua valendo).
    """

    _instancia_ativa = None

    def __init__(self, master, nome_arquivo: str, prazo_segundos: int, on_fechar_agora=None):
        super().__init__(master, 560, 300, fechar_no_overlay=False)
        self.on_fechar_agora = on_fechar_agora
        self.restantes = max(1, int(prazo_segundos))
        self.frame.grid_rowconfigure(2, weight=1)

        self.montar_cabecalho(
            "O Word parou de responder", None, icone="warning",
            cores_caixa=("#FEF3C7", "#3B2703"),
            cores_borda=("#F59E0B", "#B45309"),
        )

        ctk.CTkLabel(
            self.frame,
            text=(
                f"O Word parece travado ao converter '{nome_arquivo}'. "
                "Ele será fechado automaticamente para o processo continuar."
            ),
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=480,
            justify="left",
        ).grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 4))

        self.lbl_contagem = ctk.CTkLabel(
            self.frame, text=f"{self.restantes} s",
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.get_color_primary_text(),
        )
        self.lbl_contagem.grid(row=2, column=0, sticky="n", padx=24, pady=(0, 4))

        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 20))
        footer.grid_columnconfigure(0, weight=1)
        btn = self.botao_primario(footer, "Fechar agora", self._do_fechar_agora)
        btn.grid(row=0, column=0, sticky="ew")
        self.focar(btn)

        self._agendar_tick()

    def _agendar_tick(self) -> None:
        try:
            if not self.card.winfo_exists():
                return
            self.card.after(1000, self._tick)
        except Exception:
            pass

    def _tick(self) -> None:
        try:
            if not self.card.winfo_exists():
                return
            self.restantes -= 1
            if self.restantes <= 0:
                self.dismiss()
                return
            self.lbl_contagem.configure(text=f"{self.restantes} s")
            self._agendar_tick()
        except Exception:
            pass

    def _do_fechar_agora(self):
        self.dismiss()
        if self.on_fechar_agora:
            self.on_fechar_agora()
