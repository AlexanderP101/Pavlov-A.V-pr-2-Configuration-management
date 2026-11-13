"""Проверка структуры, коммитов и отслеживаемых файлов репозитория."""

from pathlib import Path
import re
import subprocess

REQUIRED_FILES = ('README.md', '.gitignore', 'run.sh')
REQUIRED_DIRS = ('src', 'tests')
FORBIDDEN_SUFFIXES = {'.zip', '.tar', '.gz', '.apk', '.jar', '.pyc', '.pyo',
                      '.svg', '.png', '.jpg', '.pdf', '.exe', '.so'}
FORBIDDEN_DIRS = {'__pycache__', '.venv', 'build', 'dist', '.idea', '.vscode'}
COMMIT = re.compile(r'(feat|fix|docs|test|refactor|chore|build|ci|perf|style)'
                    r'(\([a-z0-9_-]+\))?!?: .+')
MAX_FILE_LINES = 1000


def git_output(root, arguments):
    """Прочитать Git без shell и без изменений репозитория."""
    return subprocess.check_output(['git', '-C', str(root), *arguments])


def inspect_tracked(path):
    """Проверить Г1–Г5 и Р1 для одного отслеживаемого файла."""
    errors = []
    if path.suffix in FORBIDDEN_SUFFIXES:
        errors.append(f'{path}: Г1–Г4: запрещённое расширение')
    if FORBIDDEN_DIRS.intersection(path.parts):
        errors.append(f'{path}: Г3–Г5: служебный каталог')
    try:
        content = path.read_bytes()
        text = content.decode('utf-8')
    except UnicodeError:
        return errors + [f'{path}: Г2: бинарный файл']
    if b'\x00' in content:
        errors.append(f'{path}: Г2: нулевые байты')
    if len(text.splitlines()) > MAX_FILE_LINES:
        errors.append(f'{path}: Р1: больше {MAX_FILE_LINES} строк')
    return errors


def inspect_repository(root):
    """Проверить обязательные пути, историю и все файлы git ls-files."""
    errors = []
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f'С1/С2/С5: отсутствует {name}')
    for name in REQUIRED_DIRS:
        if not (root / name).is_dir():
            errors.append(f'С3/С4: отсутствует {name}')
    messages = git_output(root, ['log', '--format=%s']).decode().splitlines()
    for message in messages:
        if not COMMIT.fullmatch(message):
            errors.append(f'С6: неверный коммит: {message}')
    files = git_output(root, ['ls-files', '-z']).decode().split('\0')
    for name in filter(None, files):
        errors.extend(inspect_tracked(root / Path(name)))
    return errors
