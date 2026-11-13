"""Интерфейс командной строки."""

import argparse
import sys

from .config import load_config
from .graph import build_graph
from .repository import load_repository


def main():
    """Показать проверенные параметры конфигурации."""
    parser = argparse.ArgumentParser(description='APK Graph, вариант 18')
    parser.add_argument('config', help='путь к TOML-конфигурации')
    parser.add_argument('--stage', type=int, choices=range(1, 4), default=3)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.stage == 1:
            for key, value in config.items():
                print(f'{key}={value}')
        else:
            repository = load_repository(config)
            root = repository.root(config.package, config.version)
            if args.stage == 2:
                for dependency in root.dependencies:
                    print(dependency)
            else:
                graph = build_graph(repository, root, config.max_depth)
                for node, children in graph.edges.items():
                    print(f'{node}: {", ".join(children)}')
        return 0
    except (ValueError, OSError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
