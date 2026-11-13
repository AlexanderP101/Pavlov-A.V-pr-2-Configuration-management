"""Итеративный BFS с глубиной и обработкой циклов."""

from collections import deque
from dataclasses import dataclass

MIN_DEPTH = 0
NO_DEPENDENCIES = 0


@dataclass
class Graph:
    """Вершины, ориентированные рёбра и минимальная глубина BFS."""

    root: str
    nodes: dict
    edges: dict
    depths: dict
    conflicts: tuple = ()


def build_graph(repository, root, max_depth):
    """Обойти зависимости BFS без рекурсии; корень имеет глубину ноль."""
    if type(max_depth) is not int or max_depth < MIN_DEPTH:
        raise ValueError('max_depth: ожидается целое число >= 0')
    graph = Graph(root.key, {root.key: root}, {root.key: []}, {root.key: 0})
    pending = deque([root])
    conflicts = []
    while pending:
        package = pending.popleft()
        depth = graph.depths[package.key]
        if depth >= max_depth:
            continue
        for dependency in package.dependencies:
            if dependency.startswith('!'):
                conflicts.append((package.key, dependency))
                continue
            child = repository.resolve(dependency)
            if child.key not in graph.edges[package.key]:
                graph.edges[package.key].append(child.key)
            if child.key in graph.nodes:
                continue
            graph.nodes[child.key] = child
            graph.edges[child.key] = []
            graph.depths[child.key] = depth + 1
            pending.append(child)
    graph.conflicts = tuple(conflicts)
    return graph


def dependency_order(graph):
    """Получить порядок «зависимости раньше потребителей» без рекурсии."""
    remaining, parents = reverse_edges(graph)
    ready = deque(node for node, count in remaining.items()
                  if count == NO_DEPENDENCIES)
    result = []
    while ready:
        node = ready.popleft()
        result.append(node)
        for parent in parents[node]:
            remaining[parent] -= 1
            if remaining[parent] == NO_DEPENDENCIES:
                ready.append(parent)
    if len(result) != len(graph.nodes):
        blocked = ', '.join(node for node, count in remaining.items() if count)
        raise ValueError(f'Цикл: порядок загрузки невозможен для {blocked}')
    return result


def truncated_nodes(graph, max_depth):
    """Найти граничные вершины с нераскрытыми положительными связями."""
    return [node for node, package in graph.nodes.items()
            if graph.depths[node] == max_depth
            and any(not dep.startswith('!') for dep in package.dependencies)]


def reverse_edges(graph):
    """Построить счётчики зависимостей и списки их потребителей."""
    remaining = {node: len(children)
                 for node, children in graph.edges.items()}
    parents = {node: [] for node in graph.nodes}
    for node, children in graph.edges.items():
        for child in children:
            parents[child].append(node)
    return remaining, parents
