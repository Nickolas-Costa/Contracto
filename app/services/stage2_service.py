"""
Serviço de orquestração da Etapa 2 (Organização e PDF/A).

Recebe os documentos gerados na Etapa 1 e os documentos externos selecionados,
cria a estrutura de pastas padronizada e orquestra a conversão em lote
para PDF/A-2b, renomeando os arquivos conforme a padronização.
"""

import threading
from pathlib import Path
from typing import Callable, Optional, TypedDict

from models.participant import Participant
from services.pdfa_converter import (
    ProcessoCanceladoError,
    ResultadoConversao,
    ResultadoLote,
    converter_lote,
)
from utils.ghostscript_setup import esta_disponivel
from services.process_folder_service import criar_estrutura_pastas
from utils.filename_utils import nome_documento_processo
from utils.logger import obter_logger


_logger = obter_logger("organizacao")


class ResultadoEtapa2(TypedDict):
    sucesso: bool
    pasta_pdfa: Path
    resultado_lote: ResultadoLote
    mensagem: str
    cancelado: bool


def executar_etapa2(
    pasta_base: Path,
    participantes: list[Participant],
    arquivos_gerados_etapa1: list[Path],
    documentos_externos: dict[str, Path],
    formato_saida: str = "PDF/A-2b",
    cancel_event: Optional[threading.Event] = None,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> ResultadoEtapa2:
    """
    Executa a segunda etapa do processo:
    1. Verifica disponibilidade do Ghostscript (se formato for PDF/A).
    2. Cria a estrutura de pastas (PDF-A/ASSINADOS/REGISTRADOS).
    3. Prepara a lista de conversão com os nomes padronizados.
    4. Executa a conversão em lote para PDF/A-2b ou copia os arquivos (modo PDF).
    5. Remove os arquivos originais da Etapa 1 em caso de sucesso (limpeza).
    """
    if cancel_event is not None and cancel_event.is_set():
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_base,
            "resultado_lote": ResultadoLote(),
            "mensagem": "Processo cancelado pelo usuário.",
            "cancelado": True,
        }

    usar_pdfa = formato_saida == "PDF/A-2b"

    if usar_pdfa and not esta_disponivel():
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_base,
            "resultado_lote": ResultadoLote(),
            "mensagem": (
                "Ghostscript não encontrado no sistema.\n\n"
                "Para gerar documentos em conformidade com PDF/A, é necessário instalar "
                "o Ghostscript.\nFaça o download em: https://ghostscript.com/releases/gsdnld.html"
            ),
            "cancelado": False,
        }

    # 1. Criar estrutura de pastas
    try:
        pasta_pdfa = criar_estrutura_pastas(pasta_base)
    except OSError as exc:
        _logger.error("Não foi possível criar a estrutura em '%s'.", pasta_base, exc_info=True)
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_base,
            "resultado_lote": ResultadoLote(),
            "mensagem": f"Erro ao criar estrutura de pastas:\n{exc}",
            "cancelado": False,
        }

    if cancel_event is not None and cancel_event.is_set():
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_pdfa,
            "resultado_lote": ResultadoLote(),
            "mensagem": "Processo cancelado pelo usuário.",
            "cancelado": True,
        }

    lote_conversao: list[tuple[Path, Path]] = []

    # 2. Preparar arquivos da Etapa 1 (já têm o nome correto individual)
    for arquivo_gerado in arquivos_gerados_etapa1:
        if arquivo_gerado.exists():
            caminho_saida = pasta_pdfa / arquivo_gerado.name
            lote_conversao.append((arquivo_gerado, caminho_saida))

    from services.rtf_converter import RtfConversionError, converter_rtf_para_pdf
    import tempfile
    
    # 3. Preparar documentos externos selecionados
    arquivos_temporarios_rtf = []
    try:
        for tipo_documento, caminho_origem in documentos_externos.items():
            if cancel_event is not None and cancel_event.is_set():
                raise ProcessoCanceladoError("Operação cancelada pelo usuário.")

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
                    except (OSError, RtfConversionError) as exc:
                        _logger.error("Falha ao converter o arquivo RTF '%s'.", caminho_origem, exc_info=True)
                        return {
                            "sucesso": False,
                            "pasta_pdfa": pasta_pdfa,
                            "resultado_lote": ResultadoLote(),
                            "mensagem": f"Erro ao converter RTF para PDF: {exc}",
                            "cancelado": False,
                        }

                lote_conversao.append((caminho_para_gs, caminho_saida))

        if not lote_conversao:
            return {
                "sucesso": True,
                "pasta_pdfa": pasta_pdfa,
                "resultado_lote": ResultadoLote(),
                "mensagem": "Nenhum arquivo para processar.",
                "cancelado": False,
            }

        # 4. Converter para PDF/A ou copiar (modo PDF)
        if usar_pdfa:
            resultado_lote = converter_lote(
                lote_conversao,
                "PDF/A-2b",
                cancel_event=cancel_event,
                on_file_progress=on_progress,
            )
        else:
            # Modo PDF: apenas copiar os arquivos para a pasta de destino
            import shutil
            resultado_lote = ResultadoLote()
            total_arqs = len(lote_conversao)
            for idx_arq, (origem, destino) in enumerate(lote_conversao, start=1):
                if cancel_event is not None and cancel_event.is_set():
                    raise ProcessoCanceladoError("Operação cancelada pelo usuário.")

                if on_progress:
                    on_progress(idx_arq, total_arqs, origem.name)

                try:
                    shutil.copy2(str(origem), str(destino))
                    resultado_lote.convertidos.append(
                        ResultadoConversao(caminho_saida=destino, perfil="PDF", validado=True)
                    )
                except OSError as exc:
                    _logger.error("Falha ao copiar '%s' para '%s'.", origem, destino, exc_info=True)
                    resultado_lote.erros.append(str(exc))

    except ProcessoCanceladoError:
        return {
            "sucesso": False,
            "pasta_pdfa": pasta_pdfa,
            "resultado_lote": ResultadoLote(),
            "mensagem": "Processo cancelado pelo usuário.",
            "cancelado": True,
        }
    finally:
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
        mensagem = f"Processo finalizado com {len(resultado_lote.erros)} erro(s)."
        sucesso = False
    else:
        formato_label = "PDF/A-2b" if usar_pdfa else "PDF"
        mensagem = f"{len(resultado_lote.convertidos)} documento(s) processado(s) em {formato_label} com sucesso!"
        sucesso = True

    return {
        "sucesso": sucesso,
        "pasta_pdfa": pasta_pdfa,
        "resultado_lote": resultado_lote,
        "mensagem": mensagem,
        "cancelado": False,
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
