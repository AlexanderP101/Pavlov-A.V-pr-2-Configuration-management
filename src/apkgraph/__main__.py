"""Интерфейс командной строки."""

import argparse
import sys

from .config import load_config
from .repository import load_repository


def main():
    """Показать проверенные параметры конфигурации."""
    parser = argparse.ArgumentParser(description='APK Graph, вариант 18')
    parser.add_argument('config', help='путь к TOML-конфигурации')
    parser.add_argument('--stage', type=int, choices=range(1, 3), default=2)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.stage == 1:
            for key, value in config.items():
                print(f'{key}={value}')
        else:
            repository = load_repository(config)
            root = repository.root(config.package, config.version)
            for dependency in root.dependencies:
                print(dependency)
        return 0
    except (ValueError, OSError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
