# Sudoku Project

Sistema de resolução de Sudoku com busca por profundidade com pilha e Best First gulosa com MRV (busca heurística), interface PySide6, validação prévia e comparação de desempenho.

## Instalação no Windows

Versão testada: Python 3.14.7 e PySide6 6.11.2. No PowerShell, dentro desta pasta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Se o ambiente `.venv` já estiver configurado, basta executar o último comando.

## Uso

1. Digite os números de 1 a 9, deixando as células vazias sem texto, ou clique em **Gerar Sudoku**.
2. Escolha DFS ou Best First + MRV e clique em **Preparar Resolução**.
3. O sistema verifica conflitos e solucionabilidade antes de iniciar a busca selecionada. Entradas inválidas ou insolúveis mostram um aviso e não iniciam essa busca.
4. Use **Próximo Passo** ou **Automático** para reproduzir o histórico. O tempo exibido inclui o registro desse histórico, mas não sua reprodução.
5. Use **Comparar** para medir os dois algoritmos sobre cópias do mesmo estado inicial, sem histórico. A validação é cronometrada separadamente.
6. Durante a reprodução, **Comparar** e uma nova preparação reutilizam o estado inicial da simulação, não o quadro parcialmente resolvido. Use **Editar inicial** para restaurar e modificar esse tabuleiro. Fora da reprodução, a comparação considera todas as edições visíveis.
7. **Cancelar cálculo** interrompe a validação ou as buscas e preserva a entrada. O cálculo ocorre em QThread para manter a interface responsiva. Fechar a janela também solicita cancelamento antes de encerrar.

## Modelagem e algoritmos

O estado é uma matriz 9 × 9 de inteiros, com 0 para vazio. Uma ação atribui um candidato permitido a uma célula vazia. A transição preserva as demais posições. O objetivo é uma matriz completa válida; as pistas iniciais não são alteradas.

- **Busca por profundidade:** pilha encadeada com push, pop e isEmpty. Cada NoPilha guarda apenas o tabuleiro e a ligação para o próximo nó. Expande a primeira célula vazia e empilha candidatos do 9 ao 1 para explorar o menor primeiro. Ao esgotar um ramo, retira a próxima alternativa pendente. Não usa heurística.
- **Best First:** fila de prioridade global (`heapq`), menor h primeiro, empate pela ordem de inserção. MRV escolhe a célula com menos candidatos; empate pela ordem de linhas e colunas. Todos os candidatos da célula escolhida geram filhos.
- **Heurística:** `h = 10 * vazios + soma_dos_tamanhos_dos_dominios`. Se uma célula vazia não tiver candidatos, `h = 100000 + vazios`. Esses estados ficam penalizados e não produzem filhos ao serem avaliados. É busca gulosa, não A*: não soma custo acumulado g.
- **Validação prévia:** backtracking MRV independente, silencioso e sem histórico, para provar existência de solução. Verificar solucionabilidade pode exigir uma busca interna; o que é impedido para entradas insolúveis é iniciar as buscas de demonstração/comparação. Essa distinção evita afirmar que a existência de solução é decidida apenas conferindo repetições.

A tabela **Fronteira real** mostra os cinco primeiros estados pendentes depois da expansão, com identificadores de estado/pai e prioridade. **PRÓXIMO** corresponde ao estado que será retirado na próxima iteração. O movimento é a última atribuição que criou aquele estado; cada linha representa um tabuleiro completo. Uma mudança de ramo pode alterar várias células do quadro seguinte.

## Métricas comuns

| Métrica | Definição nos dois algoritmos |
|---|---|
| Nós avaliados | Estados visitados pela busca, incluindo raiz e objetivo, uma vez por nó da árvore. Retornar ao pai na DFS não conta novamente. |
| Tentativas válidas / estados gerados | Atribuições legais que criam filhos; não inclui a raiz. |
| Testes de candidatos | Chamadas a validaNumero para verificar números durante a busca; inclui cálculo de domínios e h na Best First. Exclui a validação da entrada. |
| Passos da solução | Preenchimentos do caminho final, iguais ao número inicial de vazios quando há solução. Sem solução: None. |
| Tempo da busca | Preparação interna, execução e cópia da solução; inclui histórico somente se solicitado. A validação de solucionabilidade é medida à parte. |

Os **quadros** da animação e as operações totais da DFS não são os passos do caminho final. Testar todos os domínios tem custo: menos nós não garante menor tempo em qualquer tabuleiro.

## Testes e medições

```powershell
.\.venv\Scripts\python.exe benchmark.py --saida resultados.json
```

Os testes verificam soluções/pistas, métricas, entradas inválidas, insolubilidade, bloqueio dos solvers pela validação, fronteira real com ramificações, cancelamento e fluxos gráficos em Qt offscreen. O benchmark usa cinco repetições, mediana do tempo, cópias novas e nenhum histórico. Entradas inválidas e insolúveis param na validação.

## Arquivos

- `sudoku.py`: regras, geração e validação independente.
- `dfs.py` e `heuristica.py`: buscas.
- `pilha.py`: Pilha usada pela busca por profundidade.
- `no_pilha.py`: nó com tabuleiro e ligação para o próximo.
- `execucao.py`: fluxo compartilhado de validação e execução.
- `interface.py` e `main.py`: interface, execução em segundo plano e inicialização.
- `relatorio.html`: relatório para impressão ou salvamento como PDF pelo navegador.

O gerador garante pelo menos uma solução, sem garantir unicidade. Não há limite arbitrário de nós ou tempo: casos difíceis podem consumir bastante memória/tempo, especialmente com histórico; use Cancelar cálculo quando necessário. Unicidade não é exigida no enunciado.
