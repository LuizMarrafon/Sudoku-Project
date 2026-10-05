import copy
import time
from sudoku import validaNumero, validaSudoku, verificar_cancelamento

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

def resolver_dfs(sudoku, registrar_passos=False, cancelar=None):
    inicio = time.perf_counter()
    verificar_cancelamento(cancelar)
    if not validaSudoku(sudoku):
        raise ValueError("Estado inicial inválido.")
    entrada = sudoku
    sudoku = copy.deepcopy(sudoku)
    vazios_iniciais = sum(linha.count(0) for linha in sudoku)
    testes_candidatos = 0
    fixos = criar_matriz_fixos(sudoku)
    tentativas = [None] * 81
    posicao = 0
    solucionado = False
    sem_solucao = False
    quantidade_tentativas = 0
    nos_explorados = 1
    passos = 0
    historico = []
    while not solucionado and not sem_solucao:
        verificar_cancelamento(cancelar)
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
                testes = []
                while len(tentativas[posicao]) > 0 and not achouNumero:
                    numero = tentativas[posicao].pop(0)
                    testes_candidatos += 1
                    if validaNumero(sudoku, linha, coluna, numero):
                        quantidade_tentativas += 1
                        testes.append({
                            "numero": numero,
                            "resultado": "Escolhido"
                        })
                        sudoku[linha][coluna] = numero
                        achouNumero = True
                        nos_explorados = nos_explorados + 1
                        passos = passos + 1
                        if registrar_passos:
                            historico.append({
                                "tabuleiro": copy.deepcopy(sudoku),
                                "titulo": "Busca por profundidade",
                                "descricao": "A busca por profundidade percorre as possibilidades em ordem e utiliza o primeiro número válido encontrado.\n\nCélula atual: L" + str(linha + 1) + " C" + str(coluna + 1) + "\nNúmero escolhido: " + str(numero),
                                "linha": linha,
                                "coluna": coluna,
                                "tipo": "colocar",
                                "opcoes": copy.deepcopy(testes)
                            })
                    else:
                        testes.append({
                            "numero": numero,
                            "resultado": "Inválido"
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
                                "titulo": "Busca por profundidade - Backtracking",
                                "descricao": "Nenhuma possibilidade levou a uma solução.\n\nA busca por profundidade voltou para a célula anterior.\nNúmero removido: " + str(numeroRemovido) + "\nCélula: L" + str(linhaAnterior + 1) + " C" + str(colunaAnterior + 1),
                                "linha": linhaAnterior,
                                "coluna": colunaAnterior,
                                "tipo": "remover",
                                "opcoes": []
                            })
    if solucionado and registrar_passos:
        historico.append({
            "tabuleiro": copy.deepcopy(sudoku),
            "titulo": "Busca por profundidade - Solução encontrada",
            "descricao": "Todas as células foram preenchidas corretamente.\n\nA busca por profundidade encontrou uma solução.",
            "linha": -1,
            "coluna": -1,
            "tipo": "solucao",
            "opcoes": []
        })
    if solucionado:
        for i in range(9):
            entrada[i][:] = sudoku[i]
    tempo = time.perf_counter() - inicio
    metricas = {
        "solucionado": solucionado,
        "tempo": tempo,
        "tentativas": quantidade_tentativas,
        "nos_explorados": nos_explorados,
        "passos": vazios_iniciais if solucionado else None,
        "operacoes": passos,
        "testes_candidatos": testes_candidatos,
        "estados_gerados": quantidade_tentativas,
        "historico": historico
    }
    return metricas