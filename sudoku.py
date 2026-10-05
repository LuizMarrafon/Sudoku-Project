import random

def criar_sudoku_vazio():
    sudoku = []
    for i in range(9):
        linha = []
        for j in range(9):
            linha.append(0)
        sudoku.append(linha)
    return sudoku

def criar_sudoku_manual():
    sudoku = criar_sudoku_vazio()
    print("Digite os numeros do Sudoku (0 para vazio):")
    print("Formato: ele vai colocando em linha")
    for i in range(9):
        print("linha ", i + 1, "\n")
        for j in range(9):
            print("Coluna ", j + 1, "\n")
            num = int(input("Numero: "))
            sudoku[i][j] = num
    return sudoku

def validaNumero(sudoku, linha, coluna, numero):
    flag = True
    for i in range(9):
        if coluna != i and sudoku[linha][i] == numero:
            flag = False
    for i in range(9):
        if linha != i and sudoku[i][coluna] == numero:
            flag = False
    box_linha = linha - linha % 3
    box_coluna = coluna - coluna % 3
    for i in range(box_linha, box_linha + 3):
        for j in range(box_coluna, box_coluna + 3):
            if (i != linha or j != coluna) and sudoku[i][j] == numero:
                flag = False
    return flag

def criar_sudoku_aleatorio():
    sudoku = criar_sudoku_vazio()
    # guarda quais números ainda podem ser tentados em cada posição
    tentativas = [None] * 81
    posicao = 0
    while posicao >= 0 and posicao < 81:
        linha = posicao // 9
        coluna = posicao % 9
        # se é a primeira vez que chegamos nessa posição
        if tentativas[posicao] is None:
            numeros = list(range(1, 10))
            random.shuffle(numeros)
            tentativas[posicao] = numeros
        achouNumero = False
        # tenta os números disponíveis daquela posição
        while len(tentativas[posicao]) > 0 and not achouNumero:
            num = tentativas[posicao].pop()
            if validaNumero(sudoku, linha, coluna, num):
                sudoku[linha][coluna] = num
                achouNumero = True
        # conseguiu colocar um número
        if achouNumero:
            posicao = posicao + 1
            # prepara a próxima posição
            if posicao < 81:
                proximaLinha = posicao // 9
                proximaColuna = posicao % 9
                sudoku[proximaLinha][proximaColuna] = 0
                tentativas[posicao] = None
        # nenhum número funcionou
        else:
            sudoku[linha][coluna] = 0
            tentativas[posicao] = None
            # volta uma posição
            posicao = posicao - 1
            if posicao >= 0:
                linhaAnterior = posicao // 9
                colunaAnterior = posicao % 9
                sudoku[linhaAnterior][colunaAnterior] = 0
    retirar_numeros(sudoku)
    return sudoku

def retirar_numeros(sudoku):
    for box_linha in range(0, 9, 3):
        for box_coluna in range(0, 9, 3):
            quantidade = random.randint(3, 6)
            posicoes = []
            for i in range(box_linha, box_linha + 3):
                for j in range(box_coluna, box_coluna + 3):
                    posicoes.append((i, j))
            random.shuffle(posicoes)
            for i in range(quantidade):
                linha, coluna = posicoes.pop()
                sudoku[linha][coluna] = 0
    return sudoku

def exibir_sudoku(sudoku):
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print("-" * 25)
        for j in range(9):
            if j % 3 == 0 and j != 0:
                print("|", end=" ")
            print(sudoku[i][j], end=" ")
        print()

def validaSudoku(sudoku):
    if not isinstance(sudoku, (list, tuple)) or len(sudoku) != 9:
        return False
    if any(not isinstance(linha, (list, tuple)) or len(linha) != 9 for linha in sudoku):
        return False
    if any(type(numero) is not int or not 0 <= numero <= 9 for linha in sudoku for numero in linha):
        return False
    valido = True
    for i in range(9):
        for j in range(9):
            numero = sudoku[i][j]
            if numero < 0 or numero > 9:
                valido = False
            if numero != 0:
                if not validaNumero(sudoku, i, j, numero):
                    valido = False
    return valido



class BuscaCancelada(Exception):
    """Interrupção solicitada pelo usuário; não significa ausência de solução."""


def verificar_cancelamento(cancelar=None):
    if cancelar is not None and cancelar():
        raise BuscaCancelada()


def validar_estado_inicial(sudoku, cancelar=None):
    """Validação independente, sem histórico e sem alterar a entrada.

    A prova de existência usa backtracking MRV interno. Não executa nenhuma
    das buscas de demonstração e seu tempo é reportado separadamente.
    """
    import time
    inicio = time.perf_counter()
    verificar_cancelamento(cancelar)
    if not validaSudoku(sudoku):
        return {"valido": False, "solucionavel": False,
                "tempo": time.perf_counter() - inicio,
                "mensagem": "O estado inicial viola as regras do Sudoku."}
    tabuleiro = [list(linha) for linha in sudoku]

    def verificar():
        verificar_cancelamento(cancelar)
        melhor = None
        for r in range(9):
            for c in range(9):
                if tabuleiro[r][c] == 0:
                    usados = set(tabuleiro[r]) | {tabuleiro[i][c] for i in range(9)}
                    usados |= {tabuleiro[i][j] for i in range(r//3*3, r//3*3+3)
                               for j in range(c//3*3, c//3*3+3)}
                    candidatos = sorted(set(range(1, 10)) - usados)
                    if not candidatos:
                        return False
                    if melhor is None or len(candidatos) < len(melhor[2]):
                        melhor = (r, c, candidatos)
        if melhor is None:
            return True
        r, c, candidatos = melhor
        for numero in candidatos:
            tabuleiro[r][c] = numero
            if verificar():
                return True
        tabuleiro[r][c] = 0
        return False

    solucionavel = verificar()
    return {"valido": True, "solucionavel": solucionavel,
            "tempo": time.perf_counter() - inicio,
            "mensagem": "Estado válido e solucionável." if solucionavel else
                        "O Sudoku não possui solução. A busca de demonstração não foi iniciada."}
