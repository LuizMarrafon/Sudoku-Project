"""Busca gulosa: prioridade h, desempate pela ordem de inserção."""
import copy
import heapq
import time
from sudoku import validaNumero, validaSudoku, verificar_cancelamento


# Lista os números de 1 a 9 que não repetem valores na linha, coluna ou bloco desta célula.
def candidatos(sudoku, linha, coluna):
    return [n for n in range(1, 10) if validaNumero(sudoku, linha, coluna, n)]


# Conta os zeros, que representam posições ainda não preenchidas.
def contar_vazios(sudoku):
    return sum(linha.count(0) for linha in sudoku)


# Domínio é a lista de candidatos de uma célula vazia. Cada item guarda linha, coluna e lista.
def analisar_estado(sudoku):
    dominios = [(r, c, candidatos(sudoku, r, c))
                for r in range(9) for c in range(9) if sudoku[r][c] == 0]
    # H avalia o tabuleiro inteiro, não uma célula isolada. Menor H tem maior prioridade.
    # O peso 10 favorece preenchimento; a soma dos domínios considera as possibilidades restantes.
    # Um domínio vazio indica contradição e recebe a penalidade 100000.
    h = (100000 + len(dominios) if any(not nums for _, _, nums in dominios)
         else 10 * len(dominios) + sum(len(nums) for _, _, nums in dominios))
    return h, dominios


# Devolve apenas H; analisar_estado também devolve os domínios calculados.
def calcula_heuristica(sudoku):
    return analisar_estado(sudoku)[0]


# MRV escolhe a célula com menos candidatos. Em empate, mantém a primeira na ordem de leitura.
# Esta função é auxiliar; o solver abaixo reutiliza os domínios já guardados no nó.
def encontra_mrv(sudoku):
    dominios = analisar_estado(sudoku)[1]
    return min(dominios, key=lambda item: len(item[2])) if dominios else (-1, -1, [])


# Busca gulosa: escolhe o menor H entre todos os nós pendentes da fronteira.
# Não soma custo acumulado ao H; portanto, não é A*.
def resolver_best_first(sudoku, registrar_passos=False, cancelar=None):
    inicio = time.perf_counter()
    verificar_cancelamento(cancelar)
    if not validaSudoku(sudoku):
        raise ValueError("Estado inicial inválido.")
    estado = copy.deepcopy(sudoku)
    h, dominios = analisar_estado(estado)
    # O identificador distingue os nós; pai indica qual nó originou este estado.
    # Profundidade conta preenchimentos; movimento registra a última atribuição.
    raiz = dict(id=0, pai=None, estado=estado, movimento=None, profundidade=0,
                h=h, dominios=dominios)
    # Cada item do heap é (H, ordem de inserção, nó).
    # O segundo valor desempata H iguais e evita comparar os dicionários dos nós.
    fronteira = [(h, 0, raiz)]
    historico = []
    gerados = explorados = 0
    # Cada domínio verifica os nove números. Conta esse trabalho, inclusive o cálculo inicial.
    testes = 9 * len(dominios)
    solucao = None
    while fronteira:
        verificar_cancelamento(cancelar)
        # Remove o menor H da fronteira global, incluindo alternativas geradas em iterações anteriores.
        _, _, no = heapq.heappop(fronteira)
        explorados += 1
        estado, dominios = no['estado'], no['dominios']
        # Sem células vazias, o nó retirado é uma solução completa.
        if not dominios:
            solucao = estado
            if registrar_passos:
                historico.append(dict(tabuleiro=copy.deepcopy(estado), titulo="Busca gulosa - Solução",
                    descricao=f"Estado {no['id']} retirado da fronteira. Tabuleiro completo e válido.",
                    linha=-1, coluna=-1, tipo="solucao", mrv=[], fronteira=[],
                    estado_id=no['id'], pai_id=no['pai'], h=no['h']))
            break
        # São duas decisões diferentes: H escolhe o nó; o menor domínio escolhe a célula nesse nó.
        # Somente os candidatos dessa célula geram filhos concorrentes.
        # Se o domínio escolhido estiver vazio, o laço seguinte não cria filhos.
        linha, coluna, numeros = min(dominios, key=lambda item: len(item[2]))
        filhos_exibidos = []
        for numero in numeros:
            verificar_cancelamento(cancelar)
            filho = copy.deepcopy(estado)
            filho[linha][coluna] = numero
            # Calcula H e domínios uma vez por filho e guarda ambos para reutilização.
            h_filho, dominios_filho = analisar_estado(filho)
            testes += 9 * len(dominios_filho)
            gerados += 1
            novo = dict(id=gerados, pai=no['id'], estado=filho,
                        movimento=(linha, coluna, numero), profundidade=no['profundidade']+1,
                        h=h_filho, dominios=dominios_filho)
            # O filho entra junto dos nós pendentes; a próxima retirada pode escolher um nó antigo.
            heapq.heappush(fronteira, (h_filho, gerados, novo))
            if registrar_passos:
                filhos_exibidos.append(dict(id=gerados, linha=linha, coluna=coluna,
                                           numero=numero, h=h_filho))
        if registrar_passos:
            # Fila completa da fronteira REAL depois de inserir todos os filhos.
            topo = []
            # O heap garante o menor no topo, mas não é uma lista totalmente ordenada.
            # sorted cria uma visão ordenada para a tela, sem mudar a estrutura usada pela busca.
            for indice, (_, _, pendente) in enumerate(sorted(fronteira)):
                topo.append(dict(id=pendente['id'], pai=pendente['pai'],
                    movimento=pendente['movimento'], h=pendente['h'],
                    profundidade=pendente['profundidade'], vazios=len(pendente['dominios']),
                    escolhido=indice == 0))
            # Dados de apoio à explicação visual; não participam da escolha de prioridades.
            analise = [dict(linha=r, coluna=c, candidatos=nums, quantidade=len(nums),
                            escolhido=(r, c) == (linha, coluna)) for r, c, nums in dominios]
            descricao = (f"Estado {no['id']} retirado da fronteira global; h = {no['h']}.\n"
                         f"Célula escolhida: L{linha+1} C{coluna+1}, candidatos {numeros}.\n"
                         f"Foram gerados {len(numeros)} sucessores.\n"
                         f"Fronteira após a expansão: {len(fronteira)} estados pendentes.\n"
                         "A fila mostra todos os nós pendentes, do menor H para o maior. Empates seguem a ordem de chegada.\n"
                         "As tabelas mostram somente os nós pendentes que realmente concorrem. O menor H da fila é o próximo.\n"
                         "PRÓXIMO indica o estado retirado na próxima iteração.\n"
                         "Cada linha é um estado completo; mudanças de ramo podem alterar várias células.")
            historico.append(dict(tabuleiro=copy.deepcopy(estado), titulo="Busca gulosa",
                descricao=descricao, linha=linha, coluna=coluna, tipo="mrv", mrv=analise,
                filhos=filhos_exibidos, fronteira=topo, estado_id=no['id'], pai_id=no['pai'], h=no['h']))
    # Atualiza a entrada somente depois do sucesso, preservando-a em caso de falha ou cancelamento.
    if solucao is not None:
        for i in range(9):
            sudoku[i][:] = solucao[i]
    # Raiz e objetivo contam como nós explorados. Filhos ainda pendentes contam apenas como gerados.
    return dict(solucionado=solucao is not None, tempo=time.perf_counter()-inicio,
                tentativas=gerados, estados_gerados=gerados, nos_explorados=explorados,
                passos=contar_vazios(raiz['estado']) if solucao is not None else None,
                testes_candidatos=testes, historico=historico)
