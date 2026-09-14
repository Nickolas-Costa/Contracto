"""Fachada da fila: operações separadas, snapshots privados e publicação isolada."""
import copy
import hashlib
import json
import secrets
import shutil
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path

from models.participant import Participant
from ports import binaries
from services.generator_service import gerar_documentos_de_perfis, validar_antes_de_gerar
from services.pdfa_converter import ProcessoCanceladoError
from services.profile_composer import combinar_perfis
from services.form_validation import preparar_participantes
from services.queue_manager import QueueManager
from services.stage2_service import executar_etapa2
from utils.cpf_validator import validar_cpf
from utils.logger import contexto_log_api
from utils.profile_manager import carregar_perfis

from .models import Error, JobState
from .selections import SelectionError, Selections


class ApiError(Exception):
    def __init__(self, code, message, status=400, issues=None):
        self.code, self.message, self.status = code, message, status
        self.issues = issues or []
        super().__init__(message)


def capabilities():
    return {"word": binaries.word_status().disponivel,
            "ghostscript": binaries.ghostscript_status().disponivel,
            "pdf": True}


class Jobs:
    def __init__(self, profiles=None, max_jobs=200):
        self.selections = Selections()
        self.queue = QueueManager()
        self._lock = threading.RLock()
        self._closed = False
        self._states = {}
        self._requests = {}
        self._outputs = {}
        self.max_jobs = max_jobs
        with contexto_log_api():
            self.profiles = {secrets.token_hex(16): copy.deepcopy(p)
                             for p in (profiles if profiles is not None else carregar_perfis())}

    def catalog(self):
        # Caminhos e mapeamentos internos dos templates nunca saem pelo HTTP.
        return [{"profile_id": key, "name": p.nome, "mode": p.modo_fluxo,
                 "max_participants": p.max_participantes,
                 "fields": [asdict(c) for c in p.campos_entrada]}
                for key, p in self.profiles.items()]

    def _profiles(self, ids):
        if len(ids) != len(set(ids)):
            raise ApiError("duplicate_profiles", "Não repita perfis")
        try:
            profiles = [copy.deepcopy(self.profiles[key]) for key in ids]
        except KeyError:
            raise ApiError("profile_not_found", "Perfil não encontrado", 404) from None
        if len(profiles) > 1 and any(p.modo_fluxo != "formulario_simples" for p in profiles):
            raise ApiError("incompatible_profiles", "Somente perfis simples podem ser combinados")
        return profiles

    def compose(self, request):
        profiles = self._profiles(request.profile_ids)
        result = combinar_perfis(profiles)
        if result.erros or result.perfil is None:
            raise ApiError("incompatible_profiles", "Perfis com campos incompatíveis", 409)
        return {"profile_ids": request.profile_ids,
                "max_participants": result.perfil.max_participantes,
                "fields": [asdict(c) for c in result.perfil.campos_entrada]}

    def _participants(self, values):
        result, issues = [], []
        for index, value in enumerate(values, 1):
            data = value.model_dump(exclude_unset=True)
            dynamic = data.get("campos_dinamicos", {})
            for key in ("endereco", "data_assinatura", "local_assinatura", "nome_completo", "cpf"):
                if key in data and key in dynamic and data[key] != dynamic[key]:
                    issues.append({"participant": index, "field": key})
            participant = Participant(**data)
            result.append(participant)
            if not participant.nome_completo.strip():
                issues.append({"participant": index, "field": "nome_completo"})
            if not validar_cpf(participant.cpf):
                issues.append({"participant": index, "field": "cpf"})
        if issues:
            raise ApiError("invalid_participants", "Confira os campos indicados e valores duplicados", 422, issues=issues)
        return result

    def generate(self, request):
        retry = self._request_retry("generate", request)
        if retry is not None:
            return retry
        profiles, participants, field_errors = self._prepare_fields(request)
        if field_errors:
            raise ApiError("invalid_fields", "Confira os campos obrigatórios e seus formatos", 422, issues=field_errors)
        return self._generate_prepared(request, profiles, participants)

    def _prepare_fields(self, request):
        profiles = self._profiles(request.profile_ids)
        self.compose(request)
        participants = self._participants(request.participants)
        combined = combinar_perfis(profiles).perfil
        allowed = {c.id for c in combined.campos_entrada} | {"nome", "nome_completo", "cpf", "endereco", "data_assinatura", "local_assinatura"}
        if any(set(p.campos_dinamicos) - allowed for p in participants):
            raise ApiError("unknown_fields", "Há campos que não pertencem aos perfis selecionados", 422)
        participants, field_errors = preparar_participantes(participants, combined)
        return profiles, participants, field_errors

    def preview(self, request):
        profiles, participants, errors = self._prepare_fields(request)
        fields = combinar_perfis(profiles).perfil.campos_entrada
        return {"values": [{f.id: p.obter_campo(f.id) for f in fields} for p in participants], "issues": errors}

    def _generate_prepared(self, request, profiles, participants):
        output = self.selections.resolve(request.output_id, "directory")
        for profile in profiles:
            if len(participants) > profile.max_participantes:
                raise ApiError("participant_limit", "Quantidade de participantes excede o perfil", 422)
            with contexto_log_api():
                errors = validar_antes_de_gerar(participants, profile, output)
            if errors:
                raise ApiError("invalid_generation", "Confira campos obrigatórios, data e modelos do perfil", 422)

        def operation(folder, job, progress):
            result = gerar_documentos_de_perfis(participants, profiles, folder,
                                               cancel_event=job.cancel_event, on_progress=progress)
            if result.avisos or not result.arquivos_gerados:
                raise ApiError("generation_failed", "Não foi possível gerar todos os formulários")
            return result.arquivos_gerados

        return self._submit(request.output_id, operation, "generate", request)

    def process(self, request):
        retry = self._request_retry("process", request)
        if retry is not None:
            return retry
        participants = self._participants(request.participants)
        self.selections.resolve(request.output_id, "directory")
        if not request.file_ids and not request.attachments:
            raise ApiError("empty_job", "Selecione ao menos um documento", 422)
        kinds = [a.document_type for a in request.attachments]
        if len(kinds) != len(set(kinds)):
            raise ApiError("duplicate_types", "Não repita tipos de anexos", 422)
        ids = request.file_ids + [a.file_id for a in request.attachments]
        if len(ids) != len(set(ids)):
            raise ApiError("duplicate_files", "Não repita arquivos", 422)
        paths = [self.selections.resolve(key, "file") for key in ids]
        if any(p.suffix.lower() != ".pdf" for p in paths[:len(request.file_ids)]):
            raise ApiError("invalid_format", "Arquivos da geração devem ser PDF", 422)
        caps = capabilities()
        if request.format == "PDF/A-2b" and not caps["ghostscript"]:
            raise ApiError("ghostscript_unavailable", "Instale o Ghostscript para gerar PDF/A", 409)
        if any(p.suffix.lower() == ".rtf" for p in paths) and not caps["word"]:
            raise ApiError("word_unavailable", "Instale o Microsoft Word para converter RTF", 409)

        def operation(folder, job, progress):
            # O serviço legado remove PDFs de entrada após processar: copiar apenas
            # para a área privada do trabalho, preservando todos os originais.
            inputs = folder / "inputs"
            inputs.mkdir()
            generated = []
            for index, key in enumerate(request.file_ids):
                source = self.selections.resolve(key, "file")
                target = inputs / f"{index + 1}-{source.name}"
                shutil.copy2(source, target)
                generated.append(target)
            attachments = {}
            for index, attachment in enumerate(request.attachments):
                source = self.selections.resolve(attachment.file_id, "file")
                target = inputs / f"attachment-{index}{source.suffix.lower()}"
                shutil.copy2(source, target)
                attachments[attachment.document_type] = target
            result = executar_etapa2(folder, participants, generated, attachments,
                                     formato_saida=request.format, cancel_event=job.cancel_event,
                                     on_progress=progress)
            if result.get("cancelado"):
                raise ProcessoCanceladoError()
            if not result["sucesso"] or len(result["resultado_lote"].convertidos) != len(ids):
                raise ApiError("processing_failed", "Não foi possível concluir o processamento")
            shutil.rmtree(inputs)
            return [r.caminho_saida for r in result["resultado_lote"].convertidos]

        return self._submit(request.output_id, operation, "process", request)

    @staticmethod
    def _fingerprint(kind, request):
        body = json.dumps(request.model_dump(exclude={"request_id"}), sort_keys=True, ensure_ascii=True)
        return hashlib.sha256((kind + body).encode()).hexdigest()

    def _request_retry(self, kind, request):
        with self._lock:
            if self._closed:
                raise ApiError("closed", "Sessão encerrada", 503)
            if request.request_id and request.request_id in self._requests:
                fingerprint, key = self._requests[request.request_id]
                if fingerprint != self._fingerprint(kind, request):
                    raise ApiError("request_conflict", "Identificador já usado por outro comando", 409)
                return self.snapshot(key)
        return None

    def _submit(self, output_id, operation, kind=None, request=None):
        with self._lock:
            if request is not None:
                retry = self._request_retry(kind, request)
                if retry is not None:
                    return retry
            if self._closed:
                raise ApiError("closed", "Sessão encerrada", 503)
            if len(self._states) >= self.max_jobs:
                raise ApiError("job_limit", "Limite de trabalhos da sessão; reinicie o aplicativo", 429)
            key = secrets.token_hex(16)
            self._states[key] = JobState(job_id=key, status="queued")
            if request is not None and request.request_id:
                self._requests[request.request_id] = (self._fingerprint(kind, request), key)

            def task(job):
                staging = published = None
                registered = []
                terminal = None
                failure = None
                state = self._states[key]
                try:
                    with contexto_log_api():
                        with self._lock:
                            self._check_cancel(job)
                            state.status = "running"
                        output = self.selections.resolve(output_id, "directory")
                        staging = Path(tempfile.mkdtemp(prefix=".contracto-", dir=output))

                        def progress(index, total, _private_name):
                            with self._lock:
                                state.completed, state.total = index, total

                        files = operation(staging, job, progress)
                        if not files or len(set(files)) != len(files):
                            raise ApiError("incomplete_output", "Os documentos não produziram saídas distintas")
                        relative = [p.relative_to(staging) for p in files]
                        with self._lock:
                            self._check_cancel(job)
                            self.selections.resolve(output_id, "directory")
                            destination = output / f"Contracto-{key}"
                            if destination.exists():
                                raise ApiError("output_conflict", "Destino já existe")
                            staging.rename(destination)
                            published, staging = destination, None
                            for path in relative:
                                registered.append(self.selections.register(destination / path, "file"))
                            state.file_ids = registered
                            self._outputs[key] = self.selections.register(destination, "directory")
                            state.status = "completed"
                            state.completed = state.total = len(files)
                            published = None  # Saída concluída pertence ao usuário.
                except ProcessoCanceladoError:
                    terminal = "cancelled"
                except Exception as exc:
                    terminal = "cancelled" if job.cancel_event.is_set() else "failed"
                    if terminal == "failed":
                        failure = Error(code=exc.code if isinstance(exc, ApiError) else "job_failed",
                                        message=exc.message if isinstance(exc, ApiError) else "Operação não concluída; confira os documentos e selecione novamente")
                finally:
                    if published:
                        self.selections.revoke(registered)
                    for folder in (staging, published):
                        if folder:
                            # Pasta criada por este trabalho; nunca a pasta selecionada.
                            try:
                                shutil.rmtree(folder)
                            except OSError:
                                terminal = "failed"
                                failure = Error(code="cleanup_failed", message="Não foi possível limpar os temporários; verifique a pasta selecionada")
                    if terminal:
                        with self._lock:
                            state.status, state.error = terminal, failure
                            state.file_ids = []
                            self._outputs.pop(key, None)

            try:
                self.queue.adicionar_tarefa(task, key)
            except Exception:
                del self._states[key]
                if request is not None and request.request_id:
                    self._requests.pop(request.request_id, None)
                raise
            return self.snapshot(key)

    def _check_cancel(self, job):
        if self._closed or job.cancel_event.is_set():
            raise ProcessoCanceladoError()

    def snapshot(self, key):
        with self._lock:
            if key not in self._states:
                raise ApiError("job_not_found", "Trabalho não encontrado", 404)
            return self._states[key].model_copy(deep=True)

    def cancel(self, key):
        with self._lock:
            state = self.snapshot(key)
            if state.status in {"queued", "running", "cancelling"}:
                self.queue.cancelar_job(key)
                self._states[key].status = "cancelled" if state.status == "queued" else "cancelling"
            return self.snapshot(key)

    def result_directory(self, key):
        """Só uma saída concluída pode ser aberta pelo shell, por ID de job."""
        with self._lock:
            if self.snapshot(key).status != "completed" or key not in self._outputs:
                raise ApiError("result_unavailable", "Resultado ainda não disponível", 409)
            return self.selections.resolve(self._outputs[key], "directory")

    def read_file(self, key, limite_bytes=20 * 1024 * 1024):
        """Lê um PDF de seleção válida para pré-visualização (sem caminho)."""
        try:
            path = self.selections.resolve(key, "file")
        except SelectionError:
            raise ApiError("file_not_found", "Arquivo não encontrado", 404) from None
        if path.suffix.lower() != ".pdf":
            raise ApiError("unsupported_preview", "Pré-visualização só para PDF", 415)
        try:
            if path.stat().st_size > limite_bytes:
                raise ApiError("file_too_large", "Arquivo grande demais para visualizar", 413)
            return path.read_bytes()
        except OSError:
            raise ApiError("file_not_found", "Arquivo não encontrado", 404) from None

    def close(self):
        with self._lock:
            self._closed = True
        complete = self.queue.encerrar()
        self.selections.close()
        if not complete:
            raise RuntimeError("Operação local ainda está encerrando")
        with self._lock:
            for state in self._states.values():
                if state.status in {"queued", "running", "cancelling"}:
                    state.status = "cancelled"
            self.profiles.clear()
