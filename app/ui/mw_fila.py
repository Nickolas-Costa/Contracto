"""Métodos de fila da janela principal (mixin de MainWindow).

Movido verbatim de `app/ui/main_window.py`: mesma ordem, mesmo código,
sem mudança de comportamento. A classe `MainWindow` herda este mixin.
"""

"""
Janela principal da aplicação Contracto.

Implementa a navegação entre telas (Início, Perfis, Configurações),
o gradiente de fundo inspirado no PDFCreator, a fila de processamento
em segundo plano (com suporte a minimizar para a toolbar), e a integração
com o sistema de perfis e configurações.
"""

import queue
import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image

from models.participant import Participant
from services.field_calculator import calcular
from services.generator_service import gerar_documentos, validar_antes_de_gerar
from services.profile_composer import combinar_perfis, limite_participantes_para_pagina
from services.pdf_service import PdfServiceError
from services.pdfa_converter import ProcessoCanceladoError
from services.queue_manager import ProcessJob, QueueManager
from services.stage2_service import ResultadoEtapa2, executar_etapa2
from ui.animated_loader import CanvasSpinner
from ui.alert_modal import AlertModal
from ui.campo_dinamico_widget import CampoDinamicoWidget
from ui.date_picker import DatePickerPopup
from ui.document_frame import DocumentFrame
from ui.feedback_toast import show_toast
from ui.loading_modal import LoadingModal
from ui.participant_frame import ParticipantFrame
from ui.profiles_frame import ProfilesFrame
from ui.settings_frame import SettingsFrame
from ui.theme import (
    COLOR_BACKGROUND, COLOR_BORDER, COLOR_BORDER_ERROR, COLOR_ERROR, COLOR_SUCCESS,
    COLOR_SURFACE, COLOR_SURFACE_VARIANT, COLOR_TEXT, COLOR_TEXT_DISABLED,
    COLOR_TEXT_SECONDARY, COLOR_WARNING,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3,
    RADIUS_BUTTON, RADIUS_CARD, RADIUS_INPUT,
    SPACING_LARGE, SPACING_MEDIUM, SPACING_SMALL, SPACING_XLARGE, SPACING_XXLARGE,
    SPACING_XSMALL,
    aplicar_gradiente, configurar_autoscroll, configure_appearance, get_color_primary,
    get_color_primary_dark_gradient, get_color_primary_hover, get_color_primary_light,
    get_color_primary_text, get_font, get_icon, reload_theme, rolar_para_widget_se_necessario,
    icone_para_secao, configurar_janela_modal,
)
from utils import config_manager
from utils.caminhos import pasta_downloads
from utils.date_formatter import validar_data
from utils.document_validator import formatar_data_progressiva
from ports.dialog import selecionar_pasta
from utils.logger import configurar_logger, obter_logger
from utils.profile_manager import (
    PERFIL_PADRAO_NOME, Perfil, carregar_perfis, listar_nomes_perfis,
    listar_perfis_por_modo, listar_nomes_perfis_por_modo, obter_perfil,
)
from version import __version__



