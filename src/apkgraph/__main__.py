"""CLI пяти этапов практической работы."""

import argparse
import sys
import tarfile

from .config import load_config
from .graph import build_graph, dependency_order, truncated_nodes
from .plantuml import to_plantuml
from .repository import load_repository


def execute(config, stage):
    """Выполнить выбранный этап; по умолчанию вывести PlantUML."""
    if stage == 1:
        for key, value in config.items():
            print(f'{key}={value}')
        return
    repository = load_repository(config)
    root = repository.root(config.package, config.version)
    if stage == 2:
        for dependency in root.dependencies:
            print(dependency)
        return
    graph = build_graph(repository, root, config.max_depth)
    if stage == 3:
        for node, children in graph.edges.items():
            print(f'{node}: {", ".join(children)}')
    elif stage == 4:
        if truncated_nodes(graph, config.max_depth):
            print('Внимание: порядок только для усечённого графа',
                  file=sys.stderr)
        print(' -> '.join(dependency_order(graph)))
    else:
        print(to_plantuml(graph, config.max_depth), end='')
    for package, conflict in graph.conflicts:
        print(f'Конфликт (не ребро): {package}: {conflict}', file=sys.stderr)


def main():
    """Разобрать аргументы и преобразовать ошибки в код завершения 2."""
    parser = argparse.ArgumentParser(description='APK Graph, вариант 18')
    parser.add_argument('config', help='путь к TOML-конфигурации')
    parser.add_argument('--stage', type=int, choices=range(1, 6), default=5,
                        help='демонстрация этапа 1–5; по умолчанию 5')
    args = parser.parse_args()
    try:
        execute(load_config(args.config), args.stage)
        return 0
    except (ValueError, OSError, tarfile.TarError, KeyError,
            UnicodeError, EOFError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
