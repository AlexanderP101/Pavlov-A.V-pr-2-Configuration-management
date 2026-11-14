"""Проверки, что аудит обнаруживает нарушения правил из PDF."""

import ast
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from code_rules import inspect_tree
from repository_rules import inspect_tracked


class RuleTests(unittest.TestCase):
    """Положительные и отрицательные примеры для новых проверок."""

    def test_complexity(self):
        """Учитывать условия и отдельные булевы ветви."""
        source = ('def sample(value):\n    """Документация."""\n'
                  '    if ' + ' or '.join(['value'] * 11) + ':\n'
                  '        return True\n')
        messages = inspect_tree(ast.parse(source))
        self.assertTrue(any('Ц1' in message for message in messages))

    def test_magic_number(self):
        """Число в сравнении запрещено; индекс элемента числом допустим."""
        self.assertTrue(inspect_tree(ast.parse('valid = depth < -1')))
        self.assertEqual(inspect_tree(ast.parse('valid = a[0] < b[0]')), [])
        self.assertEqual(inspect_tree(ast.parse('valid = depth < LIMIT')), [])

    def test_docstrings_and_names(self):
        """Обнаруживать неверное имя и отсутствие docstring."""
        source = 'def WrongName(BadArgument):\n    return BadArgument\n'
        messages = inspect_tree(ast.parse(source))
        self.assertTrue(any('К1' in message for message in messages))
        self.assertTrue(any('И1' in message for message in messages))

    def test_binary_and_archive(self):
        """Расширение архива и бинарное содержимое обнаруживаются."""
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'file.zip'
            path.write_bytes(b'archive\x00')
            messages = inspect_tracked(path)
            self.assertTrue(any('Г1' in message for message in messages))
            self.assertTrue(any('Г2' in message for message in messages))
