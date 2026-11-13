"""Итеративный BFS с глубиной и обработкой циклов."""

from collections import deque
from dataclasses import dataclass


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
    if type(max_depth) is not int or max_depth < 0:
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
