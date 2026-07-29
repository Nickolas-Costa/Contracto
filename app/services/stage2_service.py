"""
Serviço de orquestração da Etapa 2 (Organização e PDF/A).

Recebe os documentos gerados na Etapa 1 e os documentos externos selecionados,
cria a estrutura de pastas padronizada e orquestra a conversão em lote
para PDF/A-2b, renomeando os arquivos conforme a padronização.
"""

from pathlib import Path
from typing import TypedDict

from models.participant import Participant
from services.pdfa_converter import ResultadoLote, converter_lote
from utils.ghostscript_setup import esta_disponivel
from services.process_folder_service import criar_estrutura_pastas
from utils.filename_utils import nome_documento_processo


class ResultadoEtapa2(TypedDict):
    sucesso: bool
    pasta_pdfa: Path
    resultado_lote: ResultadoLote
    mensagem: str


def executar_etapa2(
    pasta_base: Path,
    participantes: list[Participant],
    arquivos_gerados_etapa1: list[Path],
    documentos_externos: dict[str, Path],
) -> ResultadoEtapa2:
    """
    Executa a segunda etapa do processo:
    1. Verifica disponibilidade do Ghostscript.
    2. Cria a estrutura de pastas (PDF-A/ASSINADOS/REGISTRADOS).
    3. Prepara a lista de conversão com os nomes padronizados.
    4. Executa a conversão em lote para PDF/A-2b.
    5. Remove os arquivos originais da Etapa 1 em caso de sucesso (limpeza).
    """
    if not esta_disponivel():
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_base,
            "resultado_lote": ResultadoLote(),
            "mensagem": (
                "Ghostscript não encontrado no sistema.\n\n"
                "Para gerar documentos em conformidade com PDF/A, é necessário instalar "
                "o Ghostscript.\nFaça o download em: https://ghostscript.com/releases/gsdnld.html"
            ),
        }

    # 1. Criar estrutura de pastas
    try:
        pasta_pdfa = criar_estrutura_pastas(pasta_base)
    except Exception as exc:
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_base,
            "resultado_lote": ResultadoLote(),
            "mensagem": f"Erro ao criar estrutura de pastas:\n{exc}",
        }

    lote_conversao: list[tuple[Path, Path]] = []

    # 2. Preparar arquivos da Etapa 1 (já têm o nome correto individual)
    for arquivo_gerado in arquivos_gerados_etapa1:
        if arquivo_gerado.exists():
            caminho_saida = pasta_pdfa / arquivo_gerado.name
            lote_conversao.append((arquivo_gerado, caminho_saida))

    from services.rtf_converter import converter_rtf_para_pdf
    import tempfile
    
    # 3. Preparar documentos externos selecionados
    arquivos_temporarios_rtf = []
    for tipo_documento, caminho_origem in documentos_externos.items():
        if caminho_origem.exists():
            nome_padronizado = nome_documento_processo(tipo_documento, participantes)
            caminho_saida = pasta_pdfa / nome_padronizado
            
            caminho_para_gs = caminho_origem
            # Se for RTF, converter primeiro para PDF num local temporário
            if caminho_origem.suffix.lower() == ".rtf":
                caminho_tmp = Path(tempfile.gettempdir()) / f"temp_{nome_padronizado}"
                try:
                    converter_rtf_para_pdf(caminho_origem, caminho_tmp)
                    caminho_para_gs = caminho_tmp
                    arquivos_temporarios_rtf.append(caminho_tmp)
                except Exception as exc:
                    return {
                        "sucesso": False,
                        "pasta_pdfa": pasta_pdfa,
                        "resultado_lote": ResultadoLote(),
                        "mensagem": f"Erro ao converter RTF para PDF: {exc}",
                    }

            lote_conversao.append((caminho_para_gs, caminho_saida))

    if not lote_conversao:
        return {
            "sucesso": True,
            "pasta_pdfa": pasta_pdfa,
            "resultado_lote": ResultadoLote(),
            "mensagem": "Nenhum arquivo para processar.",
        }

    # 4. Converter tudo para PDF/A
    resultado_lote = converter_lote(lote_conversao, "PDF/A-2b")
    
    # Limpar os RTFs convertidos temporariamente
    for tmp_file in arquivos_temporarios_rtf:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError:
                pass

    # Se teve sucessos, limpar os arquivos da Etapa 1 que foram convertidos
    if resultado_lote.convertidos:
        _limpar_arquivos_originais_etapa1(arquivos_gerados_etapa1, resultado_lote)

    if resultado_lote.erros:
        mensagem = f"Conversão finalizada com {len(resultado_lote.erros)} erro(s)."
        sucesso = False
    else:
        mensagem = f"{len(resultado_lote.convertidos)} documento(s) convertido(s) para PDF/A-2b com sucesso!"
        sucesso = True

    return {
        "sucesso": sucesso,
        "pasta_pdfa": pasta_pdfa,
        "resultado_lote": resultado_lote,
        "mensagem": mensagem,
    }


def _limpar_arquivos_originais_etapa1(originais: list[Path], resultado: ResultadoLote) -> None:
    """Remove os PDFs gerados temporariamente na Etapa 1, se convertidos com sucesso."""
    # Lista de nomes de arquivos que foram gerados/convertidos com sucesso na pasta PDF-A
    nomes_sucesso = {r.caminho_saida.name for r in resultado.convertidos}

    for arquivo in originais:
        if arquivo.name in nomes_sucesso and arquivo.exists():
            try:
                arquivo.unlink()
            except OSError:
                pass
