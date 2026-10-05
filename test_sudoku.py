"""Execute: python -m unittest -v test_sudoku. Qt usa modo offscreen."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import copy
import random
import time
import unittest
from unittest.mock import patch
from sudoku import validaSudoku, validar_estado_inicial, BuscaCancelada, criar_sudoku_aleatorio
from dfs import resolver_dfs
from heuristica import resolver_best_first
from execucao import executar

CLASSICO = [[int(n) for n in linha] for linha in [
    '530070000', '600195000', '098000060', '800060003', '400803001',
    '700020006', '060000280', '000419005', '000080079']]
SOLUCAO = [[int(n) for n in linha] for linha in [
    '534678912', '672195348', '198342567', '859761423', '426853791',
    '713924856', '961537284', '287419635', '345286179']]
QUASE = copy.deepcopy(SOLUCAO)
for i in range(9):
    QUASE[i][i] = 0
SEM_SOLUCAO = copy.deepcopy(CLASSICO)
SEM_SOLUCAO[0][2] = 1
INVALIDO = copy.deepcopy(CLASSICO)
INVALIDO[0][2] = 5


def conferir_solucao(test, entrada, saida):
    esperado = set(range(1, 10))
    for r in range(9):
        test.assertEqual(set(saida[r]), esperado)
        test.assertEqual({saida[c][r] for c in range(9)}, esperado)
        for c in range(9):
            if entrada[r][c]:
                test.assertEqual(entrada[r][c], saida[r][c])
    for r in (0, 3, 6):
        for c in (0, 3, 6):
            test.assertEqual({saida[i][j] for i in range(r, r+3) for j in range(c, c+3)}, esperado)


class TestBuscas(unittest.TestCase):
    def test_solucoes_e_metricas(self):
        for solver in (resolver_dfs, resolver_best_first):
            for entrada in (CLASSICO, QUASE, SOLUCAO):
                with self.subTest(solver=solver.__name__, vazios=sum(r.count(0) for r in entrada)):
                    b = copy.deepcopy(entrada)
                    m = solver(b)
                    self.assertTrue(m['solucionado'])
                    conferir_solucao(self, entrada, b)
                    self.assertEqual(m['passos'], sum(r.count(0) for r in entrada))
                    self.assertEqual(m['tentativas'], m['estados_gerados'])
                    self.assertLessEqual(m['nos_explorados'], m['estados_gerados']+1)
                    self.assertEqual(m['historico'], [])
                    if entrada == SOLUCAO:
                        self.assertEqual((m['nos_explorados'], m['tentativas'], m['passos']), (1, 0, 0))

    def test_entrada_invalida_e_formato(self):
        for entrada in (INVALIDO, [], [[0]*9]*8, [[0]*8]*9, [[0]*9]*8+[[1.5]*9], [[True]*9]*9):
            self.assertFalse(validaSudoku(entrada))
            self.assertFalse(validar_estado_inicial(entrada)['valido'])
            for solver in (resolver_dfs, resolver_best_first):
                with self.assertRaises(ValueError):
                    solver(entrada)

    def test_sem_solucao_preserva_entrada(self):
        self.assertTrue(validaSudoku(SEM_SOLUCAO))
        for solver in (resolver_dfs, resolver_best_first):
            b = copy.deepcopy(SEM_SOLUCAO)
            m = solver(b)
            self.assertFalse(m['solucionado'])
            self.assertIsNone(m['passos'])
            self.assertEqual(b, SEM_SOLUCAO)

    def test_validacao_separada_bloqueia_ambos_fluxos(self):
        for modo in ('resolver', 'comparar'):
            for entrada in (INVALIDO, SEM_SOLUCAO):
                with patch('execucao.resolver_dfs') as dfs, patch('execucao.resolver_best_first') as best:
                    r = executar(entrada, modo)
                    self.assertFalse(r['validacao']['solucionavel'])
                    dfs.assert_not_called()
                    best.assert_not_called()
        b = copy.deepcopy(CLASSICO)
        self.assertTrue(validar_estado_inicial(b)['solucionavel'])
        self.assertEqual(b, CLASSICO)

    def test_cancelamento_preserva_entrada(self):
        for solver in (resolver_dfs, resolver_best_first, validar_estado_inicial):
            b = copy.deepcopy(CLASSICO)
            chamadas = [0]
            def cancelar():
                chamadas[0] += 1
                return chamadas[0] > 4
            with self.assertRaises(BuscaCancelada):
                solver(b, cancelar=cancelar)
            self.assertEqual(b, CLASSICO)

    def test_fronteira_real_e_desempate(self):
        # Duas soluções ou mais: há alternativas pendentes além do ramo atual.
        b = [[0 if n in (1, 2) else n for n in row] for row in SOLUCAO]
        original = copy.deepcopy(b)
        m = resolver_best_first(b, True)
        conferir_solucao(self, original, b)
        h = m['historico']
        self.assertTrue(any(len(p.get('fronteira', [])) > 1 for p in h))
        for atual, proximo in zip(h, h[1:]):
            fronteira = atual['fronteira']
            self.assertEqual(fronteira[0]['id'], proximo['estado_id'])
            self.assertEqual(fronteira[0]['h'], proximo['h'])
            self.assertEqual([(n['h'], n['id']) for n in fronteira], sorted((n['h'], n['id']) for n in fronteira))
            self.assertEqual(sum(n['escolhido'] for n in fronteira), 1)

    def test_historico_nao_muda_contadores(self):
        for solver in (resolver_dfs, resolver_best_first):
            a = solver(copy.deepcopy(QUASE), False)
            b = solver(copy.deepcopy(QUASE), True)
            for key in ('tentativas', 'nos_explorados', 'passos', 'testes_candidatos'):
                self.assertEqual(a[key], b[key])
            self.assertEqual(b['historico'][-1]['tipo'], 'solucao')

    def test_gerados_possuem_solucao(self):
        for seed in (1, 7, 19):
            random.seed(seed)
            b = criar_sudoku_aleatorio()
            self.assertTrue(validar_estado_inicial(b)['solucionavel'])


class TestInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        import interface
        self.mod = interface
        self.w = interface.InterfaceSudoku()
        self.avisos = patch('interface.QMessageBox.warning')
        self.avisos.start()

    def aguardar(self):
        from PySide6.QtTest import QTest
        prazo = time.monotonic()+20
        while self.w.trabalho is not None and time.monotonic() < prazo:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertIsNone(self.w.trabalho, 'Cálculo excedeu o prazo do teste')

    def tearDown(self):
        if self.w.trabalho is not None:
            self.w.cancelar_calculo()
            self.aguardar()
        self.w.close()
        self.app.processEvents()
        self.avisos.stop()

    def test_reproducao_dos_dois_algoritmos(self):
        for idx in (0, 1):
            self.w.limpar_sudoku()
            self.w.preencher_interface(QUASE)
            self.w.combo_algoritmo.setCurrentIndex(idx)
            self.w.preparar_resolucao()
            self.aguardar()
            self.assertTrue(self.w.historico)
            for _ in range(len(self.w.historico)):
                self.w.proximo_passo()
            conferir_solucao(self, QUASE, self.w.ler_interface())
            self.w.editar_inicial()
            self.assertEqual(self.w.ler_interface(), QUASE)
            self.assertTrue(all(not c.isReadOnly() for row in self.w.celulas for c in row))

    def test_comparacao_considera_edicao_visivel(self):
        self.w.sudoku_inicial = copy.deepcopy(CLASSICO)
        self.w.preencher_interface(QUASE)
        self.w.comparar_algoritmos()
        self.aguardar()
        self.assertEqual(self.w.sudoku_inicial, QUASE)
        self.assertEqual(self.w.ler_interface(), QUASE)
        self.assertIn('Passos no caminho da solução: 9', self.w.texto_decisao.toPlainText())

    def test_troca_algoritmo_reutiliza_original(self):
        self.w.preencher_interface(QUASE)
        self.w.preparar_resolucao()
        self.aguardar()
        self.w.proximo_passo()
        self.w.combo_algoritmo.setCurrentIndex(1)
        self.w.preparar_resolucao()
        self.aguardar()
        self.assertEqual(self.w.sudoku_inicial, QUASE)
        self.assertEqual(self.w.label_passos.text(), 'Passos da solução: 9')

    def test_invalidos_sem_solver_na_interface(self):
        for entrada in (INVALIDO, SEM_SOLUCAO):
            self.w.preencher_interface(entrada)
            with patch('execucao.resolver_dfs') as dfs, patch('execucao.resolver_best_first') as best:
                self.w.preparar_resolucao()
                self.aguardar()
                dfs.assert_not_called()
                best.assert_not_called()
            self.assertFalse(self.w.historico)

    def test_interface_responde_e_cancela(self):
        from PySide6.QtCore import QTimer
        from sudoku import verificar_cancelamento
        def tarefa_longa(b, modo, algoritmo, cancelar):
            while True:
                verificar_cancelamento(cancelar)
                time.sleep(0.002)
        with patch('interface.executar', side_effect=tarefa_longa):
            self.w.preencher_interface(QUASE)
            self.w.preparar_resolucao()
            QTimer.singleShot(30, self.w.cancelar_calculo)
            self.aguardar()
        self.assertIn('cancelado', self.w.label_status.text())
        self.assertEqual(self.w.ler_interface(), QUASE)
        self.assertTrue(self.w.botao_resolver.isEnabled())


if __name__ == '__main__':
    unittest.main()
