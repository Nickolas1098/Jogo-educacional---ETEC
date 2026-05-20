
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "jogo_quimica.db"

COR_VERMELHO = "#941611"
COR_VERMELHO_ESCURO = "#6F0F0C"
COR_CINZA = "#4A555C"
COR_FUNDO = "#F4F6F8"
COR_BRANCO = "#FFFFFF"
COR_VERDE = "#2E7D32"
COR_AZUL = "#1565C0"
COR_BORDA = "#DDDDDD"

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def conectar():
    return sqlite3.connect(DB_PATH)

def iniciar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('aluno', 'professor'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enunciado TEXT NOT NULL,
        alternativa_a TEXT NOT NULL,
        alternativa_b TEXT NOT NULL,
        alternativa_c TEXT NOT NULL,
        alternativa_d TEXT NOT NULL,
        correta TEXT NOT NULL,
        dica TEXT,
        nivel TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS desempenho (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        pontuacao INTEGER NOT NULL,
        total INTEGER NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        usuarios = [
            ("Aluno Demo", "aluno@etec.com", hash_senha("123456"), "aluno"),
            ("Professor Demo", "professor@etec.com", hash_senha("123456"), "professor")
        ]
        cur.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            usuarios
        )

    cur.execute("SELECT COUNT(*) FROM questoes")
    if cur.fetchone()[0] == 0:
        questoes = [
            (
                "Qual material é mais utilizado para medir volumes aproximados de líquidos?",
                "Béquer", "Cápsula de porcelana", "Pinça metálica", "Tela de amianto",
                "A", "É uma vidraria cilíndrica comum em laboratório.", "Fácil", "Identificação"
            ),
            (
                "Qual material é usado na filtração simples para apoiar o papel de filtro?",
                "Funil analítico", "Proveta", "Bastão de vidro", "Cadinho",
                "A", "Possui formato cônico.", "Fácil", "Material → função"
            ),
            (
                "Qual material mede volume com mais precisão do que um béquer?",
                "Erlenmeyer", "Proveta", "Tripé", "Almofariz",
                "B", "Possui marcações graduadas.", "Médio", "Função → material"
            ),
            (
                "Qual material pode ser utilizado para secagem ou aquecimento de pequenas quantidades de sólidos?",
                "Pipeta", "Funil de separação", "Cápsula de porcelana", "Termômetro",
                "C", "É feito de porcelana e suporta aquecimento.", "Médio", "Material → função"
            ),
            (
                "Em uma destilação simples, qual conjunto de materiais aparece com mais frequência?",
                "Funil, papel filtro e béquer", "Balão, condensador e fonte de aquecimento",
                "Almofariz, pistilo e pinça", "Proveta, pipeta e cápsula",
                "B", "O vapor precisa ser resfriado para voltar ao estado líquido.", "Difícil", "Sistema experimental"
            )
        ]
        cur.executemany("""
            INSERT INTO questoes 
            (enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, correta, dica, nivel, tipo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questoes)

    conn.commit()
    conn.close()

class BotaoAnimado(tk.Button):
    def __init__(self, master, texto, comando, cor=COR_VERMELHO, largura=None):
        super().__init__(
            master,
            text=texto,
            command=comando,
            bg=cor,
            fg="white",
            activebackground=COR_VERMELHO_ESCURO,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Arial", 11, "bold"),
            padx=18,
            pady=10,
            width=largura
        )
        self.cor = cor
        self.bind("<Enter>", self.entrar)
        self.bind("<Leave>", self.sair)

    def entrar(self, event):
        self.config(bg=COR_VERMELHO_ESCURO)

    def sair(self, event):
        self.config(bg=self.cor)

class JogoQuimica:
    def __init__(self, root):
        self.root = root
        self.root.title("Química Experimental - ETEC")
        self.root.geometry("1050x690")
        self.root.minsize(950, 620)
        self.root.configure(bg=COR_FUNDO)

        self.usuario = None
        self.questoes = []
        self.indice = 0
        self.pontos = 0
        self.resposta = tk.StringVar()
        self.alternativa_widgets = {}

        self.configurar_estilo()
        self.tela_inicial()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=COR_CINZA, foreground="white")
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)

    def limpar(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def cabecalho(self, titulo):
        frame = tk.Frame(self.root, bg=COR_VERMELHO, height=78)
        frame.pack(fill="x")
        frame.pack_propagate(False)

        tk.Label(
            frame,
            text=titulo,
            bg=COR_VERMELHO,
            fg="white",
            font=("Arial", 21, "bold")
        ).pack(side="left", padx=28)

        tk.Label(
            frame,
            text="Centro Paula Souza • ETEC Júlio de Mesquita",
            bg=COR_VERMELHO,
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side="right", padx=28)

    def card(self, parent, padx=30, pady=25):
        frame = tk.Frame(
            parent,
            bg=COR_BRANCO,
            padx=padx,
            pady=pady,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        return frame

    def tela_inicial(self):
        self.limpar()
        self.cabecalho("Química Experimental")

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=50, pady=35)

        tk.Label(
            conteudo,
            text="Jogo Educacional de Materiais de Laboratório",
            bg=COR_FUNDO,
            fg=COR_VERMELHO,
            font=("Arial", 28, "bold")
        ).pack(pady=(20, 8))

        tk.Label(
            conteudo,
            text="Aprenda a identificar vidrarias, utensílios, funções e sistemas experimentais de forma interativa.",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 14),
            wraplength=800,
            justify="center"
        ).pack(pady=8)

        card = self.card(conteudo, 40, 32)
        card.pack(pady=35)

        BotaoAnimado(card, "Entrar", self.tela_login, largura=28).pack(pady=8)
        BotaoAnimado(card, "Cadastrar usuário", self.tela_cadastro, largura=28, cor=COR_CINZA).pack(pady=8)
        BotaoAnimado(card, "Sair", self.root.destroy, largura=28, cor="#777777").pack(pady=8)

        tk.Label(
            conteudo,
            text="Usuários de teste: aluno@etec.com / 123456  |  professor@etec.com / 123456",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 10)
        ).pack(pady=10)

    def campo(self, parent, texto, show=None):
        tk.Label(parent, text=texto, bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 2))
        entrada = ttk.Entry(parent, show=show, width=44)
        entrada.pack(fill="x")
        return entrada

    def tela_login(self):
        self.limpar()
        self.cabecalho("Acesso ao Sistema")

        fundo = tk.Frame(self.root, bg=COR_FUNDO)
        fundo.pack(expand=True)

        card = self.card(fundo, 38, 32)
        card.pack()

        tk.Label(card, text="Entrar na plataforma", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 22, "bold")).pack(pady=(0, 10))
        tk.Label(card, text="Informe seus dados de acesso", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 11)).pack(pady=(0, 12))

        email = self.campo(card, "E-mail")
        senha = self.campo(card, "Senha", show="*")

        def entrar():
            conn = conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?", (email.get().strip().lower(),))
            user = cur.fetchone()
            conn.close()

            if user and user[3] == hash_senha(senha.get()):
                self.usuario = {"id": user[0], "nome": user[1], "email": user[2], "tipo": user[4]}
                if user[4] == "professor":
                    self.tela_professor()
                else:
                    self.tela_menu_aluno()
            else:
                messagebox.showerror("Erro", "E-mail ou senha inválidos.")

        BotaoAnimado(card, "Entrar", entrar, largura=30).pack(pady=(20, 8))
        BotaoAnimado(card, "Voltar", self.tela_inicial, largura=30, cor=COR_CINZA).pack(pady=6)

    def tela_cadastro(self):
        self.limpar()
        self.cabecalho("Cadastro de Usuário")

        card = self.card(self.root, 35, 25)
        card.pack(pady=35)

        tk.Label(card, text="Criar novo usuário", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 20, "bold")).pack(pady=8)

        nome = self.campo(card, "Nome")
        email = self.campo(card, "E-mail")
        senha = self.campo(card, "Senha", show="*")

        tk.Label(card, text="Tipo de usuário", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 2))
        tipo = ttk.Combobox(card, values=["aluno", "professor"], state="readonly")
        tipo.set("aluno")
        tipo.pack(fill="x")

        def cadastrar():
            if not nome.get() or not email.get() or not senha.get():
                messagebox.showwarning("Atenção", "Preencha todos os campos.")
                return
            try:
                conn = conectar()
                conn.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    (nome.get(), email.get().strip().lower(), hash_senha(senha.get()), tipo.get())
                )
                conn.commit()
                conn.close()
                messagebox.showinfo("Sucesso", "Cadastro realizado.")
                self.tela_login()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "E-mail já cadastrado.")

        BotaoAnimado(card, "Cadastrar", cadastrar, largura=30).pack(pady=(18, 8))
        BotaoAnimado(card, "Voltar", self.tela_inicial, largura=30, cor=COR_CINZA).pack(pady=6)

    def tela_menu_aluno(self):
        self.limpar()
        self.cabecalho("Área do Aluno")

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=45, pady=35)

        tk.Label(
            conteudo,
            text=f"Olá, {self.usuario['nome']}!",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 19, "bold")
        ).pack(pady=10)

        card = self.card(conteudo, 45, 32)
        card.pack(pady=30)

        BotaoAnimado(card, "Iniciar jogo", self.iniciar_jogo, largura=34).pack(pady=8)
        BotaoAnimado(card, "Ver ranking", self.tela_ranking, largura=34, cor=COR_AZUL).pack(pady=8)
        BotaoAnimado(card, "Sair", self.tela_inicial, largura=34, cor=COR_CINZA).pack(pady=8)

    def iniciar_jogo(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM questoes 
            ORDER BY CASE nivel WHEN 'Fácil' THEN 1 WHEN 'Médio' THEN 2 ELSE 3 END, id
        """)
        self.questoes = cur.fetchall()
        conn.close()

        self.indice = 0
        self.pontos = 0
        self.resposta.set("")
        self.tela_questao()

    def selecionar_alternativa(self, letra):
        self.resposta.set(letra)
        for l, widget in self.alternativa_widgets.items():
            if l == letra:
                widget.config(bg="#E8F0FE", highlightbackground=COR_AZUL, highlightthickness=2)
            else:
                widget.config(bg=COR_BRANCO, highlightbackground=COR_BORDA, highlightthickness=1)

    def tela_questao(self):
        self.limpar()
        self.cabecalho("Jogo - Materiais de Laboratório")

        if self.indice >= len(self.questoes):
            self.finalizar_jogo()
            return

        q = self.questoes[self.indice]
        self.resposta.set("")
        self.alternativa_widgets = {}

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=35, pady=24)

        tk.Label(
            conteudo,
            text=f"Questão {self.indice + 1}/{len(self.questoes)}   •   Pontos: {self.pontos}   •   Nível: {q[8]}   •   Tipo: {q[9]}",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 12))

        card = self.card(conteudo, 30, 25)
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text=q[1],
            bg=COR_BRANCO,
            fg=COR_CINZA,
            font=("Arial", 18, "bold"),
            wraplength=880,
            justify="left"
        ).pack(anchor="w", pady=(0, 18))

        alternativas = [
            ("A", q[2]),
            ("B", q[3]),
            ("C", q[4]),
            ("D", q[5])
        ]

        for letra, texto in alternativas:
            caixa = tk.Frame(card, bg=COR_BRANCO, padx=15, pady=12, highlightbackground=COR_BORDA, highlightthickness=1, cursor="hand2")
            caixa.pack(fill="x", pady=7)

            bolinha = tk.Label(caixa, text=letra, bg=COR_VERMELHO, fg="white", font=("Arial", 13, "bold"), width=3, height=1)
            bolinha.pack(side="left", padx=(0, 15))

            label = tk.Label(
                caixa,
                text=texto,
                bg=COR_BRANCO,
                fg=COR_CINZA,
                font=("Arial", 13),
                anchor="w",
                justify="left",
                wraplength=770
            )
            label.pack(side="left", fill="x", expand=True)

            def bind_all(widget, letra=letra):
                widget.bind("<Button-1>", lambda e: self.selecionar_alternativa(letra))
                widget.bind("<Enter>", lambda e: caixa.config(highlightbackground=COR_AZUL))
                widget.bind("<Leave>", lambda e: caixa.config(highlightbackground=COR_AZUL if self.resposta.get() == letra else COR_BORDA))

            bind_all(caixa)
            bind_all(label)
            bind_all(bolinha)
            self.alternativa_widgets[letra] = caixa

        botoes = tk.Frame(card, bg=COR_BRANCO)
        botoes.pack(fill="x", pady=18)

        BotaoAnimado(botoes, "Dica", lambda: messagebox.showinfo("Dica", q[7] if q[7] else "Sem dica cadastrada."), cor=COR_AZUL).pack(side="left", padx=5)
        BotaoAnimado(botoes, "Responder", self.verificar_resposta).pack(side="right", padx=5)
        BotaoAnimado(botoes, "Sair", self.tela_menu_aluno, cor=COR_CINZA).pack(side="right", padx=5)

    def verificar_resposta(self):
        if not self.resposta.get():
            messagebox.showwarning("Atenção", "Selecione uma alternativa.")
            return

        q = self.questoes[self.indice]
        correta = q[6]

        if self.resposta.get() == correta:
            self.pontos += 1
            messagebox.showinfo("Resultado", "Resposta correta!")
        else:
            messagebox.showinfo("Resultado", f"Resposta incorreta. Alternativa correta: {correta}")

        self.indice += 1
        self.tela_questao()

    def finalizar_jogo(self):
        total = len(self.questoes)

        conn = conectar()
        conn.execute(
            "INSERT INTO desempenho (usuario_id, pontuacao, total, data) VALUES (?, ?, ?, ?)",
            (self.usuario["id"], self.pontos, total, datetime.now().strftime("%d/%m/%Y %H:%M"))
        )
        conn.commit()
        conn.close()

        self.limpar()
        self.cabecalho("Resultado")

        card = self.card(self.root, 45, 35)
        card.pack(pady=85)

        percentual = round((self.pontos / total) * 100, 1) if total else 0

        tk.Label(card, text="Partida finalizada!", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 25, "bold")).pack(pady=10)
        tk.Label(card, text=f"Pontuação: {self.pontos}/{total}", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 18)).pack(pady=8)
        tk.Label(card, text=f"Aproveitamento: {percentual}%", bg=COR_BRANCO, fg=COR_VERDE, font=("Arial", 17, "bold")).pack(pady=8)

        BotaoAnimado(card, "Jogar novamente", self.iniciar_jogo, largura=30).pack(pady=8)
        BotaoAnimado(card, "Ver ranking", self.tela_ranking, largura=30, cor=COR_AZUL).pack(pady=8)
        BotaoAnimado(card, "Voltar ao menu", self.tela_menu_aluno, largura=30, cor=COR_CINZA).pack(pady=8)

    def tela_professor(self):
        self.limpar()
        self.cabecalho("Área do Professor")

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=45, pady=35)

        tk.Label(
            conteudo,
            text=f"Bem-vindo(a), {self.usuario['nome']}",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 18, "bold")
        ).pack(anchor="w", pady=10)

        card = self.card(conteudo, 40, 28)
        card.pack(fill="x", pady=15)

        BotaoAnimado(card, "Cadastrar nova questão", self.tela_nova_questao, largura=38).pack(pady=8)
        BotaoAnimado(card, "Visualizar questões cadastradas", self.tela_listar_questoes, largura=38, cor=COR_AZUL).pack(pady=8)
        BotaoAnimado(card, "Visualizar usuários cadastrados", self.tela_usuarios_cadastrados, largura=38, cor=COR_CINZA).pack(pady=8)
        BotaoAnimado(card, "Relatório de desempenho dos alunos", self.tela_relatorios, largura=38, cor=COR_VERDE).pack(pady=8)
        BotaoAnimado(card, "Ranking geral", self.tela_ranking, largura=38, cor="#8A6D00").pack(pady=8)
        BotaoAnimado(card, "Sair", self.tela_inicial, largura=38, cor="#777777").pack(pady=8)

    def tela_nova_questao(self):
        self.limpar()
        self.cabecalho("Cadastrar Questão")

        frame = self.card(self.root, 30, 18)
        frame.pack(fill="both", expand=True, padx=35, pady=25)

        def label(texto):
            tk.Label(frame, text=texto, bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 1))

        label("Enunciado")
        enunciado = tk.Text(frame, height=3, width=90, font=("Arial", 10))
        enunciado.pack(fill="x")

        entradas = {}
        for campo in ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D", "Dica"]:
            label(campo)
            e = ttk.Entry(frame)
            e.pack(fill="x")
            entradas[campo] = e

        linha = tk.Frame(frame, bg=COR_BRANCO)
        linha.pack(fill="x", pady=8)

        tk.Label(linha, text="Correta", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        correta = ttk.Combobox(linha, values=["A", "B", "C", "D"], state="readonly", width=10)
        correta.set("A")
        correta.grid(row=1, column=0, padx=5)

        tk.Label(linha, text="Nível", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w")
        nivel = ttk.Combobox(linha, values=["Fácil", "Médio", "Difícil"], state="readonly", width=15)
        nivel.set("Fácil")
        nivel.grid(row=1, column=1, padx=5)

        tk.Label(linha, text="Tipo", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="w")
        tipo = ttk.Combobox(
            linha,
            values=["Identificação", "Material → função", "Função → material", "Sistema experimental", "Associação"],
            state="readonly",
            width=28
        )
        tipo.set("Identificação")
        tipo.grid(row=1, column=2, padx=5)

        def salvar():
            if not enunciado.get("1.0", "end").strip():
                messagebox.showwarning("Atenção", "Informe o enunciado.")
                return

            conn = conectar()
            conn.execute("""
                INSERT INTO questoes 
                (enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, correta, dica, nivel, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                enunciado.get("1.0", "end").strip(),
                entradas["Alternativa A"].get(),
                entradas["Alternativa B"].get(),
                entradas["Alternativa C"].get(),
                entradas["Alternativa D"].get(),
                correta.get(),
                entradas["Dica"].get(),
                nivel.get(),
                tipo.get()
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Questão cadastrada.")
            self.tela_listar_questoes()

        botoes = tk.Frame(frame, bg=COR_BRANCO)
        botoes.pack(fill="x", pady=12)
        BotaoAnimado(botoes, "Salvar questão", salvar).pack(side="right", padx=5)
        BotaoAnimado(botoes, "Voltar", self.tela_professor, cor=COR_CINZA).pack(side="right", padx=5)

    def montar_tabela(self, parent, colunas, larguras):
        tabela = ttk.Treeview(parent, columns=colunas, show="headings")
        for c in colunas:
            tabela.heading(c, text=c.capitalize())
            tabela.column(c, width=larguras.get(c, 120))
        tabela.pack(fill="both", expand=True)
        return tabela

    def tela_listar_questoes(self):
        self.limpar()
        self.cabecalho("Questões Cadastradas")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        tabela = self.montar_tabela(frame, ("id", "nivel", "tipo", "enunciado"), {
            "id": 50, "nivel": 100, "tipo": 180, "enunciado": 650
        })

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nivel, tipo, enunciado FROM questoes ORDER BY id DESC")
        for row in cur.fetchall():
            tabela.insert("", "end", values=row)
        conn.close()

        BotaoAnimado(frame, "Voltar", self.tela_professor, cor=COR_CINZA).pack(pady=12)

    def tela_usuarios_cadastrados(self):
        self.limpar()
        self.cabecalho("Usuários Cadastrados")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        tabela = self.montar_tabela(frame, ("id", "nome", "email", "tipo"), {
            "id": 60, "nome": 280, "email": 360, "tipo": 120
        })

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, tipo FROM usuarios ORDER BY id DESC")
        for row in cur.fetchall():
            tabela.insert("", "end", values=row)
        conn.close()

        BotaoAnimado(frame, "Voltar", self.tela_professor, cor=COR_CINZA).pack(pady=12)

    def tela_relatorios(self):
        self.limpar()
        self.cabecalho("Relatórios de Desempenho")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        tabela = self.montar_tabela(frame, ("aluno", "pontuacao", "total", "aproveitamento", "data"), {
            "aluno": 260, "pontuacao": 100, "total": 80, "aproveitamento": 140, "data": 180
        })

        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.nome, d.pontuacao, d.total, d.data
            FROM desempenho d
            JOIN usuarios u ON u.id = d.usuario_id
            ORDER BY d.id DESC
        """)
        for nome, pontos, total, data in cur.fetchall():
            aproveitamento = f"{round((pontos / total) * 100, 1)}%" if total else "0%"
            tabela.insert("", "end", values=(nome, pontos, total, aproveitamento, data))
        conn.close()

        BotaoAnimado(frame, "Voltar", self.voltar_por_tipo, cor=COR_CINZA).pack(pady=12)

    def tela_ranking(self):
        self.limpar()
        self.cabecalho("Ranking Geral")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(
            frame,
            text="Classificação dos alunos por melhor aproveitamento",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 15, "bold")
        ).pack(anchor="w", pady=(0, 12))

        tabela = self.montar_tabela(frame, ("posição", "aluno", "melhor_pontuação", "total", "aproveitamento"), {
            "posição": 90, "aluno": 320, "melhor_pontuação": 160, "total": 90, "aproveitamento": 160
        })

        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.nome,
                MAX(d.pontuacao) as melhor,
                d.total,
                ROUND((MAX(d.pontuacao) * 100.0) / d.total, 1) as aproveitamento
            FROM desempenho d
            JOIN usuarios u ON u.id = d.usuario_id
            GROUP BY u.id, u.nome, d.total
            ORDER BY aproveitamento DESC, melhor DESC
        """)
        for pos, row in enumerate(cur.fetchall(), start=1):
            nome, melhor, total, aproveitamento = row
            tabela.insert("", "end", values=(pos, nome, melhor, total, f"{aproveitamento}%"))
        conn.close()

        BotaoAnimado(frame, "Voltar", self.voltar_por_tipo, cor=COR_CINZA).pack(pady=12)

    def voltar_por_tipo(self):
        if self.usuario and self.usuario.get("tipo") == "professor":
            self.tela_professor()
        elif self.usuario and self.usuario.get("tipo") == "aluno":
            self.tela_menu_aluno()
        else:
            self.tela_inicial()

if __name__ == "__main__":
    iniciar_banco()
    root = tk.Tk()
    app = JogoQuimica(root)
    root.mainloop()
