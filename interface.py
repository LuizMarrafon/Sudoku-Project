import sys
import copy
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QPushButton, QComboBox, QLabel, QFrame, QMessageBox, QPlainTextEdit, QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtGui import QIntValidator, QFont, QColor
from sudoku import criar_sudoku_aleatorio
from sudoku import validaSudoku
from sudoku import BuscaCancelada
from execucao import executar

class TrabalhoSudoku(QThread):
    def __init__(self, tabuleiro, modo, algoritmo, parent=None):
        super().__init__(parent)
        self.tabuleiro = copy.deepcopy(tabuleiro)
        self.modo = modo
        self.algoritmo = algoritmo
        self.resultado = None
        self.erro = None
        self.cancelado = False

    def run(self):
        try:
            self.resultado = executar(self.tabuleiro, self.modo, self.algoritmo,
                                      self.isInterruptionRequested)
        except BuscaCancelada:
            self.cancelado = True
        except Exception as erro:
            self.erro = str(erro)


class InterfaceSudoku(QWidget):
    def __init__(self):
        super().__init__()
        self.trabalho = None
        self.fechar_apos_trabalho = False
        self.celulas = []
        self.sudoku_inicial = None
        self.historico = []
        self.indice_passo = -1
        self.algoritmo_atual = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.proximo_passo)
        self.configurar_janela()
        self.criar_interface()

    def configurar_janela(self):
        self.setWindowTitle("Sudoku IA - Busca por profundidade e Busca gulosa")
        self.resize(1450, 900)
        self.setMinimumSize(1200, 800)
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
                background-color: white;
                color: black;
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:disabled {
                background-color: #d3d3d3;
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
                border: 1px solid #888888;
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QPlainTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #777777;
            }
            QTableWidget {
                background-color: white;
                color: black;
                gridline-color: #bbbbbb;
                border: 1px solid #777777;
            }
            QHeaderView::section {
                background-color: #dddddd;
                color: black;
                font-weight: bold;
                border: 1px solid #aaaaaa;
                padding: 5px;
            }
        """)

    def criar_interface(self):
        layout_principal = QHBoxLayout()
        lado_esquerdo = QVBoxLayout()
        lado_direito = QVBoxLayout()
        titulo = QLabel("SUDOKU IA")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        lado_esquerdo.addWidget(titulo)
        subtitulo = QLabel("Busca por profundidade x Busca gulosa")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setFont(QFont("Arial", 12))
        lado_esquerdo.addWidget(subtitulo)
        layout_sudoku = QGridLayout()
        layout_sudoku.setSpacing(4)
        layout_sudoku.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for i in range(9):
            self.celulas.append([None] * 9)
        for bloco_linha in range(3):
            for bloco_coluna in range(3):
                bloco = QFrame()
                bloco.setStyleSheet("QFrame { background-color: #202020; border: 2px solid #111111; }")
                layout_bloco = QGridLayout()
                layout_bloco.setSpacing(2)
                layout_bloco.setContentsMargins(3, 3, 3, 3)
                for i in range(3):
                    for j in range(3):
                        linha = bloco_linha * 3 + i
                        coluna = bloco_coluna * 3 + j
                        campo = QLineEdit()
                        campo.setFixedSize(58, 58)
                        campo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        campo.setFont(QFont("Arial", 21, QFont.Weight.Bold))
                        campo.setMaxLength(1)
                        campo.setValidator(QIntValidator(1, 9))
                        campo.setStyleSheet("QLineEdit { background-color: white; color: black; border: 1px solid #777777; }")
                        self.celulas[linha][coluna] = campo
                        layout_bloco.addWidget(campo, i, j)
                bloco.setLayout(layout_bloco)
                layout_sudoku.addWidget(bloco, bloco_linha, bloco_coluna)
        lado_esquerdo.addLayout(layout_sudoku)
        legenda = QLabel("Cinza = inicial | Verde = avanço | Vermelho = backtracking/escolhida | Azul = célula escolhida")
        legenda.setAlignment(Qt.AlignmentFlag.AlignCenter)
        legenda.setWordWrap(True)
        lado_esquerdo.addWidget(legenda)
        grupo_config = QGroupBox("Configuração")
        layout_config = QVBoxLayout()
        linha_algoritmo = QHBoxLayout()
        linha_algoritmo.addWidget(QLabel("Algoritmo:"))
        self.combo_algoritmo = QComboBox()
        self.combo_algoritmo.addItem("Busca por profundidade")
        self.combo_algoritmo.addItem("Busca gulosa")
        linha_algoritmo.addWidget(self.combo_algoritmo)
        layout_config.addLayout(linha_algoritmo)
        linha_velocidade = QHBoxLayout()
        linha_velocidade.addWidget(QLabel("Velocidade da animação:"))
        self.spin_velocidade = QSpinBox()
        self.spin_velocidade.setRange(100, 3000)
        self.spin_velocidade.setSingleStep(100)
        self.spin_velocidade.setValue(700)
        self.spin_velocidade.setSuffix(" ms")
        linha_velocidade.addWidget(self.spin_velocidade)
        layout_config.addLayout(linha_velocidade)
        grupo_config.setLayout(layout_config)
        lado_esquerdo.addWidget(grupo_config)
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
        self.botao_comparar = QPushButton("Comparar")
        self.botao_editar = QPushButton("Editar inicial")
        self.botao_cancelar = QPushButton("Cancelar cálculo")
        self.botao_cancelar.setEnabled(False)
        self.botao_editar.clicked.connect(self.editar_inicial)
        self.botao_cancelar.clicked.connect(self.cancelar_calculo)
        self.botao_proximo.setEnabled(False)
        self.botao_automatico.setEnabled(False)
        layout_botoes2.addWidget(self.botao_proximo)
        layout_botoes2.addWidget(self.botao_automatico)
        layout_botoes2.addWidget(self.botao_comparar)
        lado_esquerdo.addLayout(layout_botoes2)
        linha_edicao = QHBoxLayout()
        linha_edicao.addWidget(self.botao_editar)
        linha_edicao.addWidget(self.botao_cancelar)
        lado_esquerdo.addLayout(linha_edicao)
        self.label_status = QLabel("Digite um Sudoku ou gere um automaticamente.")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setWordWrap(True)
        lado_esquerdo.addWidget(self.label_status)
        grupo_metricas = QGroupBox("Métricas da busca")
        layout_metricas = QGridLayout()
        self.label_tempo = QLabel("Tempo: -")
        self.label_tentativas = QLabel("Tentativas válidas: -")
        self.label_nos = QLabel("Nós avaliados: -")
        self.label_passos = QLabel("Passos da solução: -")
        layout_metricas.addWidget(self.label_tempo, 0, 0)
        layout_metricas.addWidget(self.label_tentativas, 0, 1)
        layout_metricas.addWidget(self.label_nos, 1, 0)
        layout_metricas.addWidget(self.label_passos, 1, 1)
        self.label_validacao = QLabel("Validação prévia: -")
        layout_metricas.addWidget(self.label_validacao, 2, 0, 1, 2)
        grupo_metricas.setLayout(layout_metricas)
        lado_direito.addWidget(grupo_metricas)
        self.label_passo = QLabel("ESTADO INICIAL")
        self.label_passo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_passo.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        lado_direito.addWidget(self.label_passo)
        self.grupo_opcoes = QGroupBox("Análise")
        layout_opcoes = QVBoxLayout()
        self.tabela_opcoes = QTableWidget()
        self.tabela_opcoes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_opcoes.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabela_opcoes.verticalHeader().setVisible(False)
        self.tabela_opcoes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_opcoes.setMaximumHeight(260)
        layout_opcoes.addWidget(self.tabela_opcoes)
        self.grupo_opcoes.setLayout(layout_opcoes)
        lado_direito.addWidget(self.grupo_opcoes)
        self.grupo_fronteira = QGroupBox("Busca gulosa - Fila de prioridade")
        layout_fronteira = QVBoxLayout()
        explicacao_tabela = QLabel("Fila do menor H para o maior. Vermelho: próximo nó. Nós antigos permanecem até serem explorados.")
        explicacao_tabela.setWordWrap(True)
        layout_fronteira.addWidget(explicacao_tabela)
        self.label_fila = QLabel("Fila aguardando início da busca.")
        self.label_fila.setWordWrap(True)
        layout_fronteira.addWidget(self.label_fila)
        self.tabela_fronteira = QTableWidget()
        self.tabela_fronteira.setColumnCount(7)
        self.tabela_fronteira.setHorizontalHeaderLabels(["Posição", "Nó", "Pai", "Movimento", "H", "Vazios", "Situação"])
        self.tabela_fronteira.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela_fronteira.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabela_fronteira.verticalHeader().setVisible(False)
        self.tabela_fronteira.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_fronteira.setMinimumHeight(190)
        self.tabela_fronteira.setMaximumHeight(240)
        layout_fronteira.addWidget(self.tabela_fronteira)
        self.grupo_fronteira.setLayout(layout_fronteira)
        lado_direito.addWidget(self.grupo_fronteira)
        grupo_decisao = QGroupBox("Explicação da Decisão")
        layout_decisao = QVBoxLayout()
        self.texto_decisao = QPlainTextEdit()
        self.texto_decisao.setReadOnly(True)
        self.texto_decisao.setFont(QFont("Consolas", 10))
        self.texto_decisao.setMinimumHeight(150)
        layout_decisao.addWidget(self.texto_decisao)
        grupo_decisao.setLayout(layout_decisao)
        lado_direito.addWidget(grupo_decisao)
        layout_principal.addLayout(lado_esquerdo, 5)
        layout_principal.addLayout(lado_direito, 7)
        self.setLayout(layout_principal)
        self.botao_gerar.clicked.connect(self.gerar_sudoku)
        self.botao_limpar.clicked.connect(self.limpar_sudoku)
        self.botao_resolver.clicked.connect(self.preparar_resolucao)
        self.botao_proximo.clicked.connect(self.proximo_passo)
        self.botao_automatico.clicked.connect(self.alternar_automatico)
        self.botao_comparar.clicked.connect(self.comparar_algoritmos)
        self.grupo_fronteira.hide()
        self.limpar_tabelas()

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

    def contar_vazios_interface(self, sudoku):
        quantidade = 0
        for i in range(9):
            for j in range(9):
                if sudoku[i][j] == 0:
                    quantidade = quantidade + 1
        return quantidade

    def atualizar_estilo(self, linha_destaque=-1, coluna_destaque=-1, tipo=""):
        for i in range(9):
            for j in range(9):
                fixa = False
                if self.sudoku_inicial is not None:
                    if self.sudoku_inicial[i][j] != 0:
                        fixa = True
                if fixa:
                    estilo = "QLineEdit { background-color: #d6d6d6; color: black; font-weight: bold; border: 1px solid #555555; }"
                else:
                    estilo = "QLineEdit { background-color: white; color: black; font-weight: bold; border: 1px solid #777777; }"
                if i == linha_destaque and j == coluna_destaque:
                    if tipo == "remover":
                        estilo = "QLineEdit { background-color: #ff9e9e; color: black; font-weight: bold; border: 3px solid #c00000; }"
                    elif tipo == "mrv":
                        estilo = "QLineEdit { background-color: #9ed0ff; color: black; font-weight: bold; border: 3px solid #0066cc; }"
                    else:
                        estilo = "QLineEdit { background-color: #a8e6a3; color: black; font-weight: bold; border: 3px solid #218838; }"
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
        self.limpar_simulacao()
        self.atualizar_estilo()
        self.label_status.setText("Sudoku aleatório gerado.")

    def limpar_sudoku(self):
        self.parar_animacao()
        self.sudoku_inicial = None
        for i in range(9):
            for j in range(9):
                self.celulas[i][j].clear()
                self.celulas[i][j].setReadOnly(False)
                self.celulas[i][j].setStyleSheet("QLineEdit { background-color: white; color: black; font-weight: bold; border: 1px solid #777777; }")
        self.limpar_simulacao()
        self.label_status.setText("Tabuleiro limpo.")

    def limpar_tabelas(self):
        self.tabela_opcoes.clear()
        self.tabela_opcoes.setRowCount(0)
        self.tabela_opcoes.setColumnCount(4)
        self.tabela_opcoes.setHorizontalHeaderLabels(["Número", "Resultado", "Linha", "Coluna"])
        self.label_fila.setText("Fila aguardando início da busca.")
        self.tabela_fronteira.clearContents()
        self.tabela_fronteira.setRowCount(0)
        self.tabela_fronteira.setColumnCount(7)
        self.tabela_fronteira.setHorizontalHeaderLabels(["Posição", "Nó", "Pai", "Movimento", "H", "Vazios", "Situação"])

    def limpar_simulacao(self):
        self.historico = []
        self.indice_passo = -1
        self.botao_proximo.setEnabled(False)
        self.botao_automatico.setEnabled(False)
        self.label_tempo.setText("Tempo: -")
        self.label_tentativas.setText("Tentativas válidas: -")
        self.label_nos.setText("Nós avaliados: -")
        self.label_passos.setText("Passos da solução: -")
        self.label_validacao.setText("Validação prévia: -")
        self.label_passo.setText("ESTADO INICIAL")
        self.texto_decisao.setPlainText("Aqui aparecerá a explicação da decisão tomada pelo algoritmo.")
        self.limpar_tabelas()
        self.grupo_fronteira.hide()

    def preparar_resolucao(self):
        self.iniciar_trabalho("resolver")

    def editar_inicial(self):
        self.parar_animacao()
        if self.historico and self.sudoku_inicial is not None:
            self.preencher_interface(self.sudoku_inicial)
        self.sudoku_inicial = None
        self.limpar_simulacao()
        for linha in self.celulas:
            for campo in linha:
                campo.setReadOnly(False)
        self.atualizar_estilo()
        self.label_status.setText("Edite o estado inicial e prepare ou compare novamente.")

    def iniciar_trabalho(self, modo):
        if self.trabalho is not None:
            return
        self.parar_animacao()
        # Na reprodução, comparar/reiniciar usa explicitamente o original.
        # Fora dela, todas as edições visíveis entram na validação.
        sudoku = (copy.deepcopy(self.sudoku_inicial) if self.historico
                  else self.ler_interface())
        self.preencher_interface(sudoku)
        self.limpar_simulacao()
        self.sudoku_inicial = copy.deepcopy(sudoku)
        self.algoritmo_atual = self.combo_algoritmo.currentText()
        self.label_status.setText("Validando solucionabilidade e calculando... Comparação usa o estado inicial.")
        self.trabalho = TrabalhoSudoku(sudoku, modo, self.algoritmo_atual, self)
        self.trabalho.finished.connect(self.finalizar_trabalho)
        self.definir_ocupado(True)
        self.trabalho.start()

    def definir_ocupado(self, ocupado):
        for botao in (self.botao_gerar, self.botao_limpar, self.botao_resolver,
                      self.botao_comparar, self.botao_editar, self.combo_algoritmo):
            botao.setEnabled(not ocupado)
        self.botao_cancelar.setEnabled(ocupado)
        for linha in self.celulas:
            for campo in linha:
                campo.setEnabled(not ocupado)

    def cancelar_calculo(self):
        if self.trabalho is not None:
            self.trabalho.requestInterruption()
            self.label_status.setText("Cancelando cálculo...")

    def finalizar_trabalho(self):
        trabalho = self.trabalho
        self.trabalho = None
        self.definir_ocupado(False)
        for linha in self.celulas:
            for campo in linha:
                campo.setReadOnly(False)
        trabalho.deleteLater()
        if self.fechar_apos_trabalho:
            self.close()
            return
        if trabalho.cancelado:
            self.label_status.setText("Cálculo cancelado. O estado inicial foi preservado.")
            return
        if trabalho.erro is not None:
            self.label_status.setText("Falha no cálculo.")
            QMessageBox.warning(self, "Erro", trabalho.erro)
            return
        resultado = trabalho.resultado
        validacao = resultado['validacao']
        self.label_validacao.setText(f"Validação prévia: {validacao['tempo']:.6f} s (separada da busca)")
        if not validacao['valido'] or not validacao['solucionavel']:
            titulo = "Sudoku inválido" if not validacao['valido'] else "Sem solução"
            self.label_status.setText(validacao['mensagem'])
            QMessageBox.warning(self, titulo, validacao['mensagem'])
            return
        if resultado['modo'] == 'comparar':
            self.mostrar_comparacao(resultado)
            return
        metricas = resultado['metricas']
        if not metricas['solucionado']:
            self.label_status.setText("A busca não encontrou solução.")
            return
        self.historico = [dict(tabuleiro=copy.deepcopy(self.sudoku_inicial), titulo="Estado inicial",
            descricao="Use Próximo Passo ou Automático. Comparar e Preparar usam este estado inicial; "
                      "para alterá-lo, clique em Editar inicial.", linha=-1, coluna=-1, tipo="inicio")]
        self.historico.extend(metricas['historico'])
        self.indice_passo = 0
        for linha in self.celulas:
            for campo in linha:
                campo.setReadOnly(True)
        self.atualizar_estilo()
        self.atualizar_metricas(metricas)
        self.texto_decisao.setPlainText(self.historico[0]['descricao'])
        self.label_passo.setText(f"QUADRO 0 DE {len(self.historico)-1}")
        self.botao_proximo.setEnabled(True)
        self.botao_automatico.setEnabled(True)
        self.label_status.setText("Busca preparada. Tempo inclui registro do histórico; use Comparar para medir sem histórico.")
        if self.algoritmo_atual == "Busca por profundidade":
            self.mostrar_passo_dfs(self.historico[0])
        else:
            self.mostrar_passo_heuristico(self.historico[0])

    def atualizar_metricas(self, metricas):
        self.label_tempo.setText(f"Tempo da busca: {metricas['tempo']:.6f} s")
        self.label_tentativas.setText(f"Tentativas válidas: {metricas['tentativas']}")
        self.label_nos.setText(f"Nós avaliados: {metricas['nos_explorados']}")
        self.label_passos.setText(f"Passos da solução: {metricas['passos']}")

    def closeEvent(self, event):
        if self.trabalho is not None:
            self.fechar_apos_trabalho = True
            self.cancelar_calculo()
            event.ignore()
        else:
            event.accept()

    def mostrar_passo_dfs(self, passo):
        self.grupo_opcoes.setTitle("Busca por profundidade - Tentativas na Célula")
        self.grupo_fronteira.hide()
        self.tabela_opcoes.clear()
        self.tabela_opcoes.setColumnCount(4)
        self.tabela_opcoes.setHorizontalHeaderLabels(["Número", "Resultado", "Linha", "Coluna"])
        opcoes = passo.get("opcoes", [])
        self.tabela_opcoes.setRowCount(len(opcoes))
        for i in range(len(opcoes)):
            numero = opcoes[i]["numero"]
            resultado = opcoes[i]["resultado"]
            item_numero = QTableWidgetItem(str(numero))
            item_resultado = QTableWidgetItem(resultado)
            item_linha = QTableWidgetItem(str(passo["linha"] + 1))
            item_coluna = QTableWidgetItem(str(passo["coluna"] + 1))
            if resultado == "Escolhido":
                cor = QColor("#a8e6a3")
            else:
                cor = QColor("#ffcccc")
            item_numero.setBackground(cor)
            item_resultado.setBackground(cor)
            item_linha.setBackground(cor)
            item_coluna.setBackground(cor)
            self.tabela_opcoes.setItem(i, 0, item_numero)
            self.tabela_opcoes.setItem(i, 1, item_resultado)
            self.tabela_opcoes.setItem(i, 2, item_linha)
            self.tabela_opcoes.setItem(i, 3, item_coluna)

    def mostrar_passo_heuristico(self, passo):
        self.grupo_opcoes.setTitle("Nós concorrentes - menor H primeiro")
        self.grupo_fronteira.show()
        self.tabela_opcoes.clear()
        self.tabela_opcoes.setColumnCount(5)
        self.tabela_opcoes.setHorizontalHeaderLabels(["Nó", "Pai", "Movimento", "H", "Situação"])
        concorrentes = passo.get("fronteira", [])
        self.tabela_opcoes.setRowCount(len(concorrentes))
        for i, no in enumerate(concorrentes):
            r, c, numero = no['movimento']
            valores = [no['id'], no['pai'], f"L{r+1} C{c+1}={numero}",
                       no['h'], "PRÓXIMO" if no['escolhido'] else "Pendente"]
            for j, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                if no['escolhido']:
                    item.setBackground(QColor("#ff8a8a"))
                self.tabela_opcoes.setItem(i, j, item)
        fronteira = passo.get("fronteira", [])
        atual = f"Nó explorado: {passo.get('estado_id', '-')} | H = {passo.get('h', '-')}"
        if passo['tipo'] == 'solucao':
            self.label_fila.setText(atual + " | Solução encontrada. Busca encerrada.")
        elif fronteira:
            self.label_fila.setText(atual + f" | {len(fronteira)} nós na fila. Próximo: nó {fronteira[0]['id']} (H = {fronteira[0]['h']}).")
        else:
            self.label_fila.setText(atual + " | Fila vazia.")
        self.tabela_fronteira.clearContents()
        self.tabela_fronteira.setRowCount(len(fronteira))
        for i, dado in enumerate(fronteira):
            r, c, numero = dado['movimento']
            valores = [i + 1, dado['id'], dado['pai'], f"L{r+1} C{c+1}={numero}", dado['h'],
                       dado['vazios'],
                       "PRÓXIMO" if dado['escolhido'] else "Pendente"]
            for j, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                if dado['escolhido']:
                    item.setBackground(QColor("#ff8a8a"))
                self.tabela_fronteira.setItem(i, j, item)

    def proximo_passo(self):
        if len(self.historico) > 0:
            if self.indice_passo < len(self.historico) - 1:
                self.indice_passo = self.indice_passo + 1
                passo = self.historico[self.indice_passo]
                self.preencher_interface(passo["tabuleiro"])
                self.atualizar_estilo(passo["linha"], passo["coluna"], passo["tipo"])
                self.label_passo.setText("QUADRO " + str(self.indice_passo) + " DE " + str(len(self.historico) - 1))
                self.texto_decisao.setPlainText(passo["titulo"] + "\n\n" + passo["descricao"])
                if self.algoritmo_atual == "Busca por profundidade":
                    self.mostrar_passo_dfs(passo)
                else:
                    self.mostrar_passo_heuristico(passo)
                self.label_status.setText("Passo " + str(self.indice_passo) + " de " + str(len(self.historico) - 1))
            else:
                self.parar_animacao()
                self.botao_proximo.setEnabled(False)
                self.botao_automatico.setEnabled(False)
                self.label_status.setText("Sudoku resolvido.")

    def alternar_automatico(self):
        if self.timer.isActive():
            self.parar_animacao()
            self.label_status.setText("Animação pausada.")
        else:
            self.timer.start(self.spin_velocidade.value())
            self.botao_automatico.setText("Pausar")
            self.label_status.setText("Animação automática em execução.")

    def parar_animacao(self):
        if self.timer.isActive():
            self.timer.stop()
        if hasattr(self, "botao_automatico"):
            self.botao_automatico.setText("Automático")

    def comparar_algoritmos(self):
        self.iniciar_trabalho("comparar")

    def mostrar_comparacao(self, resultado):
        texto = "COMPARAÇÃO NO MESMO ESTADO INICIAL\nSem histórico ou animação no tempo de busca.\n\n"
        for chave, titulo in [('dfs', 'Busca por profundidade'), ('best', 'Busca gulosa')]:
            m = resultado[chave]
            texto += (f"{titulo}\nTempo: {m['tempo']:.6f} s\n"
                      f"Nós avaliados: {m['nos_explorados']}\n"
                      f"Tentativas válidas / filhos gerados: {m['tentativas']}\n"
                      f"Testes de candidatos: {m['testes_candidatos']}\n"
                      f"Passos no caminho da solução: {m['passos']}\n\n")
        texto += ("Nós avaliados incluem raiz e objetivo, uma vez por estado visitado.\n"
                  "Tentativas válidas são os sucessores gerados, sem contar a raiz.\n"
                  "Passos da solução contam apenas os preenchimentos do caminho final.\n"
                  "Testes de candidatos incluem as avaliações de domínios na heurística.\n"
                  "A validação prévia é medida separadamente.")
        self.texto_decisao.setPlainText(texto)
        self.label_passo.setText("COMPARAÇÃO DOS ALGORITMOS")
        self.label_status.setText("Comparação concluída no estado inicial exibido. Você pode editá-lo.")


def iniciar_interface():
    app = QApplication(sys.argv)
    janela = InterfaceSudoku()
    janela.show()
    sys.exit(app.exec())