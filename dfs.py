import copy
import time
from sudoku import validaNumero

def criar_matriz_fixos(sudoku):
    fixos = []
    for i in range(9):
        linha = []
        for j in range(9):
            if sudoku[i][j] == 0:
                linha.append(False)
            else:
                linha.append(True)
        fixos.append(linha)
    return fixos

def resolver_dfs(sudoku, registrar_passos=False):
    fixos = criar_matriz_fixos(sudoku)
    tentativas = [None] * 81
    posicao = 0
    solucionado = False
    sem_solucao = False
    quantidade_tentativas = 0
    nos_explorados = 0
    passos = 0
    historico = []
    inicio = time.perf_counter()
    while not solucionado and not sem_solucao:
        if posicao == 81:
            solucionado = True
        elif posicao < 0:
            sem_solucao = True
        else:
            linha = posicao // 9
            coluna = posicao % 9
            if fixos[linha][coluna]:
                posicao = posicao + 1
            else:
                if tentativas[posicao] is None:
                    tentativas[posicao] = list(range(1, 10))
                achouNumero = False
                while len(tentativas[posicao]) > 0 and not achouNumero:
                    numero = tentativas[posicao].pop(0)
                    quantidade_tentativas = quantidade_tentativas + 1
                    if validaNumero(sudoku, linha, coluna, numero):
                        sudoku[linha][coluna] = numero
                        achouNumero = True
                        nos_explorados = nos_explorados + 1
                        passos = passos + 1
                        if registrar_passos:
                            historico.append({
                                "tabuleiro": copy.deepcopy(sudoku),
                                "titulo": "DFS - Avanço",
                                "descricao": "Número " + str(numero) + " colocado na linha " + str(linha + 1) + ", coluna " + str(coluna + 1) + ".",
                                "linha": linha,
                                "coluna": coluna,
                                "tipo": "colocar"
                            })
                if achouNumero:
                    posicao = posicao + 1
                else:
                    sudoku[linha][coluna] = 0
                    tentativas[posicao] = None
                    posicao = posicao - 1
                    while posicao >= 0 and fixos[posicao // 9][posicao % 9]:
                        posicao = posicao - 1
                    if posicao >= 0:
                        linhaAnterior = posicao // 9
                        colunaAnterior = posicao % 9
                        numeroRemovido = sudoku[linhaAnterior][colunaAnterior]
                        sudoku[linhaAnterior][colunaAnterior] = 0
                        passos = passos + 1
                        if registrar_passos:
                            historico.append({
                                "tabuleiro": copy.deepcopy(sudoku),
                                "titulo": "DFS - Backtracking",
                                "descricao": "O caminho não funcionou. O número " + str(numeroRemovido) + " foi removido da linha " + str(linhaAnterior + 1) + ", coluna " + str(colunaAnterior + 1) + ". A DFS vai tentar outra possibilidade.",
                                "linha": linhaAnterior,
                                "coluna": colunaAnterior,
                                "tipo": "remover"
                            })
    fim = time.perf_counter()
    tempo = fim - inicio
    metricas = {
        "solucionado": solucionado,
        "tempo": tempo,
        "tentativas": quantidade_tentativas,
        "nos_explorados": nos_explorados,
        "passos": passos,
        "historico": historico
    }
    return metricas