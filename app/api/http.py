"""FastAPI protegida por middleware ASGI antes da leitura/validação do corpo."""
import asyncio
import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from utils.logger import contexto_log_api
from version import __version__
from .jobs import ApiError, capabilities
from .models import ComposeInput, ConvertInput, EmptyInput, GenerateInput, JobState, ProcessInput, PreviewInput
from .selections import SelectionError


def error(code, message, status, issues=None):
    payload = {"code": code, "message": message}
    if issues:
        payload["issues"] = issues
    return JSONResponse(payload, status_code=status)


def _perfis(operacao):
    """Erro de perfil vira 422 com o motivo, em vez do 500 genérico que a tela não sabe explicar."""
    try:
        return operacao()
    except ValueError as exc:  # mensagens do profile_manager: nome repetido, tipo de campo, etc.
        raise ApiError("invalid_profile", str(exc), 422) from None
    except (TypeError, KeyError, AttributeError):  # JSON com chave ou tipo que o perfil não tem
        raise ApiError("invalid_profile", "Perfil inválido: confira as chaves e os tipos do JSON", 422) from None


_APELIDOS = {"name": "nome", "mode": "modo_fluxo", "max_participants": "max_participantes", "fields": "campos_entrada"}


def _mesclar_edicao(atual: dict, dados: dict) -> dict:
    """Junta o que a tela Perfis enviou (`dados`) ao perfil salvo (`atual`, formato de `asdict(Perfil)`).

    A tela edita a entrada do catálogo, que não tem `mapeamento`, `caminho` nem `identificador`
    e usa apelidos. O que a tela não conhece fica como está no perfil salvo.
    """
    final = dict(atual)
    for chave, valor in dados.items():
        chave = _APELIDOS.get(chave, chave)
        if chave in ("profile_id", "identificador"):
            continue  # o identificador nunca vem da tela: trocá-lo duplicaria um perfil de fábrica
        if chave not in atual:
            raise ValueError(f"Chave desconhecida no perfil: '{chave}'.")
        if chave == "formularios":
            # O catálogo só traz nome e geração: caminho e mapeamento vêm do formulário salvo (por nome, depois por posição).
            salvos = atual["formularios"]
            por_nome = {f["nome"]: f for f in salvos}
            valor = [{**(por_nome.get(f.get("nome")) or (salvos[i] if i < len(salvos) else {})), **f}
                     for i, f in enumerate(valor)]
        final[chave] = valor
    return final


class LocalOnly:
    def __init__(self, app, session):
        self.app, self.session = app, session

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {}
        duplicate = False
        for key, value in scope["headers"]:
            key = key.lower()
            if key in headers:
                duplicate = True
            headers[key] = value.decode("latin1")
        session = self.session
        response = None
        if session.closed:
            response = error("closed", "Sessão encerrada", 503)
        elif duplicate or scope.get("client", (None,))[0] != "127.0.0.1" or headers.get(b"host") != session.authority:
            response = error("invalid_host", "Requisição local inválida", 403)
        elif headers.get(b"origin") != session.origin:
            response = error("invalid_origin", "Origem não autorizada", 403)
        elif not secrets.compare_digest(headers.get(b"authorization", "").encode(), f"Bearer {session.token}".encode()):
            response = error("unauthorized", "Autenticação necessária", 401)
        elif scope.get("query_string"):
            response = error("invalid_query", "Parâmetros de URL não são aceitos", 400)
        elif scope["method"] not in {"GET", "POST", "PUT", "DELETE"}:
            response = error("invalid_method", "Método não permitido", 405)
        elif scope["method"] in {"POST", "PUT"} and headers.get(b"content-type", "").split(";", 1)[0] != "application/json":
            response = error("invalid_content_type", "Envie JSON", 415)
        if response is not None:
            await response(scope, receive, send)
            return
        body = bytearray()
        try:
            while True:
                message = await asyncio.wait_for(receive(), timeout=5)
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 1024 * 1024:
                    await error("body_too_large", "Corpo excede 1 MiB", 413)(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
        except TimeoutError:
            await error("request_timeout", "Envio não concluído", 408)(scope, receive, send)
            return
        if scope["method"] == "GET" and body:
            await error("unexpected_body", "GET não aceita corpo", 400)(scope, receive, send)
            return

        async def replay():
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] += [(b"cache-control", b"no-store"),
                                       (b"x-content-type-options", b"nosniff")]
            await send(message)

        with contexto_log_api():
            await self.app(scope, replay, private_send)


