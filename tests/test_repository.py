"""Проверки APKINDEX, поставщиков и версий."""

import unittest

from apkgraph.repository import Package, Repository, parse_index
from apkgraph.versions import compare, satisfies


class RepositoryTests(unittest.TestCase):
    """Разрешение реальных и виртуальных зависимостей."""

    def test_parse_and_virtual(self):
        """Двоеточие в so: не разрушает разбор строк APKINDEX."""
        repo = parse_index('P:app\nV:1-r0\nD:so:libx.so.1 !old\n\n'
                           'P:libx\nV:2-r0\np:so:libx.so.1=1\n')
        root = repo.root('app', '1-r0')
        self.assertEqual(root.dependencies, ('so:libx.so.1', '!old'))
        self.assertEqual(repo.resolve('so:libx.so.1=1').name, 'libx')
        with self.assertRaisesRegex(ValueError, 'отсутствует'):
            repo.root('app', '2-r0')

    def test_select_version(self):
        """Ограничение версии не заменяется выбором просто последней."""
        repo = Repository([Package('x', v) for v in ('1-r0', '2-r0')])
        self.assertEqual(repo.resolve('x<2').version, '1-r0')
        self.assertEqual(repo.resolve('x').version, '2-r0')
        with self.assertRaisesRegex(ValueError, 'Не найдена'):
            repo.resolve('x>3')

    def test_unversioned_virtual(self):
        """Неверсионированный provides не удовлетворяет версии."""
        repo = Repository([Package('x', '1', provides=('virtual',))])
        self.assertEqual(repo.resolve('virtual').name, 'x')
        with self.assertRaises(ValueError):
            repo.resolve('virtual>=1')

    def test_invalid_index(self):
        """Повреждённый индекс явно отвергается."""
        for text in ('', 'P:x\n', 'V:1\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_index(text)

    def test_version_comparison(self):
        """Суффиксы APK, ревизии и числа сравниваются не лексикографически."""
        ordered = ['1.0_alpha1', '1.0_beta1', '1.0_pre1', '1.0_rc1',
                   '1.0', '1.0-r1', '1.0-r10', '1.0_p1', '1.1', '1.10']
        for left, right in zip(ordered, ordered[1:]):
            with self.subTest(left=left, right=right):
                self.assertLess(compare(left, right), 0)
                self.assertGreater(compare(right, left), 0)
        self.assertTrue(satisfies('1.2.3-r0', '~', '1.2'))
        self.assertFalse(satisfies('1.20-r0', '~', '1.2'))
        self.assertEqual(compare('1.0', '1.0'), 0)
        self.assertLess(compare('1.0', '1.01'), 0)
        self.assertLess(compare('1.001', '1.01'), 0)
        self.assertGreater(compare('1_alpha1', '1_alpha_alpha'), 0)
