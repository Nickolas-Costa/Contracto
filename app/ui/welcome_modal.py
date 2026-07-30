import customtkinter as ctk
from ui import theme
from utils import config_manager


class WelcomeModal(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.title("Bem-vindo(a) ao Contracto")
        self.geometry("600x450")
        self.resizable(False, False)
        
        # Centralizar a janela em relação ao pai
        if master:
            self.transient(master)
            master.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() - 600) // 2
            y = master.winfo_y() + (master.winfo_height() - 450) // 2
            self.geometry(f"+{x}+{y}")
        
        # Bloquear a janela principal
        self.grab_set()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. Cabeçalho com degradê
        self.canvas_header = ctk.CTkCanvas(
            self, height=80, bg=theme.COLOR_BACKGROUND[0], highlightthickness=0
        )
        self.canvas_header.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self, text="Bem-vindo(a) à Versão 2.0!", 
            font=theme.get_font(20, "bold"), text_color="white", bg_color="transparent"
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")
        
        self.bind("<Configure>", self._on_configure)
        
        # 2. Área de Conteúdo
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Passos do tutorial
        self.passos = [
            {
                "titulo": "✨ Tudo em conformidade",
                "texto": "Agora o Contracto converte automaticamente todos os formulários e planilhas externas para PDF/A-2b, gerando as pastas ASSINADOS e REGISTRADOS no padrão exigido pelo dossiê digital."
            },
            {
                "titulo": "⚙️ Configurações Salvas",
                "texto": "Esqueceu de preencher o local da assinatura? Quer mudar a cor do sistema? Acesse o menu de Configurações! Suas preferências são salvas automaticamente e não se perdem ao atualizar o app."
            },
            {
                "titulo": "📋 Sistema de Perfis",
                "texto": "Crie perfis combinando diferentes modelos PDF. Na aba Perfis, você pode criar uma configuração para 'Imóvel Novo' e outra para 'Usado', agilizando o seu dia a dia."
            }
        ]
        
        self.passo_atual = 0
        
        self.titulo_passo = ctk.CTkLabel(
            self.content_frame, text="", font=theme.get_font(18, "bold"), text_color=theme.COLOR_PRIMARY
        )
        self.titulo_passo.grid(row=0, column=0, pady=(10, 15), sticky="w")
        
        self.texto_passo = ctk.CTkLabel(
            self.content_frame, text="", font=theme.get_font(14), justify="left", wraplength=500
        )
        self.texto_passo.grid(row=1, column=0, sticky="nw")
        
        # Indicador de progresso (bolinhas)
        self.progress_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.progress_frame.grid(row=2, column=0, pady=(50, 0))
        self.dots = []
        for i in range(len(self.passos)):
            lbl = ctk.CTkLabel(self.progress_frame, text="●", font=theme.get_font(20))
            lbl.pack(side="left", padx=5)
            self.dots.append(lbl)
            
        # 3. Rodapé com Botões
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 20))
        self.footer.grid_columnconfigure(0, weight=1)
        
        self.btn_next = ctk.CTkButton(
            self.footer, text="Próximo", command=self._proximo_passo,
            font=theme.get_font(14, "bold"), height=40, corner_radius=theme.RADIUS_BUTTON
        )
        self.btn_next.grid(row=0, column=1, sticky="e")
        
        self._atualizar_tela()

    def _on_configure(self, event=None) -> None:
        self.after(50, self._desenhar_gradiente)

    def _desenhar_gradiente(self) -> None:
        largura = max(self.winfo_width(), 600)
        altura = 80
        modo = ctk.get_appearance_mode()
        
        if modo == "Dark":
            cor1 = theme.COLOR_PRIMARY
            cor2 = theme.get_color_primary_dark_gradient()
        else:
            cor1 = theme.COLOR_PRIMARY
            cor2 = theme.get_color_primary_light()
            
        theme.aplicar_gradiente(self.canvas_header, largura, altura, cor1, cor2, vertical=False)
        self.title_label.tkraise()

    def _atualizar_tela(self):
        passo = self.passos[self.passo_atual]
        self.titulo_passo.configure(text=passo["titulo"])
        self.texto_passo.configure(text=passo["texto"])
        
        # Atualizar bolinhas
        for i, dot in enumerate(self.dots):
            if i == self.passo_atual:
                dot.configure(text_color=theme.COLOR_PRIMARY)
            else:
                dot.configure(text_color=theme.COLOR_TEXT_DISABLED[0] if ctk.get_appearance_mode() == "Light" else theme.COLOR_TEXT_DISABLED[1])
                
        # Atualizar botão
        if self.passo_atual == len(self.passos) - 1:
            self.btn_next.configure(text="Começar a Usar!")
        else:
            self.btn_next.configure(text="Próximo")

    def _proximo_passo(self):
        if self.passo_atual < len(self.passos) - 1:
            self.passo_atual += 1
            self._atualizar_tela()
        else:
            self._on_close()

    def _on_close(self):
        # Desabilitar a flag de primeira execução
        config_manager.definir("primeira_execucao", False)
        self.grab_release()
        self.destroy()
