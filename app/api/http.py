"""FastAPI protegida por middleware ASGI antes da leitura/validação do corpo."""
import asyncio
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response

from utils.logger import contexto_log_api
from version import __version__
from .jobs import ApiError, capabilities
from .models import ComposeInput, EmptyInput, GenerateInput, JobState, ProcessInput
from .selections import SelectionError


def error(code, message, status, issues=None):
    payload = {"code": code, "message": message}
    if issues:
        payload["issues"] = issues
    return JSONResponse(payload, status_code=status)


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
        elif scope["method"] not in {"GET", "POST"}:
            response = error("invalid_method", "Método não permitido", 405)
        elif scope["method"] == "POST" and headers.get(b"content-type", "").split(";", 1)[0] != "application/json":
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

    @app.post("/api/v1/profiles/compose")
    def compose(request: ComposeInput):
        return session.jobs.compose(request)

    @app.post("/api/v1/jobs/generate", response_model=JobState, status_code=202)
    def generate(request: GenerateInput):
        return session.jobs.generate(request)

    @app.post("/api/v1/jobs/process", response_model=JobState, status_code=202)
    def process(request: ProcessInput):
        return session.jobs.process(request)

    @app.get("/api/v1/jobs/{job_id}", response_model=JobState)
    def state(job_id: str):
        return session.jobs.snapshot(job_id)

    @app.get("/api/v1/files/{file_id}")
    def read_file(file_id: str):
        return Response(session.jobs.read_file(file_id), media_type="application/pdf")

    @app.post("/api/v1/jobs/{job_id}/cancel", response_model=JobState)
    def cancel(job_id: str, request: EmptyInput):
        return session.jobs.cancel(job_id)

    return app
