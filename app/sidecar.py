"""Sidecar headless do Contracto para o shell Tauri (ADR 0029).

Sobe a mesma API loopback (`server.LocalServer`) sem janela. Quem o inicia é o
processo pai (Tauri/Rust), que é o único a falar com ele:

- stdout: uma linha JSON por mensagem. A primeira é o aperto de mão
  `{"event": "ready", "origin": ..., "token": ..., "version": ...}`; depois, as
  respostas aos comandos `{"id": ..., "ok": ..., ...}`.
- stdin (canal de controle, inacessível à página): comandos em JSON, um por linha.
    register    {"id", "cmd": "register", "kind": "file|directory|convert|backup", "path"}
                -> {"selection_id", "name"}   (o shell nativo autoriza o caminho que o
                usuário escolheu num diálogo; a página só recebe o ID)
    result_dir  {"id", "cmd": "result_dir", "job_id"}   -> {"path"}  (shell abre a pasta)
    file_path   {"id", "cmd": "file_path", "file_id"}   -> {"path"}  (leitor padrão)
    shutdown    {"cmd": "shutdown"}
- EOF em stdin (pai encerrou) fecha o servidor e sai.

O token trafega só por este pipe: nunca é gravado em log nem exposto à página.
"""
import json
import sys
from pathlib import Path

from version import __version__


def _responder(saida, **dados):
    saida.write(json.dumps(dados, ensure_ascii=False) + "\n")
    saida.flush()


def _executar(server, comando):
    """Executa um comando validado; devolve os campos extras da resposta."""
    nome = comando.get("cmd")
    if nome == "register":
        caminho, tipo = comando.get("path"), comando.get("kind")
        if not isinstance(caminho, str) or not caminho or not isinstance(tipo, str):
            raise ValueError("invalid_request")
        selecionado = Path(caminho)
        return {"selection_id": server.jobs.selections.register(selecionado, tipo), "name": selecionado.name}
    if nome == "result_dir":
        return {"path": str(server.jobs.result_directory(_texto(comando, "job_id")))}
    if nome == "file_path":
        return {"path": str(server.jobs.selections.resolve(_texto(comando, "file_id"), "file"))}
    raise ValueError("unknown_command")


def _texto(comando, chave):
    valor = comando.get(chave)
    if not isinstance(valor, str) or not valor:
        raise ValueError("invalid_request")
    return valor


def servir(server, entrada, saida):
    """Laço de controle: lê comandos até EOF ou `shutdown`."""
    _responder(saida, event="ready", origin=server.origin, token=server.token, version=__version__)
    for linha in entrada:
        if not linha.strip():
            continue
        try:
            comando = json.loads(linha)
            if not isinstance(comando, dict):
                raise ValueError("invalid_request")
        except ValueError:
            _responder(saida, ok=False, code="invalid_request")
            continue
        if comando.get("cmd") == "shutdown":
            return
        try:
            _responder(saida, id=comando.get("id"), ok=True, **_executar(server, comando))
        except Exception as erro:  # a resposta não leva caminho nem dado do usuário
            codigo = str(erro) if str(erro) in {"invalid_request", "unknown_command"} else "failed"
            _responder(saida, id=comando.get("id"), ok=False, code=codigo)


def main(entrada=None, saida=None):
    from server import LocalServer

    with LocalServer() as server:
        servir(server, entrada or sys.stdin, saida or sys.stdout)


if __name__ == "__main__":
    main()