def create_app(session):
    @asynccontextmanager
    async def lifespan(_app):
        try:
            yield
        finally:
            session.invalidate()
            try:
                await asyncio.to_thread(session.jobs.close)
            except Exception:
                session.shutdown_failed = True
                raise

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(LocalOnly, session=session)

    @app.exception_handler(ApiError)
    async def api_error(_request, exc):
        return error(exc.code, exc.message, exc.status, exc.issues)

    @app.exception_handler(SelectionError)
    async def selection_error(_request, _exc):
        return error("invalid_selection", "Seleção inválida ou expirada; selecione novamente", 422)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _exc):
        # O erro padrão do Pydantic inclui o input (CPF, conteúdo e caminhos).
        return error("invalid_request", "Confira o formato e os campos da requisição", 422)

    @app.exception_handler(HTTPException)
    async def route_error(_request, exc):
        return error("invalid_route", "Rota ou método não disponível", exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected(_request, _exc):
        return error("internal_error", "Operação local indisponível", 500)

    @app.get("/api/v1/health")
    def health():
        return {"version": __version__, "status": "ready"}

    @app.get("/api/v1/capabilities")
    def get_capabilities():
        return capabilities()

    @app.get("/api/v1/profiles")
    def catalog():
        return session.jobs.catalog()

    @app.post("/api/v1/profiles")
    def create_profile(dados: dict):
        from utils import profile_manager
        def criar():
            # Mesmo tratamento da edição: o JSON copiado da tela usa os apelidos do catálogo.
            perfil = profile_manager._perfil_de_dict(_mesclar_edicao(asdict(profile_manager.Perfil(nome="")), dados))
            profile_manager.adicionar_perfil(perfil)
            return perfil
        perfil = _perfis(criar)
        session.jobs.refresh_profiles()
        return {"status": "created", "nome": perfil.nome}

    @app.put("/api/v1/profiles/{nome}")
    def update_profile(nome: str, dados: dict):
        from utils import profile_manager
        def atualizar():
            atual = profile_manager.obter_perfil(nome)
            if atual is None:
                raise ValueError(f"Perfil '{nome}' não encontrado.")
            perfil = profile_manager._perfil_de_dict(_mesclar_edicao(asdict(atual), dados))
            profile_manager.atualizar_perfil(nome, perfil)
            return perfil
        perfil_novo = _perfis(atualizar)
        session.jobs.refresh_profiles()
        return {"status": "updated", "nome": perfil_novo.nome}

    @app.delete("/api/v1/profiles/{nome}")
    def delete_profile(nome: str):
        from utils import profile_manager
        _perfis(lambda: profile_manager.excluir_perfil(nome))
        session.jobs.refresh_profiles()
        return {"status": "deleted", "nome": nome}

    @app.post("/api/v1/profiles/{nome}/duplicate")
    def duplicate_profile(nome: str, payload: dict = {}):
        from utils import profile_manager
        novo_nome = payload.get("novo_nome")
        novo = _perfis(lambda: profile_manager.duplicar_perfil(nome, novo_nome))
        session.jobs.refresh_profiles()
        return {"status": "duplicated", "nome": novo.nome}

    @app.post("/api/v1/profiles/compose")
    def compose(request: ComposeInput):
        return session.jobs.compose(request)

    @app.post("/api/v1/profiles/preview")
    def preview(request: PreviewInput):
        return session.jobs.preview(request)

    @app.post("/api/v1/jobs/generate", response_model=JobState, status_code=202)
    def generate(request: GenerateInput):
        return session.jobs.generate(request)

    @app.post("/api/v1/jobs/process", response_model=JobState, status_code=202)
    def process(request: ProcessInput):
        return session.jobs.process(request)

    @app.post("/api/v1/jobs/convert", response_model=JobState, status_code=202)
    def convert(request: ConvertInput):
        return session.jobs.convert(request)

    @app.get("/api/v1/jobs", response_model=list[JobState])
    def list_jobs():
        return session.jobs.list_jobs()

    @app.get("/api/v1/jobs/{job_id}", response_model=JobState)
    def state(job_id: str):
        return session.jobs.snapshot(job_id)

    @app.get("/api/v1/files/{file_id}")
    def read_file(file_id: str):
        return Response(session.jobs.read_file(file_id), media_type="application/pdf")

    @app.post("/api/v1/jobs/{job_id}/cancel", response_model=JobState)
    def cancel(job_id: str, request: EmptyInput):
        return session.jobs.cancel(job_id)

    @app.get("/api/v1/settings")
    def get_settings():
        from utils import config_manager
        return config_manager.carregar_config(forcar_disco=True)

    @app.post("/api/v1/settings")
    def update_settings(dados: dict):
        from utils import config_manager
        normalizados = dict(dados or {})
        # Frontend usa "sistema"; canônico no disco é "system" (legado) —
        # ambos resolvem para o tema do SO. Normaliza sem rejeitar.
        if normalizados.get("aparencia") == "sistema":
            normalizados["aparencia"] = "system"
        config = config_manager.carregar_config()
        ignoradas = [k for k in normalizados if k not in config_manager._DEFAULTS]
        config.update({k: v for k, v in normalizados.items() if k in config_manager._DEFAULTS})
        config_manager.salvar_config(config)
        if ignoradas:
            config["_ignoradas"] = sorted(ignoradas)
        return config

    @app.post("/api/v1/system/repair")
    def system_repair():
        from services.system_repair_service import executar_diagnostico_e_reparo
        try:
            resultado = executar_diagnostico_e_reparo()
        except Exception:
            return {"status": "error", "message": "Falha ao executar reparo do sistema."}
        return {"status": "success" if resultado.sucesso else "warning", "message": resultado.titulo}

    @app.post("/api/v1/settings/restore")
    def restore_settings():
        from utils import config_manager
        return config_manager.restaurar_padroes()

    @app.post("/api/v1/profiles/active")
    def activate_profile(dados: dict):
        from utils import config_manager, profile_manager
        nome = (dados or {}).get("nome", "")
        if not isinstance(nome, str) or not nome.strip():
            return error("invalid_request", "Informe o nome do perfil", 422)
        perfil = profile_manager.obter_perfil(nome.strip())
        if perfil is None:
            return error("unknown_profile", "Perfil não encontrado", 404)
        config_manager.definir("perfil_ativo", perfil.nome)
        return {"status": "activated", "nome": perfil.nome}

    @app.post("/api/v1/system/backup")
    def system_backup():
        from utils import backup as backup_util
        pacote = backup_util.criar_backup()
        return {"status": "created", "name": pacote.name}

    @app.post("/api/v1/system/restore")
    def system_restore(dados: dict):
        from utils import backup as backup_util
        selection_id = (dados or {}).get("selection_id", "")
        try:
            caminho = session.jobs.selections.resolve(selection_id, kind="backup")
        except Exception:
            raise SelectionError()
        if caminho.suffix.lower() != ".zip":
            return error("invalid_request", "Selecione um backup .zip válido", 422)
        try:
            backup_util.restaurar_backup(caminho)
        except ValueError as exc:
            return error("invalid_backup", str(exc), 422)
        session.jobs.refresh_profiles()  # sem isto a tela seguia com os perfis de antes da restauração
        return {"status": "restored"}

    return app
