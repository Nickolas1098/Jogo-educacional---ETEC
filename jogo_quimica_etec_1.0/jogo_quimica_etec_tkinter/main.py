
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "jogo_quimica.db"

COR_VERMELHO = "#941611"
COR_CINZA = "#4A555C"
COR_FUNDO = "#F5F5F5"
COR_BRANCO = "#FFFFFF"
COR_VERDE = "#2E7D32"
COR_AZUL = "#1565C0"

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

class JogoQuimica:
    def __init__(self, root):
        self.root = root
        self.root.title("LabQuest ETEC - Jogo de Química")
        self.root.geometry("980x640")
        self.root.configure(bg=COR_FUNDO)
        self.usuario = None
        self.questoes = []
        self.indice = 0
        self.pontos = 0
        self.resposta = tk.StringVar()
        self.dica_usada = False

        self.configurar_estilo()
        self.tela_inicial()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Arial", 11), padding=8)
        style.configure("Titulo.TLabel", font=("Arial", 24, "bold"), background=COR_FUNDO, foreground=COR_VERMELHO)
        style.configure("Subtitulo.TLabel", font=("Arial", 13), background=COR_FUNDO, foreground=COR_CINZA)
        style.configure("Texto.TLabel", font=("Arial", 11), background=COR_FUNDO, foreground=COR_CINZA)

    def limpar(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def cabecalho(self, titulo):
        frame = tk.Frame(self.root, bg=COR_VERMELHO, height=72)
        frame.pack(fill="x")
        tk.Label(
            frame,
            text=titulo,
            bg=COR_VERMELHO,
            fg="white",
            font=("Arial", 20, "bold")
        ).pack(side="left", padx=24, pady=18)

        tk.Label(
            frame,
            text="Centro Paula Souza • ETEC Júlio de Mesquita",
            bg=COR_VERMELHO,
            fg="white",
            font=("Arial", 10)
        ).pack(side="right", padx=24)

    def tela_inicial(self):
        self.limpar()
        self.cabecalho("LabQuest ETEC")

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(
            conteudo,
            text="Jogo Educacional de Materiais de Laboratório",
            bg=COR_FUNDO,
            fg=COR_VERMELHO,
            font=("Arial", 26, "bold")
        ).pack(pady=18)

        tk.Label(
            conteudo,
            text="Aprenda a identificar vidrarias, utensílios, funções e sistemas experimentais da Química Geral e Experimental.",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 13),
            wraplength=760,
            justify="center"
        ).pack(pady=10)

        card = tk.Frame(conteudo, bg=COR_BRANCO, padx=30, pady=25, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(pady=30)

        ttk.Button(card, text="Entrar", command=self.tela_login).pack(fill="x", pady=8)
        ttk.Button(card, text="Cadastrar usuário", command=self.tela_cadastro).pack(fill="x", pady=8)
        ttk.Button(card, text="Sair", command=self.root.destroy).pack(fill="x", pady=8)

        tk.Label(
            conteudo,
            text="Usuários de teste: aluno@etec.com / 123456  |  professor@etec.com / 123456",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 10)
        ).pack(pady=8)

    def campo(self, parent, texto, show=None):
        tk.Label(parent, text=texto, bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 2))
        entrada = ttk.Entry(parent, show=show, width=42)
        entrada.pack(fill="x")
        return entrada

    def tela_login(self):
        self.limpar()
        self.cabecalho("Login")

        card = tk.Frame(self.root, bg=COR_BRANCO, padx=35, pady=30, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(pady=70)

        tk.Label(card, text="Acesse sua conta", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 20, "bold")).pack(pady=10)

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
                    self.iniciar_jogo()
            else:
                messagebox.showerror("Erro", "E-mail ou senha inválidos.")

        ttk.Button(card, text="Entrar", command=entrar).pack(fill="x", pady=18)
        ttk.Button(card, text="Voltar", command=self.tela_inicial).pack(fill="x")

    def tela_cadastro(self):
        self.limpar()
        self.cabecalho("Cadastro")

        card = tk.Frame(self.root, bg=COR_BRANCO, padx=35, pady=25, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(pady=35)

        tk.Label(card, text="Criar novo usuário", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 20, "bold")).pack(pady=10)

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

        ttk.Button(card, text="Cadastrar", command=cadastrar).pack(fill="x", pady=18)
        ttk.Button(card, text="Voltar", command=self.tela_inicial).pack(fill="x")

    def iniciar_jogo(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM questoes 
            ORDER BY CASE nivel WHEN 'Fácil' THEN 1 WHEN 'Médio' THEN 2 ELSE 3 END, id
        """)
        dados = cur.fetchall()
        conn.close()

        self.questoes = dados
        self.indice = 0
        self.pontos = 0
        self.resposta.set("")
        self.dica_usada = False
        self.tela_questao()

    def tela_questao(self):
        self.limpar()
        self.cabecalho("Modo Aluno")

        if self.indice >= len(self.questoes):
            self.finalizar_jogo()
            return

        q = self.questoes[self.indice]
        self.resposta.set("")
        self.dica_usada = False

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=35, pady=25)

        topo = tk.Frame(conteudo, bg=COR_FUNDO)
        topo.pack(fill="x")

        tk.Label(
            topo,
            text=f"Aluno: {self.usuario['nome']}   |   Questão {self.indice + 1}/{len(self.questoes)}   |   Pontos: {self.pontos}",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 11, "bold")
        ).pack(side="left")

        tk.Label(
            topo,
            text=f"Nível: {q[8]}  |  Tipo: {q[9]}",
            bg=COR_FUNDO,
            fg=COR_AZUL,
            font=("Arial", 11, "bold")
        ).pack(side="right")

        card = tk.Frame(conteudo, bg=COR_BRANCO, padx=30, pady=25, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(fill="both", expand=True, pady=20)

        tk.Label(
            card,
            text=q[1],
            bg=COR_BRANCO,
            fg=COR_CINZA,
            font=("Arial", 17, "bold"),
            wraplength=830,
            justify="left"
        ).pack(anchor="w", pady=10)

        alternativas = [
            ("A", q[2]),
            ("B", q[3]),
            ("C", q[4]),
            ("D", q[5])
        ]

        for letra, texto in alternativas:
            rb = tk.Radiobutton(
                card,
                text=f"{letra}) {texto}",
                variable=self.resposta,
                value=letra,
                bg=COR_BRANCO,
                fg=COR_CINZA,
                font=("Arial", 13),
                anchor="w",
                justify="left",
                wraplength=780,
                activebackground=COR_BRANCO
            )
            rb.pack(fill="x", pady=6)

        botoes = tk.Frame(card, bg=COR_BRANCO)
        botoes.pack(fill="x", pady=20)

        ttk.Button(botoes, text="Usar dica", command=lambda: messagebox.showinfo("Dica", q[7] if q[7] else "Sem dica cadastrada.")).pack(side="left", padx=5)
        ttk.Button(botoes, text="Responder", command=self.verificar_resposta).pack(side="right", padx=5)
        ttk.Button(botoes, text="Sair do jogo", command=self.tela_inicial).pack(side="right", padx=5)

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

        card = tk.Frame(self.root, bg=COR_BRANCO, padx=40, pady=35, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(pady=80)

        percentual = round((self.pontos / total) * 100, 1) if total else 0

        tk.Label(card, text="Partida finalizada!", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Arial", 24, "bold")).pack(pady=10)
        tk.Label(card, text=f"Pontuação: {self.pontos}/{total}", bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 18)).pack(pady=8)
        tk.Label(card, text=f"Aproveitamento: {percentual}%", bg=COR_BRANCO, fg=COR_VERDE, font=("Arial", 16, "bold")).pack(pady=8)

        ttk.Button(card, text="Jogar novamente", command=self.iniciar_jogo).pack(fill="x", pady=8)
        ttk.Button(card, text="Voltar ao início", command=self.tela_inicial).pack(fill="x", pady=8)

    def tela_professor(self):
        self.limpar()
        self.cabecalho("Área do Professor")

        conteudo = tk.Frame(self.root, bg=COR_FUNDO)
        conteudo.pack(expand=True, fill="both", padx=35, pady=25)

        tk.Label(
            conteudo,
            text=f"Bem-vindo(a), {self.usuario['nome']}",
            bg=COR_FUNDO,
            fg=COR_CINZA,
            font=("Arial", 16, "bold")
        ).pack(anchor="w", pady=10)

        card = tk.Frame(conteudo, bg=COR_BRANCO, padx=30, pady=25, highlightbackground="#DDDDDD", highlightthickness=1)
        card.pack(fill="x", pady=15)

        ttk.Button(card, text="Cadastrar nova questão", command=self.tela_nova_questao).pack(fill="x", pady=8)
        ttk.Button(card, text="Visualizar questões cadastradas", command=self.tela_listar_questoes).pack(fill="x", pady=8)
        ttk.Button(card, text="Relatório de desempenho dos alunos", command=self.tela_relatorios).pack(fill="x", pady=8)
        ttk.Button(card, text="Sair", command=self.tela_inicial).pack(fill="x", pady=8)

    def tela_nova_questao(self):
        self.limpar()
        self.cabecalho("Cadastrar Questão")

        frame = tk.Frame(self.root, bg=COR_BRANCO, padx=30, pady=20, highlightbackground="#DDDDDD", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=35, pady=25)

        def label(texto):
            tk.Label(frame, text=texto, bg=COR_BRANCO, fg=COR_CINZA, font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 1))

        label("Enunciado")
        enunciado = tk.Text(frame, height=3, width=90)
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
            self.tela_professor()

        botoes = tk.Frame(frame, bg=COR_BRANCO)
        botoes.pack(fill="x", pady=12)
        ttk.Button(botoes, text="Salvar questão", command=salvar).pack(side="right", padx=5)
        ttk.Button(botoes, text="Voltar", command=self.tela_professor).pack(side="right", padx=5)

    def tela_listar_questoes(self):
        self.limpar()
        self.cabecalho("Questões Cadastradas")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        colunas = ("id", "nivel", "tipo", "enunciado")
        tabela = ttk.Treeview(frame, columns=colunas, show="headings")
        tabela.heading("id", text="ID")
        tabela.heading("nivel", text="Nível")
        tabela.heading("tipo", text="Tipo")
        tabela.heading("enunciado", text="Enunciado")
        tabela.column("id", width=50)
        tabela.column("nivel", width=100)
        tabela.column("tipo", width=180)
        tabela.column("enunciado", width=600)
        tabela.pack(fill="both", expand=True)

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nivel, tipo, enunciado FROM questoes ORDER BY id DESC")
        for row in cur.fetchall():
            tabela.insert("", "end", values=row)
        conn.close()

        ttk.Button(frame, text="Voltar", command=self.tela_professor).pack(pady=12)

    def tela_relatorios(self):
        self.limpar()
        self.cabecalho("Relatórios de Desempenho")

        frame = tk.Frame(self.root, bg=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=25, pady=20)

        colunas = ("aluno", "pontuacao", "total", "aproveitamento", "data")
        tabela = ttk.Treeview(frame, columns=colunas, show="headings")
        for c in colunas:
            tabela.heading(c, text=c.capitalize())
        tabela.column("aluno", width=250)
        tabela.column("pontuacao", width=100)
        tabela.column("total", width=80)
        tabela.column("aproveitamento", width=130)
        tabela.column("data", width=160)
        tabela.pack(fill="both", expand=True)

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

        ttk.Button(frame, text="Voltar", command=self.tela_professor).pack(pady=12)

if __name__ == "__main__":
    iniciar_banco()
    root = tk.Tk()
    app = JogoQuimica(root)
    root.mainloop()
