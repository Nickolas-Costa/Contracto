"""Importação/exportação de perfis por arquivo, depois que o shell nativo escolheu o caminho."""
import json
from dataclasses import asdict
from pathlib import Path


def importar_arquivo(server, path: Path):
    if path.suffix.lower() != ".json" or path.stat().st_size > 1024 * 1024:
        return {"ok": False, "code": "invalid_file"}
    try:
        dados = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"ok": False, "code": "invalid_json"}
    if not isinstance(dados, dict):
        return {"ok": False, "code": "invalid_profile"}
    from utils import profile_manager
    try:
        perfil = profile_manager._perfil_de_dict(dados)
        profile_manager.adicionar_perfil(perfil)
    except (ValueError, TypeError, KeyError) as exc:
        return {"ok": False, "code": "invalid_profile", "message": str(exc)}
    server.jobs.refresh_profiles()
    return {"ok": True, "nome": perfil.nome}


def exportar_arquivo(nome: str, path: Path):
    from utils import profile_manager
    perfil = next((p for p in profile_manager.carregar_perfis() if p.nome == nome), None)
    if perfil is None:
        return {"ok": False, "code": "profile_not_found"}
    path.write_text(json.dumps(asdict(perfil), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "nome": perfil.nome}
