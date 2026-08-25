"""
Gerenciador de Fila de Execução em Segundo Plano (Background Queue Manager).

Permite que o processamento de geração e conversão de documentos seja desacoplado
da interface gráfica, possibilitando:
1. Execução contínua em segundo plano mesmo se o aplicativo perder foco, for minimizado ou com Alt+Tab.
2. Enfileiramento de múltiplos lotes/processos sequencialmente.
3. Notificações e atualizações em tempo real para a barra superior e modais.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from models.participant import Participant
from services.generator_service import gerar_documentos
from services.pdfa_converter import ProcessoCanceladoError
from services.stage2_service import ResultadoEtapa2, executar_etapa2
from utils.profile_manager import Perfil


@dataclass
class ProcessJob:
    """Representa uma solicitação de geração e organização de documentos na fila."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    titulo: str = ""
    participantes: list[Participant] = field(default_factory=list)
    pasta_saida: Path = field(default_factory=Path)
    documentos_externos: dict[str, Path] = field(default_factory=dict)
    forms_selecionados: list[str] = field(default_factory=list)
    formato_saida: str = "PDF/A-2b"
    perfil: Optional[Perfil] = None

    status: str = "na_fila"  # "na_fila", "executando", "concluido", "erro", "cancelado"
    etapa_atual: int = 1
    etapa_total: int = 3
    mensagem: str = "Aguardando na fila..."
    submensagem: str = ""
    cancel_event: threading.Event = field(default_factory=threading.Event)
    resultado: Optional[ResultadoEtapa2] = None
    erro: Optional[str] = None
    criado_em: float = field(default_factory=time.time)


