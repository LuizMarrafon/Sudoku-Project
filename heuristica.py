"""Busca gulosa: prioridade h, desempate pela ordem de inserção."""
import copy
import heapq
import time
from sudoku import validaNumero, validaSudoku, verificar_cancelamento


def candidatos(sudoku, linha, coluna):
    return [n for n in range(1, 10) if validaNumero(sudoku, linha, coluna, n)]


def contar_vazios(sudoku):
    return sum(linha.count(0) for linha in sudoku)


def analisar_estado(sudoku):
    dominios = [(r, c, candidatos(sudoku, r, c))
                for r in range(9) for c in range(9) if sudoku[r][c] == 0]
    h = (100000 + len(dominios) if any(not nums for _, _, nums in dominios)
         else 10 * len(dominios) + sum(len(nums) for _, _, nums in dominios))
    return h, dominios


def calcula_heuristica(sudoku):
    return analisar_estado(sudoku)[0]


def encontra_mrv(sudoku):
    dominios = analisar_estado(sudoku)[1]
    return min(dominios, key=lambda item: len(item[2])) if dominios else (-1, -1, [])


def resolver_best_first(sudoku, registrar_passos=False, cancelar=None):
    inicio = time.perf_counter()
    verificar_cancelamento(cancelar)
    if not validaSudoku(sudoku):
        raise ValueError("Estado inicial inválido.")
    estado = copy.deepcopy(sudoku)
    h, dominios = analisar_estado(estado)
    raiz = dict(id=0, pai=None, estado=estado, movimento=None, profundidade=0,
                h=h, dominios=dominios)
    fronteira = [(h, 0, raiz)]
    historico = []
    gerados = explorados = 0
    testes = 9 * len(dominios)
    solucao = None
    while fronteira:
        verificar_cancelamento(cancelar)
        _, _, no = heapq.heappop(fronteira)
        explorados += 1
        estado, dominios = no['estado'], no['dominios']
        if not dominios:
            solucao = estado
            if registrar_passos:
                historico.append(dict(tabuleiro=copy.deepcopy(estado), titulo="Busca gulosa - Solução",
                    descricao=f"Estado {no['id']} retirado da fronteira. Tabuleiro completo e válido.",
                    linha=-1, coluna=-1, tipo="solucao", mrv=[], fronteira=[],
                    estado_id=no['id'], pai_id=no['pai'], h=no['h']))
            break
        linha, coluna, numeros = min(dominios, key=lambda item: len(item[2]))
        filhos_exibidos = []
        for numero in numeros:
            verificar_cancelamento(cancelar)
            filho = copy.deepcopy(estado)
            filho[linha][coluna] = numero
            h_filho, dominios_filho = analisar_estado(filho)
            testes += 9 * len(dominios_filho)
            gerados += 1
            novo = dict(id=gerados, pai=no['id'], estado=filho,
                        movimento=(linha, coluna, numero), profundidade=no['profundidade']+1,
                        h=h_filho, dominios=dominios_filho)
            heapq.heappush(fronteira, (h_filho, gerados, novo))
            if registrar_passos:
                filhos_exibidos.append(dict(id=gerados, linha=linha, coluna=coluna,
                                           numero=numero, h=h_filho))
        if registrar_passos:
            # Fila completa da fronteira REAL depois de inserir todos os filhos.
            topo = []
            for indice, (_, _, pendente) in enumerate(sorted(fronteira)):
                topo.append(dict(id=pendente['id'], pai=pendente['pai'],
                    movimento=pendente['movimento'], h=pendente['h'],
                    profundidade=pendente['profundidade'], vazios=len(pendente['dominios']),
                    escolhido=indice == 0))
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
    if solucao is not None:
        for i in range(9):
            sudoku[i][:] = solucao[i]
    return dict(solucionado=solucao is not None, tempo=time.perf_counter()-inicio,
                tentativas=gerados, estados_gerados=gerados, nos_explorados=explorados,
                passos=contar_vazios(raiz['estado']) if solucao is not None else None,
                testes_candidatos=testes, historico=historico)
