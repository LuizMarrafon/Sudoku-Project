import copy
import time
from pilha import Pilha
from no_pilha import NoPilha
from sudoku import validaNumero, validaSudoku, verificar_cancelamento


# Busca por profundidade sem heurística: usa a ordem das células e uma pilha LIFO.
# LIFO significa que o último nó empilhado é o primeiro a ser retirado.
def resolver_dfs(sudoku, registrar_passos=False, cancelar=None):
    # O cronômetro começa antes de preparar a pilha. O histórico, se solicitado, também tem custo.
    inicio = time.perf_counter()
    verificar_cancelamento(cancelar)
    # Confere as regras das pistas; a prova de existência de solução é feita antes pelo fluxo da interface.
    if not validaSudoku(sudoku):
        raise ValueError("Estado inicial inválido.")

    # A raiz é uma cópia da entrada. Cada nó guarda um tabuleiro independente,
    # para que uma tentativa não altere os outros ramos nem a entrada durante o cálculo.
    pilha = Pilha()
    pilha.push(NoPilha(copy.deepcopy(sudoku)))
    # A quantidade inicial de vazios será o comprimento do caminho final, se houver solução.
    vazios_iniciais = sum(linha.count(0) for linha in sudoku)
    solucionado = False
    solucao = None
    # Avaliar um nó é retirá-lo da pilha; gerar um nó é criar e empilhar um filho.
    # Podem sobrar filhos na pilha quando a solução é encontrada.
    nos_explorados = 0
    estados_gerados = 0
    testes_candidatos = 0
    historico = []

    # O laço termina pelo seu próprio teste: solução encontrada ou pilha sem alternativas.
    while not pilha.isEmpty() and not solucionado:
        verificar_cancelamento(cancelar)
        # Retira o próximo estado pela ordem da pilha, sem calcular H.
        no = pilha.pop()
        estado = no.tabuleiro
        nos_explorados += 1

        # Localiza a primeira célula vazia sem interromper o laço à força.
        posicao = 0
        encontrou_vazio = False
        while posicao < 81 and not encontrou_vazio:
            # A divisão inteira encontra a linha; o resto da divisão encontra a coluna.
            # Assim, as posições 0 a 80 percorrem a matriz por linhas.
            linha = posicao // 9
            coluna = posicao % 9
            if estado[linha][coluna] == 0:
                encontrou_vazio = True
            else:
                posicao += 1

        # Sem zeros, o estado é objetivo: as pistas e cada preenchimento já respeitaram as regras.
        if not encontrou_vazio:
            solucionado = True
            solucao = estado
            # O histórico serve apenas para a interface e não muda a ordem de exploração.
            if registrar_passos:
                historico.append(dict(
                    tabuleiro=copy.deepcopy(estado),
                    titulo="Busca por profundidade - Solução encontrada",
                    descricao="O estado retirado do topo da pilha está completo e válido.",
                    linha=-1, coluna=-1, tipo="solucao", opcoes=[]))
        else:
            testes = []
            # Empilha do 9 ao 1: o menor candidato fica no topo e sai primeiro.
            for numero in range(9, 0, -1):
                verificar_cancelamento(cancelar)
                testes_candidatos += 1
                # Um movimento permitido cria um filho. Legalidade local não garante solução futura.
                valido = validaNumero(estado, linha, coluna, numero)
                if valido:
                    # Altera somente a célula vazia selecionada; as pistas já preenchidas são preservadas.
                    filho = copy.deepcopy(estado)
                    filho[linha][coluna] = numero
                    pilha.push(NoPilha(filho))
                    estados_gerados += 1
                if registrar_passos:
                    testes.append(dict(numero=numero,
                                       resultado="Empilhado" if valido else "Inválido"))
            if registrar_passos:
                # Reorganiza a tabela para mostrar 1 a 9. Isso não modifica a ordem da pilha.
                testes.reverse()
                historico.append(dict(
                    tabuleiro=copy.deepcopy(estado),
                    titulo="Busca por profundidade - Expansão do nó",
                    descricao=(f"Estado retirado do topo da pilha. Célula: L{linha+1} C{coluna+1}.\n"
                               "Os números válidos são empilhados do 9 ao 1, para explorar o menor primeiro.\n"
                               "Se nenhum número servir, a próxima iteração retira uma alternativa pendente.\n"
                               "Cada quadro mostra um estado explorado; uma troca de ramo pode alterar várias células."),
                    linha=linha, coluna=coluna, tipo="colocar", opcoes=testes))

    # Só copia o resultado para a entrada quando encontra solução.
    # Cancelamento ou ausência de solução deixam o tabuleiro recebido intacto.
    if solucionado:
        for i in range(9):
            sudoku[i][:] = solucao[i]

    # Tentativas conta filhos válidos; testes_candidatos inclui números rejeitados.
    # Passos é o comprimento da solução, não a quantidade de quadros nem de nós visitados.
    metricas = dict(
        solucionado=solucionado, tempo=time.perf_counter() - inicio,
        tentativas=estados_gerados, estados_gerados=estados_gerados,
        nos_explorados=nos_explorados,
        passos=vazios_iniciais if solucionado else None,
        testes_candidatos=testes_candidatos, historico=historico)
    return metricas
