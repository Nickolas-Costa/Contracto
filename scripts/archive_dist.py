"""Arquiva artefatos de versões antigas de dist/ em dist/_versoes_anteriores/.

Uso:
    python scripts/archive_dist.py [<versao_atual>]

- Move apenas arquivos da RAIZ de dist/ que casem com os padrões versionados
  e cuja versão seja diferente da atual.
- Idempotente: sem arquivos velhos, não faz nada (não cria pasta vazia).
- Nunca move a própria pasta destino nem dirs temporários Contracto_v*/.
- Sem sobrescrita silenciosa: mesmo tamanho pula; tamanho difere sufixa timestamp.
- Falha explícita (exit 1) em PermissionError — sem fallback silencioso.
"""
import re
import shutil
import sys
import time
from pathlib import Path

ARQUIVO_NOME = "_versoes_anteriores"
PADROES = ("Contracto_v*.exe", "Contracto_v*.zip", "*.sha256.txt", "Contracto_Installer_v*.exe")
VERSAO_RE = re.compile(r"v(\d+\.\d+\.\d+)")


def versao_de(nome: str) -> str | None:
    m = VERSAO_RE.search(nome)
    return m.group(1) if m else None


def versao_atual() -> str:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip().lstrip("v")
    projeto = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(projeto / "app"))
    import version
    return str(version.__version__).strip().lstrip("v")


def arquivar(versao: str, dist: Path | None = None) -> int:
    dist = dist or (Path(__file__).resolve().parent.parent / "dist")
    destino = dist / ARQUIVO_NOME
    if not dist.is_dir():
        return 0
    candidatos: list[Path] = []
    for padrao in PADROES:
        for p in dist.glob(padrao):
            if not p.is_file():
                continue
            # Nunca tocar no que já está arquivado.
            try:
                p.relative_to(destino)
                continue
            except ValueError:
                pass
            v = versao_de(p.name)
            if v is None or v == versao:
                continue
            candidatos.append(p)
    # Deduplicar (zip + sha sobrepõem globs).
    candidatos = sorted({c.resolve(): c for c in candidatos}.values(), key=lambda p: p.name)
    if not candidatos:
        return 0
    destino.mkdir(parents=True, exist_ok=True)
    movidos = 0
    for origem in candidatos:
        alvo = destino / origem.name
        if alvo.exists():
            try:
                if alvo.stat().st_size == origem.stat().st_size:
                    print(f"[INFO] Já arquivado (mesmo tamanho), mantendo: {origem.name}")
                    origem.unlink()
                    movidos += 1
                    continue
            except OSError:
                pass
            sufixo = time.strftime("%Y%m%d-%H%M%S")
            alvo = destino / f"{origem.name}.{sufixo}"
            print(f"[AVISO] Colisão no arquivo; renomeando para: {alvo.name}")
        try:
            shutil.move(str(origem), str(alvo))
            print(f"[OK] Arquivado: {origem.name} -> {ARQUIVO_NOME}/{alvo.name}")
            movidos += 1
        except PermissionError as exc:
            print(f"[ERRO] Sem permissão para mover {origem.name}: {exc}")
            print("       Feche o Explorer/antivírus e rode novamente. Nada foi apagado.")
            raise SystemExit(1)
        except OSError as exc:
            print(f"[ERRO] Falha ao mover {origem.name}: {exc}")
            raise SystemExit(1)
    # Aviso de retenção (cada versão ~145 MB).
    try:
        total = sum(p.stat().st_size for p in destino.rglob("*") if p.is_file())
        gb = total / (1024 ** 3)
        print(f"[INFO] Arquivo total: {gb:.2f} GB em {destino}")
        if total > 2 * 1024 ** 3:
            print("[AVISO] Arquivo acima de 2 GB — considere apagar versões muito antigas.")
    except OSError:
        pass
    return movidos


def main() -> None:
    versao = versao_atual()
    n = arquivar(versao)
    if n:
        print(f"[OK] {n} arquivo(s) de versões antigas movidos para dist/{ARQUIVO_NOME}/ (versão atual v{versao} mantida na raiz).")
    else:
        print(f"[INFO] Nada a arquivar (raiz só tem v{versao} ou está vazia).")


if __name__ == "__main__":
    main()
