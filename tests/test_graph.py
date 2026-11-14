"""Проверки BFS, граничной глубины, ромба и циклов."""

import unittest

from apkgraph.graph import build_graph
from apkgraph.repository import Package, Repository


def repository(edges):
    """Создать репозиторий из компактного описания смежности."""
    return Repository([Package(name, '1', tuple(children))
                       for name, children in edges.items()])


class GraphTests(unittest.TestCase):
    """Обход завершается на циклах и сохраняет все найденные рёбра."""

    def build(self, edges, depth=10):
        """Построить граф от пакета A."""
        repo = repository(edges)
        return build_graph(repo, repo.root('A', '1'), depth)

    def test_bfs_shortest_depth(self):
        """Узел, найденный несколькими путями, разворачивается один раз."""
        graph = self.build({'A': ['B', 'C'], 'B': ['D'], 'C': ['D'],
                            'D': ['E'], 'E': []}, depth=2)
        self.assertEqual(list(graph.nodes), ['A@1', 'B@1', 'C@1', 'D@1'])
        self.assertEqual(graph.depths['D@1'], 2)
        self.assertEqual(graph.edges['C@1'], ['D@1'])
        self.assertNotIn('E@1', graph.nodes)

    def test_zero_depth(self):
        """При нулевой глубине не требуется разрешать даже прямые связи."""
        graph = self.build({'A': ['MISSING']}, depth=0)
        self.assertEqual(list(graph.nodes), ['A@1'])
        self.assertEqual(graph.edges['A@1'], [])

    def test_cycle_and_self_loop(self):
        """Цикл и петля сохраняются; бесконечного обхода нет."""
        graph = self.build({'A': ['A', 'B'], 'B': ['A']})
        self.assertEqual(graph.edges, {'A@1': ['A@1', 'B@1'],
                                       'B@1': ['A@1']})

    def test_missing_dependency(self):
        """Отсутствующая вершина внутри глубины — явная ошибка."""
        with self.assertRaisesRegex(ValueError, 'MISSING'):
            self.build({'A': ['MISSING']})

    def test_conflict_is_not_edge(self):
        """Отрицательная зависимость фиксируется отдельно."""
        graph = self.build({'A': ['!B'], 'B': []})
        self.assertEqual(graph.edges['A@1'], [])
        self.assertEqual(graph.conflicts, (('A@1', '!B'),))

    def test_long_chain(self):
        """Длинная цепочка подтверждает отсутствие рекурсии."""
        size = 1500
        packages = [Package(str(i), '1', (str(i + 1),))
                    for i in range(size)]
        packages.append(Package(str(size), '1'))
        graph = build_graph(Repository(packages), packages[0], size)
        self.assertEqual(len(graph.nodes), size + 1)


class OrderTests(unittest.TestCase):
    """Порядок зависит от частичного порядка, а не от случайного алфавита."""

    def test_diamond(self):
        """Каждая зависимость должна появляться раньше потребителя."""
        from apkgraph.graph import dependency_order
        repo = repository({'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []})
        graph = build_graph(repo, repo.root('A', '1'), 10)
        order = dependency_order(graph)
        self.assertEqual(order, ['D@1', 'B@1', 'C@1', 'A@1'])
        positions = {node: index for index, node in enumerate(order)}
        for node, children in graph.edges.items():
            for child in children:
                self.assertLess(positions[child], positions[node])

    def test_cycle(self):
        """На цикле нельзя заявлять существование топологического порядка."""
        from apkgraph.graph import dependency_order
        repo = repository({'A': ['B'], 'B': ['A']})
        graph = build_graph(repo, repo.root('A', '1'), 10)
        with self.assertRaisesRegex(ValueError, 'Цикл'):
            dependency_order(graph)

    def test_partial_and_isolated(self):
        """Нулевой предел и отдельный пакет поддерживаются."""
        from apkgraph.graph import dependency_order, truncated_nodes
        repo = repository({'A': ['B'], 'B': []})
        graph = build_graph(repo, repo.root('A', '1'), 0)
        self.assertEqual(dependency_order(graph), ['A@1'])
        self.assertEqual(truncated_nodes(graph, 0), ['A@1'])
        graph = build_graph(repo, repo.root('B', '1'), 10)
        self.assertEqual(dependency_order(graph), ['B@1'])
