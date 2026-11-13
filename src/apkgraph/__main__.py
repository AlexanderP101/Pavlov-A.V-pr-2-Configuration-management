"""Интерфейс командной строки."""

import argparse
import sys

from .config import load_config


def main():
    """Показать проверенные параметры конфигурации."""
    parser = argparse.ArgumentParser(description='APK Graph, вариант 18')
    parser.add_argument('config', help='путь к TOML-конфигурации')
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        for key, value in config.items():
            print(f'{key}={value}')
        return 0
    except (ValueError, OSError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
