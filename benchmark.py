"""Resultados reproduzíveis sem histórico: python benchmark.py --saida resultados.json."""
import argparse
import copy
import hashlib
import json
import platform
import statistics
from pathlib import Path
from sudoku import validar_estado_inicial
from dfs import resolver_dfs
from heuristica import resolver_best_first
from test_sudoku import CLASSICO, QUASE, SOLUCAO, SEM_SOLUCAO, INVALIDO


def medir(repeticoes=5):
    casos = {'Quase completo': QUASE, 'Clássico': CLASSICO, 'Completo': SOLUCAO,
             'Sem solução': SEM_SOLUCAO, 'Inválido': INVALIDO}
    resultados = []
    for nome, entrada in casos.items():
        validacoes = [validar_estado_inicial(entrada) for _ in range(repeticoes)]
        v = dict(validacoes[-1])
        v['tempos'] = [x['tempo'] for x in validacoes]
        v['tempo'] = statistics.median(v['tempos'])
        item = dict(caso=nome, tabuleiro=entrada, validacao=v, buscas={})
        if v['solucionavel']:
            for rotulo, solver in [('Busca por profundidade', resolver_dfs), ('Busca gulosa', resolver_best_first)]:
                execucoes = [solver(copy.deepcopy(entrada), False) for _ in range(repeticoes)]
                m = dict(execucoes[-1])
                m.pop('historico')
                m['tempos'] = [x['tempo'] for x in execucoes]
                m['tempo'] = statistics.median(m['tempos'])
                item['buscas'][rotulo] = m
        resultados.append(item)
    arquivos = ['main.py', 'sudoku.py', 'dfs.py', 'heuristica.py', 'interface.py', 'execucao.py']
    pasta = Path(__file__).parent
    return dict(python=platform.python_version(), sistema=platform.platform(),
                repeticoes=repeticoes, resultados=resultados,
                hashes={n: hashlib.sha256((pasta/n).read_bytes()).hexdigest() for n in arquivos})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--saida', default='resultados.json')
    args = parser.parse_args()
    dados = medir()
    Path(args.saida).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in dados['resultados']:
        print(item['caso'], 'validação', f"{item['validacao']['tempo']:.6f} s")
        for nome, m in item['buscas'].items():
            print(nome, f"{m['tempo']:.6f} s", 'nós', m['nos_explorados'], 'filhos', m['tentativas'], 'passos', m['passos'])
