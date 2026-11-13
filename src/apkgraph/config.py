"""Чтение и проверка TOML-конфигурации."""

from dataclasses import dataclass, asdict
from pathlib import Path
import re
import tomllib
from urllib.parse import urlparse

from .versions import tokens


@dataclass(frozen=True)
class Config:
    """Пять параметров варианта; пути разрешаются от TOML-файла."""

    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int

    def items(self):
        """Вернуть параметры для демонстрации первого этапа."""
        return asdict(self).items()


def load_config(path):
    """Загрузить строгую схему TOML; сообщить об ошибке параметра."""
    path = Path(path).resolve()
    with path.open('rb') as stream:
        data = tomllib.load(stream)
    required = set(Config.__annotations__)
    if set(data) != required:
        missing = sorted(required - set(data))
        extra = sorted(set(data) - required)
        raise ValueError(f'Поля TOML: отсутствуют {missing}, лишние {extra}')
    validate_fields(data)
    if data['test_mode']:
        target = (path.parent / data['repository']).resolve()
        if not target.is_file():
            raise ValueError(f'repository: файл не найден: {target}')
        data['repository'] = str(target)
    else:
        url = urlparse(data['repository'])
        if url.scheme not in ('http', 'https') or not url.netloc:
            raise ValueError('repository: ожидается URL http:// или https://')
    return Config(**data)


def validate_fields(data):
    """Проверить типы, имена пакетов, версию и глубину."""
    for key in ('package', 'repository', 'version'):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(f'{key}: ожидается непустая строка')
    if type(data['test_mode']) is not bool:
        raise ValueError('test_mode: ожидается true или false')
    if type(data['max_depth']) is not int or data['max_depth'] < 0:
        raise ValueError('max_depth: ожидается целое число >= 0')
    pattern = r'[A-Z]+' if data['test_mode'] else r'[a-z0-9][a-z0-9+_.-]*'
    if re.fullmatch(pattern, data['package']) is None:
        raise ValueError('package: недопустимое имя пакета')
    if re.fullmatch(r'[0-9][A-Za-z0-9._+-]*', data['version']) is None:
        raise ValueError('version: недопустимая версия')
    try:
        tokens(data['version'])
    except ValueError as error:
        raise ValueError(f'version: {error}') from error