class FilaMixin:
    def _ao_minimizar_modal_fila(self) -> None:
        """Minimiza o modal de progresso, retorna à tela inicial limpa e atualiza o status na toolbar."""
        self._modal_fila_ativo = None
        self._resetar_aplicacao()
        self._atualizar_botao_fila_status()
        show_toast(self, "Processo minimizado. Executando em segundo plano.", "info")

    def _abrir_modal_fila(self) -> None:
        """Reabre o modal de acompanhamento do processo ativo na fila."""
        job_ativo = self.queue_manager.obter_job_ativo()
        if job_ativo is None:
            show_toast(self, "Nenhum processo em execução no momento.", "info")
            return

        self._modal_fila_ativo = LoadingModal(
            self,
            message=job_ativo.mensagem or "Processando documentos...",
            submessage=job_ativo.submensagem or f"(Etapa {job_ativo.etapa_atual}/{job_ativo.etapa_total})",
            on_cancel=lambda: self.queue_manager.cancelar_job(job_ativo.id),
            on_minimize=self._ao_minimizar_modal_fila,
        )

    def _iniciar_loop_eventos_ui(self) -> None:
        """Processa eventos enviados pela thread de background no loop principal do Tkinter."""
        def _poll():
            try:
                while hasattr(self, "_ui_event_queue") and not self._ui_event_queue.empty():
                    fn, args = self._ui_event_queue.get_nowait()
                    fn(*args)
            except Exception:
                pass
            try:
                if self.winfo_exists():
                    self._fila_timer = self.after(40, _poll)
            except Exception:
                pass

        self._fila_timer = self.after(40, _poll)

    def _ao_iniciar_job_fila(self, job: ProcessJob) -> None:
        self._ui_event_queue.put((self._ui_job_iniciado, (job,)))

    def _ao_word_travar_na_fila(self, nome_arquivo: str, prazo: int, encerrar) -> None:
        """Recebe o aviso da thread de fundo e agenda o modal na thread da UI."""
        self._ui_event_queue.put((self._mostrar_aviso_word, (nome_arquivo, prazo, encerrar)))

    def _mostrar_aviso_word(self, nome_arquivo: str, prazo: int, encerrar) -> None:
        """Exibe a contagem regressiva antes do encerramento do Word travado."""
        from ui.word_travado_modal import WordTravadoModal

        WordTravadoModal(self, nome_arquivo, prazo, on_fechar_agora=encerrar)

    def _ui_job_iniciado(self, job: ProcessJob) -> None:
        self._atualizar_botao_fila_status()
        if self._modal_fila_ativo:
            self._modal_fila_ativo.update_message(
                "Processando documentos...",
                job.submensagem or f"(Etapa {job.etapa_atual}/{job.etapa_total})"
            )

    def _ao_progresso_job_fila(self, job: ProcessJob, etapa: int, total: int, submsg: str) -> None:
        self._ui_event_queue.put((self._ui_job_progresso, (job, etapa, total, submsg)))

    def _ui_job_progresso(self, job: ProcessJob, etapa: int, total: int, submsg: str) -> None:
        self._atualizar_botao_fila_status()
        if self._modal_fila_ativo:
            self._modal_fila_ativo.atualizar_etapa(etapa, total, submsg)

    def _ao_concluir_job_fila(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        self._ui_event_queue.put((self._ui_job_concluido, (job, resultado)))

    def _ui_job_concluido(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        modal_estava_aberto = (self._modal_fila_ativo is not None)
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None

        # Alerta sonoro amigável do Windows
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

        # Exibir modal de confirmação para o usuário saber que finalizou e poder abrir a pasta
        msg = f"{resultado['mensagem']}\n\nPasta de saída:\n{resultado['pasta_pdfa']}"
        from ui.confirm_modal import ConfirmModal

        def _abrir():
            self._abrir_pasta(resultado["pasta_pdfa"])

        ConfirmModal(
            self,
            titulo="Geração Concluída ✓",
            subtitulo=f"Processo '{job.titulo}' finalizado com sucesso!\n\n" + msg + "\n\nDeseja abrir a pasta com os documentos agora?",
            on_confirm=_abrir,
            texto_confirmar="Sim, Abrir Pasta",
            texto_cancelar="Fechar",
        )

        preservar = bool(hasattr(self, "chk_preservar_dados") and self.chk_preservar_dados.get())
        if modal_estava_aberto:
            self._resetar_aplicacao(preservar_dados=preservar)
        else:
            show_toast(self, f"Sucesso: {job.titulo} finalizado!", "success")

        self._exibir_status_concluido_temporario(job, resultado)

    def _exibir_status_concluido_temporario(self, job: ProcessJob, resultado: ResultadoEtapa2) -> None:
        if not hasattr(self, "btn_fila_status"):
            return

        self._status_concluido_ativo = True
        self.btn_fila_status.configure(
            text=" FILA: Concluído ✓",
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS,
            command=lambda: self._abrir_pasta(resultado["pasta_pdfa"]),
        )
        self.btn_fila_status.grid()

        def _expirar():
            self._status_concluido_ativo = False
            self._atualizar_botao_fila_status()

        self.after(8000, _expirar)

    def _ao_erro_job_fila(self, job: ProcessJob, erro: str) -> None:
        self._ui_event_queue.put((self._ui_job_erro, (job, erro)))

    def _ui_job_erro(self, job: ProcessJob, erro: str) -> None:
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None
        show_toast(self, f"Erro: {erro}", "error")
        self._atualizar_botao_fila_status()

    def _ao_cancelado_job_fila(self, job: ProcessJob) -> None:
        self._ui_event_queue.put((self._ui_job_cancelado, (job,)))

    def _ui_job_cancelado(self, job: ProcessJob) -> None:
        if self._modal_fila_ativo:
            self._modal_fila_ativo.dismiss()
            self._modal_fila_ativo = None
        show_toast(self, f"Processo '{job.titulo}' foi cancelado.", "warning")
        self._atualizar_botao_fila_status()

    def _ao_mudar_fila(self) -> None:
        self._ui_event_queue.put((self._atualizar_botao_fila_status, ()))

    def _atualizar_botao_fila_status(self) -> None:
        if not hasattr(self, "btn_fila_status"):
            return

        if getattr(self, "_status_concluido_ativo", False):
            # Mantém exibindo o status de sucesso pelo período definido
            return

        if self.queue_manager.tem_trabalho_ativo():
            resumo = self.queue_manager.obter_status_resumo()
            self.btn_fila_status.configure(
                text=f" {resumo}",
                fg_color=get_color_primary_hover(),
                hover_color=get_color_primary_hover(),
                command=self._abrir_modal_fila,
            )
            self.btn_fila_status.grid()
        else:
            self.btn_fila_status.grid_remove()

    def _resetar_aplicacao(self, preservar_dados: bool = False) -> None:
        self._mostrar_tela("inicio")
        if not preservar_dados:
            for frame in list(self.participant_frames[1:]):
                self._remover_participante(frame)

            if self.participant_frames:
                primeiro = self.participant_frames[0]
                primeiro.limpar_campos()
                
            self.entry_data.delete(0, "end")
            self.entry_data.configure(border_color=COLOR_BORDER)
            for w in self.widgets_dinamicos_globais.values():
                w.limpar()

        if hasattr(self, 'document_frame') and self.document_frame:
            self.document_frame.limpar_campos()

        self.participantes_etapa1 = []
        self.arquivos_gerados_etapa1 = []

        local_padrao = config_manager.obter("local_padrao") or "CAMOCIM-CE"
        self.entry_local.delete(0, "end")
        self.entry_local.insert(0, local_padrao)
        self.entry_local.configure(border_color=COLOR_BORDER)
        
        self.entry_pasta_saida.configure(border_color=COLOR_BORDER)
        self.document_frame.limpar()

    @staticmethod
    @staticmethod
    def _abrir_pasta(caminho: Path | str) -> bool:
        """Compatibilidade: delega para `utils.files.abrir_pasta`."""
        from utils.files import abrir_pasta

        return abrir_pasta(caminho)

