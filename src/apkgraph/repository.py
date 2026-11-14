"""Самостоятельное чтение APKINDEX и разрешение зависимостей."""

from dataclasses import dataclass
from functools import cmp_to_key
from io import BytesIO
import json
from pathlib import Path
import re
import tarfile
from urllib.request import urlopen

from .versions import compare, satisfies

DEPENDENCY = re.compile(r'([^<>=~!\s]+)(<=|>=|=|<|>|~)?([^\s]*)')
MAX_DOWNLOAD = 64 * 1024 * 1024


@dataclass(frozen=True)
class Package:
    """Запись одного пакета APKINDEX."""

    name: str
    version: str
    dependencies: tuple = ()
    provides: tuple = ()

    @property
    def key(self):
        """Версия является частью идентификатора вершины."""
        return f'{self.name}@{self.version}'


def parse_dependency(text):
    """Разобрать имя и необязательное ограничение версии."""
    match = DEPENDENCY.fullmatch(text)
    if match is None:
        raise ValueError(f'Неверная зависимость: {text}')
    name, operator, version = match.groups()
    if bool(operator) != bool(version):
        raise ValueError(f'Неверное ограничение версии: {text}')
    return name, operator or '', version


class Repository:
    """Индекс реальных пакетов и виртуальных предоставляемых имён."""

    def __init__(self, packages):
        """Индексировать записи, сохраняя версии виртуальных provides."""
        self.packages = packages
        self.index = {}
        for package in packages:
            self.index.setdefault(package.name, []).append(
                (package, package.version))
            for provided in package.provides:
                name, _, version = parse_dependency(provided)
                self.index.setdefault(name, []).append((package, version))

    def resolve(self, dependency):
        """Выбрать новейшего подходящего поставщика; иначе выдать ошибку."""
        name, operator, version = parse_dependency(dependency)
        candidates = [package for package, provided in self.index.get(name, [])
                      if not operator or (provided and satisfies(
                          provided, operator, version))]
        if not candidates:
            raise ValueError(f'Не найдена зависимость: {dependency}')
        candidates.sort(key=lambda package: package.name)
        candidates.sort(key=cmp_to_key(
            lambda a, b: compare(a.version, b.version)), reverse=True)
        return candidates[0]

    def root(self, name, version):
        """Найти именно указанную версию реального корневого пакета."""
        for package in self.packages:
            if (package.name, package.version) == (name, version):
                return package
        raise ValueError(f'Пакет {name} версии {version} отсутствует в индексе')


def parse_index(text):
    """Прочитать P, V, D, p из текстового APKINDEX без сторонних средств."""
    packages = []
    for record in re.split(r'\n\s*\n', text.strip()):
        fields = dict(line.split(':', 1) for line in record.splitlines()
                      if ':' in line)
        if not {'P', 'V'} <= fields.keys():
            raise ValueError('APKINDEX: в записи отсутствуют P или V')
        packages.append(Package(fields['P'], fields['V'],
                                tuple(fields.get('D', '').split()),
                                tuple(fields.get('p', '').split())))
    if not packages:
        raise ValueError('APKINDEX пуст')
    return Repository(packages)


def read_remote(url):
    """Скачать APKINDEX.tar.gz и прочитать его без распаковки на диск."""
    if not url.endswith('APKINDEX.tar.gz'):
        url = url.rstrip('/') + '/APKINDEX.tar.gz'
    with urlopen(url, timeout=30) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('APKINDEX: превышен предел загрузки 64 MiB')
    with tarfile.open(fileobj=BytesIO(data), mode='r:gz') as archive:
        member = archive.getmember('APKINDEX')
        if member.size > MAX_DOWNLOAD:
            raise ValueError('APKINDEX: превышен предел распаковки 64 MiB')
        with archive.extractfile(member) as stream:
            return parse_index(stream.read().decode('utf-8'))


def read_test(path):
    """Прочитать JSON-граф с именами из больших латинских букв."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not data:
        raise ValueError('Тестовый репозиторий должен быть непустым объектом')
    packages = []
    for name, record in data.items():
        validate_test_record(name, record)
        packages.append(Package(name, record['version'],
                                tuple(record['dependencies'])))
    return Repository(packages)


def validate_test_record(name, record):
    """Проверить формат версии и зависимостей тестового пакета."""
    if re.fullmatch(r'[A-Z]+', name) is None:
        raise ValueError(f'Тестовое имя должно состоять из A-Z: {name}')
    if not isinstance(record, dict) or set(record) != {
            'version', 'dependencies'}:
        raise ValueError(f'{name}: нужны поля version и dependencies')
    if not isinstance(record['version'], str):
        raise ValueError(f'{name}: version должна быть строкой')
    compare(record['version'], record['version'])
    dependencies = record['dependencies']
    if not isinstance(dependencies, list):
        raise ValueError(f'{name}: dependencies должен быть списком')
    for dependency in dependencies:
        if not isinstance(dependency, str):
            raise ValueError(f'{name}: зависимость должна быть строкой')
        target, _, _ = parse_dependency(dependency)
        if re.fullmatch(r'[A-Z]+', target) is None:
            raise ValueError(f'{name}: недопустимая зависимость {dependency}')


def load_repository(config):
    """Выбрать источник данных согласно TOML."""
    if config.test_mode:
        return read_test(config.repository)
    return read_remote(config.repository)
