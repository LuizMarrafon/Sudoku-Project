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
# Tabuleiros fixos permitem repetir a comparação com as mesmas entradas.
# Cada caractere vira um inteiro; 0 representa uma célula vazia.
CLASSICO = [[int(n) for n in linha] for linha in [
    '530070000', '600195000', '098000060', '800060003', '400803001',
    '700020006', '060000280', '000419005', '000080079']]
SOLUCAO = [[int(n) for n in linha] for linha in [
    '534678912', '672195348', '198342567', '859761423', '426853791',
    '713924856', '961537284', '287419635', '345286179']]
# A cópia evita modificar a solução conhecida. Apagar a diagonal cria nove vazios.
QUASE = copy.deepcopy(SOLUCAO)
for i in range(9):
    QUASE[i][i] = 0
# Este 1 não repete nenhuma pista, mas impede uma solução completa.
# Já o 5 do caso INVALIDO repete uma pista na primeira linha.
SEM_SOLUCAO = copy.deepcopy(CLASSICO)
SEM_SOLUCAO[0][2] = 1
INVALIDO = copy.deepcopy(CLASSICO)
INVALIDO[0][2] = 5



# Executa as medições sem abrir a interface. O padrão é repetir cada caso cinco vezes.
def medir(repeticoes=5):
    casos = {'Quase completo': QUASE, 'Clássico': CLASSICO, 'Completo': SOLUCAO,
             'Sem solução': SEM_SOLUCAO, 'Inválido': INVALIDO}
    resultados = []
    for nome, entrada in casos.items():
        # A validação tem um tempo separado: ela não entra no tempo dos algoritmos.
        validacoes = [validar_estado_inicial(entrada) for _ in range(repeticoes)]
        v = dict(validacoes[-1])
        v['tempos'] = [x['tempo'] for x in validacoes]
        # A mediana é o valor central dos tempos ordenados e reduz a influência de medições isoladas.
        v['tempo'] = statistics.median(v['tempos'])
        item = dict(caso=nome, tabuleiro=entrada, validacao=v, buscas={})
        # Entradas sem solução ou inválidas ficam registradas, mas não iniciam as buscas.
        if v['solucionavel']:
            for rotulo, solver in [('Busca por profundidade', resolver_dfs), ('Busca gulosa', resolver_best_first)]:
                # Cada execução recebe uma cópia nova, pois o solver preenche o tabuleiro recebido.
                # False desliga o histórico, evitando medir o custo da animação junto da busca.
                execucoes = [solver(copy.deepcopy(entrada), False) for _ in range(repeticoes)]
                # Mantém os contadores da última execução e guarda todos os tempos para conferência.
                m = dict(execucoes[-1])
                m.pop('historico')
                m['tempos'] = [x['tempo'] for x in execucoes]
                m['tempo'] = statistics.median(m['tempos'])
                item['buscas'][rotulo] = m
        resultados.append(item)
    # O hash funciona como uma assinatura do conteúdo de cada arquivo.
    # Permite identificar a versão do código usada nessas medições; não mede desempenho.
    arquivos = ['main.py', 'sudoku.py', 'dfs.py', 'heuristica.py', 'interface.py', 'execucao.py', 'pilha.py', 'no_pilha.py']
    pasta = Path(__file__).parent
    return dict(python=platform.python_version(), sistema=platform.platform(),
                repeticoes=repeticoes, resultados=resultados,
                hashes={n: hashlib.sha256((pasta/n).read_bytes()).hexdigest() for n in arquivos})


# Este bloco só roda ao executar este arquivo diretamente, não ao importá-lo.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # --saida permite escolher o nome do arquivo que receberá os resultados.
    parser.add_argument('--saida', default='resultados.json')
    args = parser.parse_args()
    dados = medir()
    # JSON guarda tabuleiros, métricas e tempos em um arquivo que pode ser consultado depois.
    Path(args.saida).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in dados['resultados']:
        print(item['caso'], 'validação', f"{item['validacao']['tempo']:.6f} s")
        for nome, m in item['buscas'].items():
            print(nome, f"{m['tempo']:.6f} s", 'nós', m['nos_explorados'], 'filhos', m['tentativas'], 'passos', m['passos'])
