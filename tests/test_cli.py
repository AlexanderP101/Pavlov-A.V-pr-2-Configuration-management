"""Проверки публичного CLI и текста PlantUML."""

from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    """Запуск программы как отдельного процесса."""

    def run_cli(self, example, stage):
        """Запустить модуль с конфигурацией из examples."""
        return subprocess.run(
            [sys.executable, '-B', '-m', 'apkgraph',
             str(ROOT / 'examples' / example),
             '--stage', str(stage)], text=True, capture_output=True,
            check=False, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))

    def test_all_stages(self):
        """Все пять режимов работают на одном репозитории."""
        expected = {1: 'max_depth=10', 2: 'B\nC\n',
                    3: 'A@1.0-r0: B@1.0-r0, C@1.0-r0',
                    4: 'D@1.0-r0 -> B@1.0-r0 -> C@1.0-r0 -> A@1.0-r0',
                    5: '@startuml'}
        for stage, fragment in expected.items():
            with self.subTest(stage=stage):
                result = self.run_cli('acyclic.toml', stage)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(fragment, result.stdout)

    def test_cycle_visualized_but_not_ordered(self):
        """Цикл отображается, но топологический порядок отвергается."""
        result = self.run_cli('cycle.toml', 5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('n2 --> n0', result.stdout)
        result = self.run_cli('cycle.toml', 4)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Цикл', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_isolated_and_partial(self):
        """Изолированная вершина не теряется; глубина ограничивает граф."""
        result = self.run_cli('isolated.toml', 5)
        self.assertIn('component "A@1.0-r0"', result.stdout)
        self.assertNotIn('-->', result.stdout)
        result = self.run_cli('depth1.toml', 5)
        self.assertNotIn('D@1.0-r0', result.stdout)
        result = self.run_cli('depth1.toml', 4)
        self.assertEqual(result.returncode, 0)
        self.assertIn('усечённого', result.stderr)

    def test_missing_config(self):
        """Ошибка пути читаема и не сопровождается traceback."""
        result = self.run_cli('absent.toml', 5)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Ошибка:', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
