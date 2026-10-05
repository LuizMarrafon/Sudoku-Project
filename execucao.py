"""Fluxo comum: validar antes de chamar qualquer busca de demonstração."""
import copy
from sudoku import validar_estado_inicial, verificar_cancelamento
from dfs import resolver_dfs
from heuristica import resolver_best_first


def executar(sudoku, modo, algoritmo="Busca por profundidade", cancelar=None):
    validacao = validar_estado_inicial(sudoku, cancelar)
    resultado = dict(validacao=validacao, modo=modo, algoritmo=algoritmo)
    if not validacao['valido'] or not validacao['solucionavel']:
        return resultado
    verificar_cancelamento(cancelar)
    if modo == 'comparar':
        resultado['dfs'] = resolver_dfs(copy.deepcopy(sudoku), False, cancelar)
        verificar_cancelamento(cancelar)
        resultado['best'] = resolver_best_first(copy.deepcopy(sudoku), False, cancelar)
    elif modo == 'resolver':
        solver = resolver_dfs if algoritmo == 'Busca por profundidade' else resolver_best_first
        resultado['metricas'] = solver(copy.deepcopy(sudoku), True, cancelar)
    else:
        raise ValueError("Modo de execução desconhecido.")
    return resultado
