"""Проверки каждого параметра TOML."""

from pathlib import Path
import tempfile
import unittest

from apkgraph.config import load_config, validate_fields


class ConfigTests(unittest.TestCase):
    """Строгая схема и полезные ошибки."""

    def setUp(self):
        """Создать корректный набор параметров."""
        self.data = dict(package='A', repository='graph.json', test_mode=True,
                         version='1.0-r0', max_depth=3)

    def test_invalid_values(self):
        """Каждое поле отклоняет неверные типы и значения."""
        cases = [('package', ''), ('package', 'abc'), ('repository', ''),
                 ('test_mode', 1), ('version', ''), ('version', 'bad'),
                 ('max_depth', -1), ('max_depth', True), ('max_depth', 1.5)]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ValueError, key):
                    validate_fields(dict(self.data, **{key: value}))

    def test_relative_path(self):
        """Путь не зависит от текущего рабочего каталога."""
        root = Path(__file__).resolve().parents[1]
        config = load_config(root / 'examples/acyclic.toml')
        self.assertEqual(Path(config.repository).name, 'acyclic.json')
        self.assertTrue(Path(config.repository).is_absolute())

    def test_schema_and_url(self):
        """Проверить схему, URL, существование файла и TOML-синтаксис."""
        base = ('package="A"\nrepository="absent.json"\n'
                'test_mode=true\nversion="1"\nmax_depth=0\n')
        cases = [(base, 'файл не найден'),
                 (base + 'typo=1\n', 'Поля TOML'),
                 (base.replace('max_depth=0\n', ''), 'Поля TOML'),
                 (base.replace('true', 'false').replace('"A"', '"a"'),
                  'URL'),
                 ('package = [', 'Invalid')]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.toml'
            for content, message in cases:
                path.write_text(content, encoding='utf-8')
                with self.subTest(content=content):
                    with self.assertRaisesRegex(ValueError, message):
                        load_config(path)
