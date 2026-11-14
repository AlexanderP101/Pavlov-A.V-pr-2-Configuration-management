"""Правила К1, Ц1, М1, И1 для синтаксического дерева Python."""

import ast
import re

MAX_COMPLEXITY = 10
SNAKE_CASE = re.compile(r'_|_?[a-z][a-z0-9_]*|__[a-z][a-z0-9_]*__')
CLASS_NAME = re.compile(r'_?[A-Z][A-Za-z0-9]*')
CONSTANT_NAME = re.compile(r'[A-Z][A-Z0-9_]*')
OVERRIDES = {'setUp', 'tearDown'}


def complexity(function):
    """Подсчитать ветвления, булевы операции и генераторы (база 1)."""
    result = 1
    branches = (ast.If, ast.IfExp, ast.For, ast.AsyncFor, ast.While,
                ast.ExceptHandler, ast.Assert)
    for node in ast.walk(function):
        if isinstance(node, branches):
            result += 1
        elif isinstance(node, ast.BoolOp):
            result += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            result += 1 + len(node.ifs)
    return result


def numeric_literal(node):
    """Обнаружить непосредственный числовой литерал, включая отрицательный."""
    if isinstance(node, ast.UnaryOp):
        return numeric_literal(node.operand)
    return (isinstance(node, ast.Constant)
            and type(node.value) in (int, float, complex))


def magic_comparison(node):
    """Проверить числа в операндах сравнения, исключая индексы массивов."""
    if not isinstance(node, ast.Compare):
        return False
    return any(numeric_literal(part) for part in
               [node.left, *node.comparators])


def invalid_name(node):
    """Проверить определения, аргументы и переменные по соглашениям PEP8."""
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    if isinstance(node, ast.ClassDef):
        return not CLASS_NAME.fullmatch(node.name)
    if isinstance(node, functions):
        return (node.name not in OVERRIDES
                and not SNAKE_CASE.fullmatch(node.name))
    if isinstance(node, ast.arg):
        return not SNAKE_CASE.fullmatch(node.arg)
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return not (SNAKE_CASE.fullmatch(node.id)
                    or CONSTANT_NAME.fullmatch(node.id))
    return False


def inspect_tree(tree):
    """Вернуть нарушения документации, сложности, чисел и имён."""
    errors = []
    for node in ast.walk(tree):
        line = getattr(node, 'lineno', 1)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score = complexity(node)
            if score > MAX_COMPLEXITY:
                errors.append(f'{line}: Ц1: сложность {score}')
            if ast.get_docstring(node) is None:
                errors.append(f'{line}: К1: отсутствует docstring')
        if magic_comparison(node):
            errors.append(f'{line}: М1: числовой литерал в сравнении')
        if invalid_name(node):
            errors.append(f'{line}: И1: имя не соответствует PEP8')
    return errors
