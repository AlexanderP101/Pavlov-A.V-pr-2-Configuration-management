"""Проверить механические правила оформления из задания."""

import ast
from pathlib import Path

MAX_LINE = 80
MAX_FILE = 1000
MAX_FUNCTION = 40
MAX_ARGUMENTS = 7
ROOT = Path(__file__).resolve().parents[1]


def inspect_file(path):
    """Проверить длины, число аргументов и наличие docstring."""
    source = path.read_text(encoding='utf-8')
    lines = source.splitlines()
    errors = []
    if len(lines) > MAX_FILE:
        errors.append(f'{path}: больше {MAX_FILE} строк')
    for number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE:
            errors.append(f'{path}:{number}: строка длиннее {MAX_LINE}')
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        location = f'{path}:{node.lineno}: {node.name}'
        if node.end_lineno - node.lineno + 1 > MAX_FUNCTION:
            errors.append(f'{location}: функция длиннее {MAX_FUNCTION}')
        arguments = node.args
        count = (len(arguments.posonlyargs) + len(arguments.args)
                 + len(arguments.kwonlyargs)
                 + bool(arguments.vararg) + bool(arguments.kwarg))
        if count > MAX_ARGUMENTS:
            errors.append(f'{location}: больше {MAX_ARGUMENTS} аргументов')
        if ast.get_docstring(node) is None:
            errors.append(f'{location}: отсутствует docstring')
    return errors


def main():
    """Завершить проверку ненулевым кодом при нарушениях."""
    errors = []
    for directory in ('src', 'tests', 'scripts'):
        for path in sorted((ROOT / directory).rglob('*.py')):
            errors.extend(inspect_file(path))
    for error in errors:
        print(error)
    if errors:
        return 1
    print('Оформление: длины строк/файлов/функций, аргументы, docstring — OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
