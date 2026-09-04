import copy
import time
from sudoku import validaNumero

def candidatos(sudoku, linha, coluna):
    numeros = []
    for numero in range(1, 10):
        if validaNumero(sudoku, linha, coluna, numero):
            numeros.append(numero)
    return numeros

def contar_vazios(sudoku):
    quantidade = 0
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                quantidade = quantidade + 1
    return quantidade

def encontra_mrv(sudoku):
    melhor_linha = -1
    melhor_coluna = -1
    melhores_numeros = []
    menor_quantidade = 10
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                numeros = candidatos(sudoku, i, j)
                if len(numeros) < menor_quantidade:
                    menor_quantidade = len(numeros)
                    melhor_linha = i
                    melhor_coluna = j
                    melhores_numeros = numeros
    return melhor_linha, melhor_coluna, melhores_numeros

def calcula_heuristica(sudoku):
    vazios = 0
    total_possibilidades = 0
    impossivel = False
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                vazios = vazios + 1
                numeros = candidatos(sudoku, i, j)
                total_possibilidades = total_possibilidades + len(numeros)
                if len(numeros) == 0:
                    impossivel = True
    if impossivel:
        valor = 100000 + vazios
    else:
        valor = (vazios * 10) + total_possibilidades
    return valor

def gerar_texto_mrv(sudoku, linha_escolhida, coluna_escolhida):
    texto = "CÉLULAS ANALISADAS PELO MRV:\n\n"
    for i in range(9):
        for j in range(9):
            if sudoku[i][j] == 0:
                numeros = candidatos(sudoku, i, j)
                texto = texto + "L" + str(i + 1) + " C" + str(j + 1) + " -> " + str(numeros) + " -> " + str(len(numeros)) + " possibilidade(s)"
                if i == linha_escolhida and j == coluna_escolhida:
                    texto = texto + "   <-- ESCOLHIDA"
                texto = texto + "\n"
    return texto

def resolver_best_first(sudoku, registrar_passos=False):
    inicio = time.perf_counter()
    fronteira = []
    nos_explorados = 0
    tentativas = 0
    passos = 0
    solucionado = False
    solucao = None
    historico = []
    estado_inicial = copy.deepcopy(sudoku)
    fronteira.append({
        "estado": estado_inicial,
        "movimento": None,
        "heuristica": calcula_heuristica(estado_inicial)
    })
    while len(fronteira) > 0 and not solucionado:
        melhor_indice = 0
        melhor_valor = fronteira[0]["heuristica"]
        for i in range(1, len(fronteira)):
            valor = fronteira[i]["heuristica"]
            if valor < melhor_valor:
                melhor_valor = valor
                melhor_indice = i
        escolhido = fronteira.pop(melhor_indice)
        estado = escolhido["estado"]
        movimento_escolhido = escolhido["movimento"]
        nos_explorados = nos_explorados + 1
        linha, coluna, numeros = encontra_mrv(estado)
        if linha == -1:
            solucionado = True
            solucao = estado
            if registrar_passos:
                historico.append({
                    "tabuleiro": copy.deepcopy(estado),
                    "titulo": "Best First + MRV - Solução",
                    "descricao": "Não existem mais células vazias. O Sudoku foi resolvido.",
                    "linha": -1,
                    "coluna": -1,
                    "tipo": "solucao"
                })
        else:
            opcoes_geradas = []
            for numero in numeros:
                tentativas = tentativas + 1
                novo_estado = copy.deepcopy(estado)
                novo_estado[linha][coluna] = numero
                h = calcula_heuristica(novo_estado)
                item = {
                    "estado": novo_estado,
                    "movimento": (linha, coluna, numero),
                    "heuristica": h
                }
                fronteira.append(item)
                opcoes_geradas.append(item)
                passos = passos + 1
            if registrar_passos:
                descricao = ""
                if movimento_escolhido is None:
                    descricao = descricao + "ESTADO INICIAL ESCOLHIDO.\n\n"
                else:
                    descricao = descricao + "BEST FIRST ESCOLHEU NA FRONTEIRA:\n"
                    descricao = descricao + "Número " + str(movimento_escolhido[2]) + " em L" + str(movimento_escolhido[0] + 1) + " C" + str(movimento_escolhido[1] + 1) + "\n"
                    descricao = descricao + "h = " + str(melhor_valor) + "\n\n"
                descricao = descricao + gerar_texto_mrv(estado, linha, coluna)
                descricao = descricao + "\nMRV ESCOLHEU:\n"
                descricao = descricao + "Linha " + str(linha + 1) + ", Coluna " + str(coluna + 1) + "\n"
                descricao = descricao + "Candidatos: " + str(numeros) + "\n"
                descricao = descricao + "Quantidade: " + str(len(numeros)) + "\n\n"
                descricao = descricao + "ESTADOS GERADOS:\n"
                if len(opcoes_geradas) == 0:
                    descricao = descricao + "Nenhum estado válido. Esse caminho morreu.\n"
                else:
                    for item in opcoes_geradas:
                        movimento = item["movimento"]
                        descricao = descricao + "Colocar " + str(movimento[2]) + " -> h = " + str(item["heuristica"]) + " | vazios = " + str(contar_vazios(item["estado"])) + "\n"
                if len(fronteira) > 0:
                    proximo_indice = 0
                    proximo_h = fronteira[0]["heuristica"]
                    for i in range(1, len(fronteira)):
                        if fronteira[i]["heuristica"] < proximo_h:
                            proximo_h = fronteira[i]["heuristica"]
                            proximo_indice = i
                    proximo = fronteira[proximo_indice]
                    descricao = descricao + "\nPRÓXIMO MELHOR ESTADO NA FRONTEIRA:\n"
                    if proximo["movimento"] is not None:
                        descricao = descricao + "Colocar " + str(proximo["movimento"][2]) + " em L" + str(proximo["movimento"][0] + 1) + " C" + str(proximo["movimento"][1] + 1) + "\n"
                    descricao = descricao + "h = " + str(proximo_h)
                historico.append({
                    "tabuleiro": copy.deepcopy(estado),
                    "titulo": "Best First + MRV - Análise",
                    "descricao": descricao,
                    "linha": linha,
                    "coluna": coluna,
                    "tipo": "mrv"
                })
    fim = time.perf_counter()
    tempo = fim - inicio
    if solucionado:
        for i in range(9):
            for j in range(9):
                sudoku[i][j] = solucao[i][j]
    metricas = {
        "solucionado": solucionado,
        "tempo": tempo,
        "tentativas": tentativas,
        "nos_explorados": nos_explorados,
        "passos": passos,
        "historico": historico
    }
    return metricas