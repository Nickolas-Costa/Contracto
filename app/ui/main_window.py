"""
Janela principal da aplicação.
"""

import os
import threading
import subprocess
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from models.participant import Participant
from services.generator_service import gerar_documentos, validar_antes_de_gerar
from services.pdf_service import PdfServiceError
from services.stage2_service import executar_etapa2
from ui.document_frame import DocumentFrame
from ui.participant_frame import ParticipantFrame
from ui.theme import *
from ui.loading_modal import LoadingModal
from ui.feedback_toast import show_toast
from utils.file_picker import selecionar_arquivo_pdf, selecionar_pasta
from utils.resource_path import modelo_padrao_ppe, modelo_padrao_primeiro_imovel


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        configure_appearance()

        self.title("Contrato — Preparação de Documentos")
        self.geometry("900x850")
        self.minsize(800, 700)
        self.configure(fg_color=COLOR_BACKGROUND)

        # =============================================================
        # Estado da Aplicação
        # =============================================================
        self.caminho_modelo_ppe: Path | None = modelo_padrao_ppe()
        self.caminho_modelo_primeiro_imovel: Path | None = modelo_padrao_primeiro_imovel()
        self.pasta_saida: Path | None = None
        self.participant_frames: list[ParticipantFrame] = []
        
        self.participantes_etapa1: list[Participant] = []
        self.arquivos_gerados_etapa1: list[Path] = []

        # =============================================================
        # Layout Principal
        # =============================================================
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_stepper()

        self.container_etapa1 = ctk.CTkFrame(self, fg_color="transparent")
        self.container_etapa1.grid(row=1, column=0, sticky="nsew")
        self.container_etapa1.grid_columnconfigure(0, weight=1)
        self.container_etapa1.grid_rowconfigure(0, weight=1)

        self.container_etapa2 = ctk.CTkFrame(self, fg_color="transparent")
        self.container_etapa2.grid_columnconfigure(0, weight=1)
        self.container_etapa2.grid_rowconfigure(2, weight=1)

        self._construir_etapa1()
        self._construir_etapa2()

        self._adicionar_participante(principal=True)
        self._atualizar_stepper(1)

    def _construir_stepper(self) -> None:
        self.frame_stepper = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0, border_width=0)
        self.frame_stepper.grid(row=0, column=0, sticky="ew")
        self.frame_stepper.grid_columnconfigure(0, weight=1)
        self.frame_stepper.grid_columnconfigure(2, weight=1)

        self.lbl_etapa1 = ctk.CTkLabel(self.frame_stepper, text="1. Geração de Documentos", font=get_font(FONT_SIZE_H3, "bold"))
        self.lbl_etapa1.grid(row=0, column=0, pady=SPACING_LARGE, sticky="e", padx=SPACING_LARGE)

        self.lbl_seta = ctk.CTkLabel(self.frame_stepper, text="→", font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED)
        self.lbl_seta.grid(row=0, column=1, pady=SPACING_LARGE)

        self.lbl_etapa2 = ctk.CTkLabel(self.frame_stepper, text="2. Conversão PDF/A", font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT_DISABLED)
        self.lbl_etapa2.grid(row=0, column=2, pady=SPACING_LARGE, sticky="w", padx=SPACING_LARGE)

    def _atualizar_stepper(self, etapa: int) -> None:
        if etapa == 1:
            self.lbl_etapa1.configure(text_color=COLOR_PRIMARY)
            self.lbl_etapa2.configure(text_color=COLOR_TEXT_DISABLED)
        else:
            self.lbl_etapa1.configure(text_color=COLOR_TEXT_DISABLED)
            self.lbl_etapa2.configure(text_color=COLOR_PRIMARY)

    # ------------------------------------------------------------------
    # ETAPA 1: Preenchimento e Geração
    # ------------------------------------------------------------------
    def _construir_etapa1(self) -> None:
        self._construir_secao_participantes()
        self._construir_secao_modelos()
        self._construir_secao_saida()
        
        self.botao_avancar = ctk.CTkButton(
            self.container_etapa1,
            text="GERAR DOCUMENTOS E AVANÇAR",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_avancar,
        )
        self.botao_avancar.grid(row=3, column=0, padx=SPACING_LARGE, pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")

    def _construir_secao_participantes(self) -> None:
        secao = ctk.CTkFrame(self.container_etapa1, fg_color="transparent")
        secao.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="nsew")
        secao.grid_columnconfigure(0, weight=1)
        secao.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(secao, text="Participantes", font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")

        self.participantes_scroll = ctk.CTkScrollableFrame(secao, fg_color="transparent", label_text="")
        self.participantes_scroll.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.participantes_scroll.grid_columnconfigure(0, weight=1)

        botao_adicionar = ctk.CTkButton(
            secao, text="+ Adicionar Participante", 
            fg_color=COLOR_SURFACE, text_color=COLOR_PRIMARY, border_width=1, border_color=COLOR_PRIMARY,
            hover_color=COLOR_SURFACE_VARIANT, corner_radius=RADIUS_BUTTON,
            command=self._adicionar_participante
        )
        botao_adicionar.grid(row=2, column=0, padx=0, pady=(SPACING_SMALL, 0), sticky="w")

    def _construir_secao_modelos(self) -> None:
        secao = ctk.CTkFrame(self.container_etapa1, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        secao.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(secao, text="Modelos Base", font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, columnspan=3, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_XSMALL), sticky="w")

        linha = 1
        if self.caminho_modelo_ppe and self.caminho_modelo_primeiro_imovel:
            aviso = ctk.CTkLabel(
                secao,
                text="✓ Modelos oficiais já carregados automaticamente.",
                font=get_font(FONT_SIZE_CAPTION),
                text_color=COLOR_SUCCESS,
            )
            aviso.grid(row=linha, column=0, columnspan=3, padx=SPACING_LARGE, pady=(0, SPACING_SMALL), sticky="w")
            linha += 1

        ctk.CTkLabel(secao, text="Modelo PPE:", font=get_font(FONT_SIZE_BODY)).grid(row=linha, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=SPACING_SMALL, sticky="w")
        self.entry_modelo_ppe = ctk.CTkEntry(secao, placeholder_text="Nenhum arquivo selecionado", corner_radius=RADIUS_INPUT)
        self.entry_modelo_ppe.grid(row=linha, column=1, padx=SPACING_SMALL, pady=SPACING_SMALL, sticky="ew")
        if self.caminho_modelo_ppe:
            self.entry_modelo_ppe.insert(0, str(self.caminho_modelo_ppe))
        self.entry_modelo_ppe.configure(state="disabled")
        
        ctk.CTkButton(secao, text="Selecionar", width=80, corner_radius=RADIUS_BUTTON, fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._selecionar_modelo_ppe).grid(row=linha, column=2, padx=(SPACING_SMALL, SPACING_LARGE), pady=SPACING_SMALL)
        linha += 1

        ctk.CTkLabel(secao, text="Modelo Primeiro Imóvel:", font=get_font(FONT_SIZE_BODY)).grid(row=linha, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=(SPACING_SMALL, SPACING_LARGE), sticky="w")
        self.entry_modelo_imovel = ctk.CTkEntry(secao, placeholder_text="Nenhum arquivo selecionado", corner_radius=RADIUS_INPUT)
        self.entry_modelo_imovel.grid(row=linha, column=1, padx=SPACING_SMALL, pady=(SPACING_SMALL, SPACING_LARGE), sticky="ew")
        if self.caminho_modelo_primeiro_imovel:
            self.entry_modelo_imovel.insert(0, str(self.caminho_modelo_primeiro_imovel))
        self.entry_modelo_imovel.configure(state="disabled")
        
        ctk.CTkButton(secao, text="Selecionar", width=80, corner_radius=RADIUS_BUTTON, fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._selecionar_modelo_primeiro_imovel).grid(row=linha, column=2, padx=(SPACING_SMALL, SPACING_LARGE), pady=(SPACING_SMALL, SPACING_LARGE))

    def _construir_secao_saida(self) -> None:
        secao = ctk.CTkFrame(self.container_etapa1, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD, border_width=1, border_color=COLOR_BORDER)
        secao.grid(row=2, column=0, padx=SPACING_LARGE, pady=SPACING_SMALL, sticky="ew")
        secao.grid_columnconfigure(1, weight=1)

        titulo = ctk.CTkLabel(secao, text="Destino", font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT)
        titulo.grid(row=0, column=0, columnspan=3, padx=SPACING_LARGE, pady=(SPACING_LARGE, SPACING_SMALL), sticky="w")

        ctk.CTkLabel(secao, text="Pasta de saída:", font=get_font(FONT_SIZE_BODY)).grid(row=1, column=0, padx=(SPACING_LARGE, SPACING_SMALL), pady=(0, SPACING_LARGE), sticky="w")
        self.entry_pasta_saida = ctk.CTkEntry(secao, placeholder_text="Nenhuma pasta selecionada", corner_radius=RADIUS_INPUT)
        self.entry_pasta_saida.grid(row=1, column=1, padx=SPACING_SMALL, pady=(0, SPACING_LARGE), sticky="ew")
        self.entry_pasta_saida.configure(state="disabled")
        
        ctk.CTkButton(secao, text="Selecionar", width=80, corner_radius=RADIUS_BUTTON, fg_color=COLOR_SURFACE_VARIANT, text_color=COLOR_TEXT, hover_color=COLOR_BORDER, command=self._selecionar_pasta_saida).grid(row=1, column=2, padx=(SPACING_SMALL, SPACING_LARGE), pady=(0, SPACING_LARGE))

    def _adicionar_participante(self, principal: bool = False) -> None:
        indice = len(self.participant_frames) + 1
        frame = ParticipantFrame(
            self.participantes_scroll,
            indice=indice,
            principal=principal,
            on_remover=None if principal else self._remover_participante,
        )
        frame.grid(row=indice - 1, column=0, padx=SPACING_XSMALL, pady=SPACING_SMALL, sticky="ew")
        self.participant_frames.append(frame)

    def _remover_participante(self, frame: ParticipantFrame) -> None:
        frame.destroy()
        self.participant_frames.remove(frame)
        for novo_indice, restante in enumerate(self.participant_frames, start=1):
            restante.atualizar_indice(novo_indice)

    def _verificar_permissao_escrita(self, pasta: Path) -> bool:
        if not pasta or not pasta.exists():
            return False
        try:
            teste_arq = pasta / ".teste_escrita"
            teste_arq.touch()
            teste_arq.unlink()
            return True
        except Exception:
            return False

    def _ao_clicar_avancar(self) -> None:
        principal = self.participant_frames[0].obter_participante()
        participantes = [principal]
        for frame in self.participant_frames[1:]:
            p = frame.obter_participante()
            p.copiar_dados_compartilhados(principal)
            participantes.append(p)

        erros = validar_antes_de_gerar(participantes, self.caminho_modelo_ppe, self.caminho_modelo_primeiro_imovel, self.pasta_saida)
        
        if not erros and self.pasta_saida and not self._verificar_permissao_escrita(self.pasta_saida):
            erros.append("Sem permissão de escrita na pasta de saída.")

        if erros:
            show_toast(self, "Corrija os campos obrigatórios.", "error")
            return

        self.botao_avancar.configure(state="disabled")
        self._loading = LoadingModal(self, "Gerando documentos...")
        
        thread = threading.Thread(target=self._gerar_em_background, args=(participantes,), daemon=True)
        thread.start()
        
    def _gerar_em_background(self, participantes):
        try:
            resultado = gerar_documentos(participantes, self.caminho_modelo_ppe, self.caminho_modelo_primeiro_imovel, self.pasta_saida)
            self.after(0, lambda: self._ao_concluir_geracao(resultado, participantes))
        except Exception as exc:
            self.after(0, lambda: self._ao_erro_geracao(exc))

    def _ao_concluir_geracao(self, resultado, participantes):
        if hasattr(self, '_loading'):
            self._loading.dismiss()
            
        self.participantes_etapa1 = participantes
        self.arquivos_gerados_etapa1 = resultado.arquivos_gerados
        
        if resultado.avisos:
            msg = " ".join(resultado.avisos)
            show_toast(self, f"Gerado com avisos: {msg}", "warning")
        else:
            show_toast(self, "Documentos gerados com sucesso!", "success")
            
        self.botao_avancar.configure(state="normal")
        self._mostrar_etapa2()

    def _ao_erro_geracao(self, exc):
        if hasattr(self, '_loading'):
            self._loading.dismiss()
        self.botao_avancar.configure(state="normal")
        show_toast(self, f"Erro: {str(exc)}", "error")

    # ------------------------------------------------------------------
    # ETAPA 2: Documentos da Gerente e PDF/A
    # ------------------------------------------------------------------
    def _construir_etapa2(self) -> None:
        frame_header = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_header.grid(row=0, column=0, padx=SPACING_LARGE, pady=(SPACING_LARGE, 0), sticky="ew")
        frame_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame_header, 
            text="Organização de Arquivos", 
            font=get_font(FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT
        ).grid(row=0, column=0, sticky="w", pady=(0, SPACING_SMALL))
        
        self.label_pasta_etapa2 = ctk.CTkLabel(frame_header, text="Pasta: ", font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT_SECONDARY)
        self.label_pasta_etapa2.grid(row=1, column=0, sticky="w")
        
        frame_docs = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_docs.grid(row=1, column=0, padx=SPACING_LARGE, pady=SPACING_LARGE, sticky="nsew")
        frame_docs.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            frame_docs, 
            text="Adicionar documentos extras (opcional)", 
            font=get_font(FONT_SIZE_H3, "bold"), text_color=COLOR_TEXT
        ).grid(row=0, column=0, padx=0, pady=(0, SPACING_SMALL), sticky="w")
        
        ctk.CTkLabel(
            frame_docs, 
            text="Arquivos selecionados aqui serão renomeados e convertidos para PDF/A.",
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            font=get_font(FONT_SIZE_BODY)
        ).grid(row=1, column=0, padx=0, pady=(0, SPACING_LARGE), sticky="w")

        self.document_frame = DocumentFrame(frame_docs)
        self.document_frame.grid(row=2, column=0, padx=0, pady=0, sticky="ew")

        frame_botoes = ctk.CTkFrame(self.container_etapa2, fg_color="transparent")
        frame_botoes.grid(row=3, column=0, padx=SPACING_LARGE, pady=(0, SPACING_LARGE), sticky="ew")
        frame_botoes.grid_columnconfigure(1, weight=1)
        
        self.botao_voltar = ctk.CTkButton(
            frame_botoes, 
            text="Voltar", 
            fg_color=COLOR_SURFACE,
            text_color=COLOR_TEXT,
            border_width=1,
            border_color=COLOR_BORDER,
            hover_color=COLOR_SURFACE_VARIANT,
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._mostrar_etapa1
        )
        self.botao_voltar.grid(row=0, column=0, padx=(0, SPACING_MEDIUM))
        
        self.botao_finalizar = ctk.CTkButton(
            frame_botoes,
            text="FINALIZAR PROCESSO (PDF/A)",
            font=get_font(FONT_SIZE_H3, "bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            corner_radius=RADIUS_BUTTON,
            height=48,
            command=self._ao_clicar_finalizar,
        )
        self.botao_finalizar.grid(row=0, column=1, sticky="ew")

    def _mostrar_etapa2(self) -> None:
        self.label_pasta_etapa2.configure(text=f"Pasta de destino: {self.pasta_saida}")
        self.container_etapa1.grid_forget()
        self.container_etapa2.grid(row=1, column=0, sticky="nsew")
        self._atualizar_stepper(2)

    def _mostrar_etapa1(self) -> None:
        self.container_etapa2.grid_forget()
        self.container_etapa1.grid(row=1, column=0, sticky="nsew")
        self._atualizar_stepper(1)

    def _ao_clicar_finalizar(self) -> None:
        if not self.pasta_saida:
            return

        documentos_externos = self.document_frame.obter_documentos_selecionados()

        self.botao_finalizar.configure(state="disabled")
        self.botao_voltar.configure(state="disabled")
        
        self._loading2 = LoadingModal(self, "Convertendo para PDF/A...")
        
        thread = threading.Thread(target=self._finalizar_em_background, args=(documentos_externos,), daemon=True)
        thread.start()

    def _finalizar_em_background(self, documentos_externos):
        try:
            resultado = executar_etapa2(
                pasta_base=self.pasta_saida,
                participantes=self.participantes_etapa1,
                arquivos_gerados_etapa1=self.arquivos_gerados_etapa1,
                documentos_externos=documentos_externos,
            )
            self.after(0, lambda: self._ao_concluir_etapa2(resultado))
        except Exception as exc:
            self.after(0, lambda: self._ao_erro_etapa2(exc))

    def _ao_concluir_etapa2(self, resultado):
        if hasattr(self, '_loading2'):
            self._loading2.dismiss()
            
        self.botao_finalizar.configure(state="normal")
        self.botao_voltar.configure(state="normal")
        
        if resultado["sucesso"]:
            msg = f"{resultado['mensagem']}\nEstrutura:\n{resultado['pasta_pdfa']}"
            if messagebox.askyesno("Concluído", msg + "\n\nDeseja abrir a pasta PDF-A?"):
                self._abrir_pasta(resultado["pasta_pdfa"])
            self._resetar_aplicacao()
        else:
            show_toast(self, resultado["mensagem"], "error")

    def _ao_erro_etapa2(self, exc):
        if hasattr(self, '_loading2'):
            self._loading2.dismiss()
        self.botao_finalizar.configure(state="normal")
        self.botao_voltar.configure(state="normal")
        show_toast(self, f"Erro: {str(exc)}", "error")

    def _resetar_aplicacao(self) -> None:
        self._mostrar_etapa1()
        for frame in list(self.participant_frames[1:]):
            self._remover_participante(frame)
        
        primeiro = self.participant_frames[0]
        primeiro.entry_nome.delete(0, "end")
        primeiro.entry_cpf.delete(0, "end")
        primeiro._validar_campo(primeiro.entry_nome)
        primeiro._validar_campo(primeiro.entry_cpf)
        
        if primeiro.entry_endereco:
            primeiro.entry_endereco.delete(0, "end")
            primeiro._validar_campo(primeiro.entry_endereco)
        if primeiro.entry_data:
            primeiro.entry_data.delete(0, "end")
            primeiro._validar_campo(primeiro.entry_data)
        
        self.document_frame.limpar()

    @staticmethod
    def _abrir_pasta(caminho: Path) -> None:
        if os.name == "nt":
            os.startfile(caminho)
        else:
            subprocess.run(["xdg-open", str(caminho)])

    # ------------------------------------------------------------------
    # Utilitários de Seleção (Etapa 1)
    # ------------------------------------------------------------------
    def _selecionar_modelo_ppe(self) -> None:
        caminho = selecionar_arquivo_pdf("Selecione o modelo PDF da Declaração PPE")
        if caminho:
            self.caminho_modelo_ppe = caminho
            self._atualizar_entry(self.entry_modelo_ppe, str(caminho))

    def _selecionar_modelo_primeiro_imovel(self) -> None:
        caminho = selecionar_arquivo_pdf("Selecione o modelo PDF da Declaração de Primeiro Imóvel")
        if caminho:
            self.caminho_modelo_primeiro_imovel = caminho
            self._atualizar_entry(self.entry_modelo_imovel, str(caminho))

    def _selecionar_pasta_saida(self) -> None:
        caminho = selecionar_pasta("Selecione a pasta de saída")
        if caminho:
            self.pasta_saida = caminho
            self._atualizar_entry(self.entry_pasta_saida, str(caminho))

    @staticmethod
    def _atualizar_entry(entry: ctk.CTkEntry, texto: str) -> None:
        entry.configure(state="normal", text_color=COLOR_TEXT)
        entry.delete(0, "end")
        entry.insert(0, texto)
        entry.configure(state="disabled")
