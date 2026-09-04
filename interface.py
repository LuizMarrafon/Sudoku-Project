import sys
import copy
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QPushButton, QComboBox, QLabel, QFrame, QMessageBox, QPlainTextEdit, QGroupBox, QSpinBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QFont
from sudoku import criar_sudoku_aleatorio
from sudoku import validaSudoku
from dfs import resolver_dfs
from heuristica import resolver_best_first

class InterfaceSudoku(QWidget):
    def __init__(self):
        super().__init__()
        self.celulas = []
        self.sudoku_inicial = None
        self.historico = []
        self.indice_passo = -1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.proximo_passo)
        self.configurar_janela()
        self.criar_interface()

    def configurar_janela(self):
        self.setWindowTitle("Sudoku IA - Buscas")
        self.resize(1050, 850)
        self.setStyleSheet("""
            QWidget {
                background-color: #f2f2f2;
                color: #111111;
                font-family: Arial;
            }
            QLabel {
                color: #111111;
            }
            QPushButton {
                background-color: #ffffff;
                color: #111111;
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #777777;
            }
            QComboBox {
                background-color: white;
                color: black;
                border: 1px solid #777777;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
            }
            QSpinBox {
                background-color: white;
                color: black;
                border: 1px solid #777777;
                padding: 5px;
            }
            QGroupBox {
                color: #111111;
                font-weight: bold;
                border: 1px solid #999999;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QPlainTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #777777;
            }
        """)

    def criar_interface(self):
        layout_principal = QHBoxLayout()
        lado_esquerdo = QVBoxLayout()
        lado_direito = QVBoxLayout()
        titulo = QLabel("SUDOKU IA")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setFont(QFont("Arial", 24, QFont.Bold))
        lado_esquerdo.addWidget(titulo)
        layout_sudoku = QGridLayout()
        layout_sudoku.setSpacing(4)
        layout_sudoku.setAlignment(Qt.AlignCenter)
        for i in range(9):
            self.celulas.append([None] * 9)
        for bloco_linha in range(3):
            for bloco_coluna in range(3):
                bloco = QFrame()
                bloco.setStyleSheet("""
                    QFrame {
                        background-color: #202020;
                        border: 2px solid #111111;
                    }
                """)
                layout_bloco = QGridLayout()
                layout_bloco.setSpacing(2)
                layout_bloco.setContentsMargins(3, 3, 3, 3)
                for i in range(3):
                    for j in range(3):
                        linha = bloco_linha * 3 + i
                        coluna = bloco_coluna * 3 + j
                        campo = QLineEdit()
                        campo.setFixedSize(58, 58)
                        campo.setAlignment(Qt.AlignCenter)
                        campo.setFont(QFont("Arial", 21, QFont.Bold))
                        campo.setMaxLength(1)
                        campo.setValidator(QIntValidator(1, 9))
                        campo.setStyleSheet("""
                            QLineEdit {
                                background-color: white;
                                color: black;
                                border: 1px solid #777777;
                            }
                        """)
                        self.celulas[linha][coluna] = campo
                        layout_bloco.addWidget(campo, i, j)
                bloco.setLayout(layout_bloco)
                layout_sudoku.addWidget(bloco, bloco_linha, bloco_coluna)
        lado_esquerdo.addLayout(layout_sudoku)
        grupo_algoritmo = QGroupBox("Configuração")
        layout_config = QVBoxLayout()
        layout_algoritmo = QHBoxLayout()
        layout_algoritmo.addWidget(QLabel("Algoritmo:"))
        self.combo_algoritmo = QComboBox()
        self.combo_algoritmo.addItem("DFS")
        self.combo_algoritmo.addItem("Best First + MRV")
        layout_algoritmo.addWidget(self.combo_algoritmo)
        layout_config.addLayout(layout_algoritmo)
        layout_velocidade = QHBoxLayout()
        layout_velocidade.addWidget(QLabel("Velocidade da animação:"))
        self.spin_velocidade = QSpinBox()
        self.spin_velocidade.setRange(100, 3000)
        self.spin_velocidade.setValue(500)
        self.spin_velocidade.setSingleStep(100)
        self.spin_velocidade.setSuffix(" ms")
        layout_velocidade.addWidget(self.spin_velocidade)
        layout_config.addLayout(layout_velocidade)
        grupo_algoritmo.setLayout(layout_config)
        lado_esquerdo.addWidget(grupo_algoritmo)
        layout_botoes1 = QHBoxLayout()
        self.botao_gerar = QPushButton("Gerar Sudoku")
        self.botao_limpar = QPushButton("Limpar")
        self.botao_resolver = QPushButton("Preparar Resolução")
        layout_botoes1.addWidget(self.botao_gerar)
        layout_botoes1.addWidget(self.botao_limpar)
        layout_botoes1.addWidget(self.botao_resolver)
        lado_esquerdo.addLayout(layout_botoes1)
        layout_botoes2 = QHBoxLayout()
        self.botao_proximo = QPushButton("Próximo Passo")
        self.botao_automatico = QPushButton("Automático")
        self.botao_comparar = QPushButton("Comparar Algoritmos")
        self.botao_proximo.setEnabled(False)
        self.botao_automatico.setEnabled(False)
        layout_botoes2.addWidget(self.botao_proximo)
        layout_botoes2.addWidget(self.botao_automatico)
        layout_botoes2.addWidget(self.botao_comparar)
        lado_esquerdo.addLayout(layout_botoes2)
        self.label_status = QLabel("Digite um Sudoku ou clique em Gerar Sudoku.")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setFont(QFont("Arial", 12))
        lado_esquerdo.addWidget(self.label_status)
        grupo_metricas = QGroupBox("Métricas")
        layout_metricas = QVBoxLayout()
        self.label_tempo = QLabel("Tempo: -")
        self.label_tentativas = QLabel("Tentativas: -")
        self.label_nos = QLabel("Nós explorados: -")
        self.label_passos = QLabel("Passos: -")
        layout_metricas.addWidget(self.label_tempo)
        layout_metricas.addWidget(self.label_tentativas)
        layout_metricas.addWidget(self.label_nos)
        layout_metricas.addWidget(self.label_passos)
        grupo_metricas.setLayout(layout_metricas)
        lado_direito.addWidget(grupo_metricas)
        grupo_explicacao = QGroupBox("Explicação do passo")
        layout_explicacao = QVBoxLayout()
        self.texto_explicacao = QPlainTextEdit()
        self.texto_explicacao.setReadOnly(True)
        self.texto_explicacao.setMinimumWidth(400)
        self.texto_explicacao.setMinimumHeight(600)
        self.texto_explicacao.setFont(QFont("Consolas", 10))
        self.texto_explicacao.setPlainText("Aqui aparecerá a explicação de cada passo da busca.")
        layout_explicacao.addWidget(self.texto_explicacao)
        grupo_explicacao.setLayout(layout_explicacao)
        lado_direito.addWidget(grupo_explicacao)
        layout_principal.addLayout(lado_esquerdo)
        layout_principal.addLayout(lado_direito)
        self.setLayout(layout_principal)
        self.botao_gerar.clicked.connect(self.gerar_sudoku)
        self.botao_limpar.clicked.connect(self.limpar_sudoku)
        self.botao_resolver.clicked.connect(self.preparar_resolucao)
        self.botao_proximo.clicked.connect(self.proximo_passo)
        self.botao_automatico.clicked.connect(self.alternar_automatico)
        self.botao_comparar.clicked.connect(self.comparar_algoritmos)

    def ler_interface(self):
        sudoku = []
        for i in range(9):
            linha = []
            for j in range(9):
                texto = self.celulas[i][j].text()
                if texto == "":
                    linha.append(0)
                else:
                    linha.append(int(texto))
            sudoku.append(linha)
        return sudoku

    def preencher_interface(self, sudoku):
        for i in range(9):
            for j in range(9):
                if sudoku[i][j] == 0:
                    self.celulas[i][j].clear()
                else:
                    self.celulas[i][j].setText(str(sudoku[i][j]))

    def atualizar_estilo(self, linha_destaque=-1, coluna_destaque=-1, tipo=""):
        for i in range(9):
            for j in range(9):
                fixa = False
                if self.sudoku_inicial is not None:
                    if self.sudoku_inicial[i][j] != 0:
                        fixa = True
                if fixa:
                    estilo = """
                        QLineEdit {
                            background-color: #d6d6d6;
                            color: #111111;
                            font-weight: bold;
                            border: 1px solid #555555;
                        }
                    """
                else:
                    estilo = """
                        QLineEdit {
                            background-color: #ffffff;
                            color: #111111;
                            font-weight: bold;
                            border: 1px solid #777777;
                        }
                    """
                if i == linha_destaque and j == coluna_destaque:
                    if tipo == "remover":
                        estilo = """
                            QLineEdit {
                                background-color: #ff9e9e;
                                color: black;
                                font-weight: bold;
                                border: 3px solid #d00000;
                            }
                        """
                    elif tipo == "mrv":
                        estilo = """
                            QLineEdit {
                                background-color: #9ed0ff;
                                color: black;
                                font-weight: bold;
                                border: 3px solid #0066cc;
                            }
                        """
                    else:
                        estilo = """
                            QLineEdit {
                                background-color: #a8e6a3;
                                color: black;
                                font-weight: bold;
                                border: 3px solid #218838;
                            }
                        """
                self.celulas[i][j].setStyleSheet(estilo)

    def gerar_sudoku(self):
        self.parar_animacao()
        sudoku = criar_sudoku_aleatorio()
        self.sudoku_inicial = copy.deepcopy(sudoku)
        self.preencher_interface(sudoku)
        for i in range(9):
            for j in range(9):
                if sudoku[i][j] != 0:
                    self.celulas[i][j].setReadOnly(True)
                else:
                    self.celulas[i][j].setReadOnly(False)
        self.atualizar_estilo()
        self.limpar_simulacao()
        self.label_status.setText("Sudoku aleatório gerado.")

    def limpar_sudoku(self):
        self.parar_animacao()
        self.sudoku_inicial = None
        for i in range(9):
            for j in range(9):
                self.celulas[i][j].clear()
                self.celulas[i][j].setReadOnly(False)
                self.celulas[i][j].setStyleSheet("""
                    QLineEdit {
                        background-color: white;
                        color: black;
                        font-weight: bold;
                        border: 1px solid #777777;
                    }
                """)
        self.limpar_simulacao()
        self.label_status.setText("Tabuleiro limpo. Digite o Sudoku desejado.")

    def limpar_simulacao(self):
        self.historico = []
        self.indice_passo = -1
        self.botao_proximo.setEnabled(False)
        self.botao_automatico.setEnabled(False)
        self.label_tempo.setText("Tempo: -")
        self.label_tentativas.setText("Tentativas: -")
        self.label_nos.setText("Nós explorados: -")
        self.label_passos.setText("Passos: -")
        self.texto_explicacao.setPlainText("Aqui aparecerá a explicação de cada passo da busca.")

    def preparar_resolucao(self):
        self.parar_animacao()
        sudoku = self.ler_interface()
        if not validaSudoku(sudoku):
            QMessageBox.warning(self, "Sudoku inválido", "O estado inicial viola as regras do Sudoku.")
        else:
            self.sudoku_inicial = copy.deepcopy(sudoku)
            sudoku_resolver = copy.deepcopy(sudoku)
            algoritmo = self.combo_algoritmo.currentText()
            self.label_status.setText("Calculando solução...")
            QApplication.processEvents()
            if algoritmo == "DFS":
                metricas = resolver_dfs(sudoku_resolver, True)
            else:
                metricas = resolver_best_first(sudoku_resolver, True)
            if not metricas["solucionado"]:
                QMessageBox.warning(self, "Sem solução", "O Sudoku é válido, mas não possui solução alcançável.")
                self.label_status.setText("Sudoku sem solução.")
            else:
                self.historico = []
                self.historico.append({
                    "tabuleiro": copy.deepcopy(self.sudoku_inicial),
                    "titulo": "Estado inicial",
                    "descricao": "Este é o estado inicial do Sudoku.\n\nClique em Próximo Passo ou Automático para acompanhar a resolução.",
                    "linha": -1,
                    "coluna": -1,
                    "tipo": "inicio"
                })
                for passo in metricas["historico"]:
                    self.historico.append(passo)
                self.indice_passo = 0
                self.preencher_interface(self.sudoku_inicial)
                for i in range(9):
                    for j in range(9):
                        self.celulas[i][j].setReadOnly(True)
                self.atualizar_estilo()
                self.atualizar_metricas(metricas)
                self.texto_explicacao.setPlainText(self.historico[0]["titulo"] + "\n\n" + self.historico[0]["descricao"])
                self.botao_proximo.setEnabled(True)
                self.botao_automatico.setEnabled(True)
                self.label_status.setText("Resolução preparada. Use Próximo Passo ou Automático.")

    def atualizar_metricas(self, metricas):
        self.label_tempo.setText("Tempo: " + "{:.6f}".format(metricas["tempo"]) + " segundos")
        self.label_tentativas.setText("Tentativas: " + str(metricas["tentativas"]))
        self.label_nos.setText("Nós explorados: " + str(metricas["nos_explorados"]))
        self.label_passos.setText("Passos: " + str(metricas["passos"]))

    def proximo_passo(self):
        if len(self.historico) > 0:
            if self.indice_passo < len(self.historico) - 1:
                self.indice_passo = self.indice_passo + 1
                passo = self.historico[self.indice_passo]
                self.preencher_interface(passo["tabuleiro"])
                self.atualizar_estilo(passo["linha"], passo["coluna"], passo["tipo"])
                texto = passo["titulo"] + "\n\n"
                texto = texto + passo["descricao"]
                texto = texto + "\n\n------------------------------"
                texto = texto + "\nPasso " + str(self.indice_passo) + " de " + str(len(self.historico) - 1)
                self.texto_explicacao.setPlainText(texto)
                self.label_status.setText("Passo " + str(self.indice_passo) + " de " + str(len(self.historico) - 1))
            else:
                self.parar_animacao()
                self.label_status.setText("Sudoku resolvido.")
                self.botao_proximo.setEnabled(False)
                self.botao_automatico.setEnabled(False)

    def alternar_automatico(self):
        if self.timer.isActive():
            self.parar_animacao()
            self.label_status.setText("Animação pausada.")
        else:
            intervalo = self.spin_velocidade.value()
            self.timer.start(intervalo)
            self.botao_automatico.setText("Pausar")
            self.label_status.setText("Animação automática em execução.")

    def parar_animacao(self):
        if self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "botao_automatico"):
            self.botao_automatico.setText("Automático")

    def comparar_algoritmos(self):
        self.parar_animacao()
        if self.sudoku_inicial is not None:
            sudoku = copy.deepcopy(self.sudoku_inicial)
        else:
            sudoku = self.ler_interface()
        if not validaSudoku(sudoku):
            QMessageBox.warning(self, "Sudoku inválido", "O estado inicial viola as regras do Sudoku.")
        else:
            sudoku_dfs = copy.deepcopy(sudoku)
            sudoku_best = copy.deepcopy(sudoku)
            self.label_status.setText("Comparando algoritmos...")
            QApplication.processEvents()
            metricas_dfs = resolver_dfs(sudoku_dfs, False)
            metricas_best = resolver_best_first(sudoku_best, False)
            if not metricas_dfs["solucionado"] or not metricas_best["solucionado"]:
                QMessageBox.warning(self, "Sem solução", "O Sudoku informado não possui solução.")
            else:
                texto = "COMPARAÇÃO DOS ALGORITMOS\n"
                texto = texto + "================================\n\n"
                texto = texto + "DFS - BUSCA CEGA\n"
                texto = texto + "--------------------------------\n"
                texto = texto + "Tempo: " + "{:.6f}".format(metricas_dfs["tempo"]) + " s\n"
                texto = texto + "Tentativas: " + str(metricas_dfs["tentativas"]) + "\n"
                texto = texto + "Nós explorados: " + str(metricas_dfs["nos_explorados"]) + "\n"
                texto = texto + "Passos: " + str(metricas_dfs["passos"]) + "\n\n"
                texto = texto + "BEST FIRST + MRV\n"
                texto = texto + "BUSCA HEURÍSTICA\n"
                texto = texto + "--------------------------------\n"
                texto = texto + "Tempo: " + "{:.6f}".format(metricas_best["tempo"]) + " s\n"
                texto = texto + "Tentativas: " + str(metricas_best["tentativas"]) + "\n"
                texto = texto + "Nós explorados: " + str(metricas_best["nos_explorados"]) + "\n"
                texto = texto + "Passos: " + str(metricas_best["passos"]) + "\n\n"
                if metricas_best["nos_explorados"] < metricas_dfs["nos_explorados"]:
                    diferenca = metricas_dfs["nos_explorados"] - metricas_best["nos_explorados"]
                    texto = texto + "A busca heurística explorou " + str(diferenca) + " nós a menos que a DFS."
                elif metricas_dfs["nos_explorados"] < metricas_best["nos_explorados"]:
                    diferenca = metricas_best["nos_explorados"] - metricas_dfs["nos_explorados"]
                    texto = texto + "A DFS explorou " + str(diferenca) + " nós a menos que a busca heurística."
                else:
                    texto = texto + "Os dois algoritmos exploraram a mesma quantidade de nós."
                self.texto_explicacao.setPlainText(texto)
                self.label_status.setText("Comparação concluída.")

def iniciar_interface():
    app = QApplication(sys.argv)
    janela = InterfaceSudoku()
    janela.show()
    sys.exit(app.exec())