class QueueManager:
    """Orquestrador de tarefas em fila com thread trabalhadora dedicada em background."""

    def __init__(self):
        self._lock = threading.Lock()
        self._fila: list[ProcessJob] = []
        self._job_ativo: Optional[ProcessJob] = None
        self._historico: list[ProcessJob] = []
        self._thread_trabalhadora: Optional[threading.Thread] = None
        self._executando = True

        # Callbacks de interface (disparados através de marshaling de thread)
        self.on_job_started: Optional[Callable[[ProcessJob], None]] = None
        self.on_job_progress: Optional[Callable[[ProcessJob, int, int, str], None]] = None
        self.on_job_completed: Optional[Callable[[ProcessJob, ResultadoEtapa2], None]] = None
        self.on_job_failed: Optional[Callable[[ProcessJob, str], None]] = None
        self.on_job_cancelled: Optional[Callable[[ProcessJob], None]] = None
        self.on_queue_changed: Optional[Callable[[], None]] = None

    def adicionar_job(
        self,
        participantes: list[Participant],
        pasta_saida: Path,
        documentos_externos: dict[str, Path],
        forms_selecionados: list[str],
        formato_saida: str,
        perfil: Perfil,
    ) -> ProcessJob:
        """Enfileira um novo lote para processamento em segundo plano."""
        nome_principal = participantes[0].nome_completo if participantes else "Documentos"
        titulo = f"{nome_principal} ({len(participantes)} participante{'s' if len(participantes) > 1 else ''})"

        job = ProcessJob(
            titulo=titulo,
            participantes=participantes,
            pasta_saida=pasta_saida,
            documentos_externos=documentos_externos,
            forms_selecionados=forms_selecionados,
            formato_saida=formato_saida,
            perfil=perfil,
        )

        with self._lock:
            self._fila.append(job)

        self._notificar_mudanca_fila()
        self._garantir_worker_ativo()
        return job

    def cancelar_job_ativo(self) -> None:
        """Sinaliza cancelamento para o job atualmente em execução."""
        with self._lock:
            if self._job_ativo and not self._job_ativo.cancel_event.is_set():
                self._job_ativo.cancel_event.set()
                self._job_ativo.status = "cancelando"
                self._job_ativo.mensagem = "Cancelando operação..."

    def cancelar_job(self, job_id: str) -> None:
        """Cancela um job específico (ativo ou que ainda esteja na fila)."""
        with self._lock:
            if self._job_ativo and self._job_ativo.id == job_id:
                self._job_ativo.cancel_event.set()
                self._job_ativo.status = "cancelando"
                return

            for job in list(self._fila):
                if job.id == job_id:
                    job.status = "cancelado"
                    self._fila.remove(job)
                    self._historico.append(job)
                    self._notificar_mudanca_fila()
                    return

    def obter_job_ativo(self) -> Optional[ProcessJob]:
        with self._lock:
            return self._job_ativo

    def obter_total_fila(self) -> int:
        with self._lock:
            total = len(self._fila)
            if self._job_ativo is not None:
                total += 1
            return total

    def tem_trabalho_ativo(self) -> bool:
        with self._lock:
            return self._job_ativo is not None or len(self._fila) > 0

    def obter_status_resumo(self) -> str:
        """Retorna uma string compacta para exibição na barra superior."""
        with self._lock:
            if self._job_ativo:
                total = len(self._fila) + 1
                etapa_str = f"Etapa {self._job_ativo.etapa_atual}/{self._job_ativo.etapa_total}"
                if total > 1:
                    return f"FILA: [{total}] {etapa_str}"
                return f"FILA: {etapa_str}"
            elif self._fila:
                return f"FILA: {len(self._fila)} pendente(s)"
            return "FILA: Ociosa"

    def _garantir_worker_ativo(self) -> None:
        if self._thread_trabalhadora is None or not self._thread_trabalhadora.is_alive():
            self._thread_trabalhadora = threading.Thread(
                target=self._executar_worker_loop,
                daemon=True,
                name="ContractoQueueWorker",
            )
            self._thread_trabalhadora.start()

    def _executar_worker_loop(self) -> None:
        """Loop contínuo que retira e executa jobs da fila sequencialmente."""
        while self._executando:
            proximo_job: Optional[ProcessJob] = None
            with self._lock:
                if self._fila:
                    proximo_job = self._fila.pop(0)
                    self._job_ativo = proximo_job
                    proximo_job.status = "executando"
                else:
                    self._job_ativo = None

            if proximo_job is None:
                break

            self._notificar_mudanca_fila()
            self._processar_job(proximo_job)

            with self._lock:
                self._historico.append(proximo_job)
                self._job_ativo = None

            self._notificar_mudanca_fila()

    def _processar_job(self, job: ProcessJob) -> None:
        """Executa a geração e conversão completa de um único ProcessJob."""
        if self.on_job_started:
            self.on_job_started(job)

        try:
            # 1. Geração de documentos da Etapa 1
            job.etapa_atual = 1
            job.mensagem = "Processando documentos..."
            job.submensagem = "(Etapa 1/3: Gerando formulários preenchidos)"
            self._notificar_progresso(job, 1, 3, "Gerando formulários preenchidos")

            def _on_progresso_etapa1(idx, total, nome_doc):
                sub = f"Gerando documento {idx}/{total}"
                job.submensagem = f"(Etapa 1/3: {sub})"
                self._notificar_progresso(job, 1, 3, sub)

            resultado_geracao = gerar_documentos(
                job.participantes,
                job.perfil,
                job.pasta_saida,
                formularios_ativos=job.forms_selecionados,
                cancel_event=job.cancel_event,
                on_progress=_on_progresso_etapa1,
            )

            # 2. Conversão da Etapa 2
            job.etapa_atual = 2
            job.submensagem = "(Etapa 2/3: Convertendo arquivos para PDF/A)"
            self._notificar_progresso(job, 2, 3, "Convertendo arquivos para PDF/A")

            def _on_progresso_etapa2(idx, total, nome_doc):
                sub = f"Convertendo documento {idx}/{total}"
                job.submensagem = f"(Etapa 2/3: {sub})"
                self._notificar_progresso(job, 2, 3, sub)

            resultado_etapa2 = executar_etapa2(
                pasta_base=job.pasta_saida,
                participantes=job.participantes,
                arquivos_gerados_etapa1=resultado_geracao.arquivos_gerados,
                documentos_externos=job.documentos_externos,
                formato_saida=job.formato_saida,
                cancel_event=job.cancel_event,
                on_progress=_on_progresso_etapa2,
            )

            # 3. Conclusão
            job.etapa_atual = 3
            job.submensagem = "(Etapa 3/3: Concluindo processo)"
            self._notificar_progresso(job, 3, 3, "Concluindo processo")

            if resultado_etapa2.get("cancelado") or job.cancel_event.is_set():
                job.status = "cancelado"
                if self.on_job_cancelled:
                    self.on_job_cancelled(job)
            elif resultado_etapa2["sucesso"]:
                job.status = "concluido"
                job.resultado = resultado_etapa2
                if self.on_job_completed:
                    self.on_job_completed(job, resultado_etapa2)
            else:
                job.status = "erro"
                job.erro = resultado_etapa2["mensagem"]
                if self.on_job_failed:
                    self.on_job_failed(job, resultado_etapa2["mensagem"])

        except ProcessoCanceladoError:
            job.status = "cancelado"
            if self.on_job_cancelled:
                self.on_job_cancelled(job)
        except Exception as exc:
            job.status = "erro"
            job.erro = str(exc)
            if self.on_job_failed:
                self.on_job_failed(job, str(exc))

    def _notificar_progresso(self, job: ProcessJob, etapa: int, total: int, submsg: str) -> None:
        if self.on_job_progress:
            try:
                self.on_job_progress(job, etapa, total, submsg)
            except Exception:
                pass

    def _notificar_mudanca_fila(self) -> None:
        if self.on_queue_changed:
            try:
                self.on_queue_changed()
            except Exception:
                pass
