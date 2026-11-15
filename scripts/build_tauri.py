"""Build de release do Contracto sobre o shell Tauri (ADR 0029).

Sincroniza a versão (VERSION -> tauri.conf.json/Cargo.toml), gera o sidecar, roda o bundler NSIS e
entrega em dist/: instalador, ZIP portátil, SHA-256 e o `latest.json` do atualizador, arquivando as versões antigas.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TAURI = RAIZ / "src-tauri"
DIST = RAIZ / "dist"
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "app"))


def sincronizar_versao(versao: str) -> None:
    conf = TAURI / "tauri.conf.json"
    texto = re.sub(r'("version":\s*")[^"]+', rf"\g<1>{versao}", conf.read_text(encoding="utf-8"), count=1)
    conf.write_text(texto, encoding="utf-8")
    cargo = TAURI / "Cargo.toml"
    cargo.write_text(re.sub(r'(?m)^version = "[^"]+"', f'version = "{versao}"', cargo.read_text(encoding="utf-8"), count=1),
                     encoding="utf-8")


def executar(*comando: str, cwd: Path = RAIZ) -> None:
    # Rust fica fora do PATH logo depois do rustup; npx.cmd só existe como .cmd no Windows.
    ambiente = {**os.environ, "PATH": os.environ["PATH"] + os.pathsep + str(Path.home() / ".cargo" / "bin")}
    if subprocess.run(comando, cwd=cwd, env=ambiente, shell=sys.platform == "win32").returncode:
        sys.exit(f"[ERRO] Falhou: {' '.join(comando)}")


def sha256(arquivo: Path) -> None:
    with arquivo.open("rb") as f:
        h = hashlib.file_digest(f, "sha256").hexdigest().upper()
    Path(str(arquivo) + ".sha256.txt").write_text(f"SHA256  {h}  {arquivo.name}\n", encoding="utf-8")


CHAVE_PADRAO = Path.home() / ".tauri" / "contracto-updater.key"
REPOSITORIO = "https://github.com/Nickolas-Costa/Contracto"


def manifesto(versao: str, assinatura: str, quando: datetime) -> dict:
    """`latest.json` lido pelo atualizador do app (ADR 0032): versão, assinatura minisign e onde baixar."""
    return {
        "version": versao,
        "notes": f"Novidades da versão {versao}: {REPOSITORIO}/releases/tag/{versao}",
        "pub_date": quando.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platforms": {"windows-x86_64": {
            "signature": assinatura.strip(),
            "url": f"{REPOSITORIO}/releases/download/{versao}/Contracto_Setup_v{versao}.exe",
        }},
    }


def main() -> None:
    from archive_dist import arquivar
    import build_sidecar
    import version

    versao = version.__version__
    if json.loads((RAIZ / "package.json").read_text(encoding="utf-8")).get("name") != "contracto-shell":
        sys.exit("[ERRO] package.json inesperado.")
    # A chave privada nunca entra no repositório: vem do ambiente ou do arquivo padrão do usuário.
    if not os.environ.get("TAURI_SIGNING_PRIVATE_KEY"):
        if not CHAVE_PADRAO.is_file():
            sys.exit(f"[ERRO] Chave de assinatura das atualizações ausente: defina TAURI_SIGNING_PRIVATE_KEY ou restaure {CHAVE_PADRAO}.")
        os.environ["TAURI_SIGNING_PRIVATE_KEY"] = CHAVE_PADRAO.read_text(encoding="utf-8").strip()
        os.environ.setdefault("TAURI_SIGNING_PRIVATE_KEY_PASSWORD", "")
    sincronizar_versao(versao)
    build_sidecar.main()
    executar("npm", "ci")
    executar("npx", "tauri", "build")

    liberacao = TAURI / "target" / "release"
    instalador = next((liberacao / "bundle" / "nsis").glob(f"*_{versao}_x64-setup.exe"), None)
    if instalador is None:
        sys.exit("[ERRO] O bundler não gerou o instalador NSIS.")
    DIST.mkdir(exist_ok=True)
    arquivar(versao, DIST)
    destino = DIST / f"Contracto_Setup_v{versao}.exe"
    shutil.copy2(instalador, destino)
    pacote = DIST / f"Contracto_v{versao}.zip"
    with zipfile.ZipFile(pacote, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(liberacao / "contracto.exe", f"Contracto_v{versao}/Contracto.exe")
        for arquivo in (TAURI / "binaries" / "sidecar").rglob("*"):
            if arquivo.is_file():
                z.write(arquivo, f"Contracto_v{versao}/sidecar/{arquivo.relative_to(TAURI / 'binaries' / 'sidecar').as_posix()}")
    sha256(destino)
    sha256(pacote)
    assinatura = Path(str(instalador) + ".sig")
    if not assinatura.is_file():
        sys.exit("[ERRO] O bundler não gerou a assinatura (.sig) do instalador.")
    (DIST / "latest.json").write_text(
        json.dumps(manifesto(versao, assinatura.read_text(encoding="utf-8"), datetime.now(timezone.utc)), indent=2), encoding="utf-8")
    print(f"\n[OK] {destino.name} ({destino.stat().st_size / 2**20:.1f} MiB)\n[OK] {pacote.name} ({pacote.stat().st_size / 2**20:.1f} MiB)")


if __name__ == "__main__":
    main()
