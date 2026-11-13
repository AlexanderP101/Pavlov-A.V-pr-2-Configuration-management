"""Сравнение числовых компонентов, суффиксов и ревизий APK."""

import re

SUFFIXES = dict(alpha=-4, beta=-3, pre=-2, rc=-1,
                cvs=0, svn=1, git=2, hg=3, p=4)
END = 5
VERSION = re.compile(
    r'[0-9]+(?:\.[0-9]+)*(?:[a-z][0-9]*)?'
    r'(?:_(?:alpha|beta|pre|rc|cvs|svn|git|hg|p)[0-9]*)*'
    r'(?:-r[0-9]+)?'
)


def tokens(version):
    """Разбить версию на числовые, буквенные и служебные компоненты."""
    if VERSION.fullmatch(version) is None:
        raise ValueError(f'Неподдерживаемая APK-версия: {version}')
    result = []
    for match in re.finditer(r'(\.?\d+)|([a-z])|_([a-z]+)|(\-r\d+)',
                             version):
        number, letter, suffix, revision = match.groups()
        if number:
            if number.startswith('.0'):
                digits = number[1:]
                zeros = len(digits) - len(digits.lstrip('0'))
                count = max(zeros - 1, 0)
                result.append((0, -count))
                result.append((0, int(digits[count:])))
            else:
                kind = 3 if result and result[-1][0] == 2 else 0
                result.append((kind, int(number.lstrip('.'))))
        elif letter:
            result.append((1, ord(letter)))
        elif suffix:
            result.append((2, SUFFIXES[suffix]))
        else:
            result.append((4, int(revision[2:])))
    return result


def compare(left, right, fuzzy=False):
    """Вернуть -1, 0, 1; fuzzy сравнивает префикс компонентов."""
    first, second = tokens(left), tokens(right)
    for index in range(max(len(first), len(second))):
        a = first[index] if index < len(first) else (END, 0)
        b = second[index] if index < len(second) else (END, 0)
        if a == b:
            continue
        if a[0] == b[0]:
            return (a[1] > b[1]) - (a[1] < b[1])
        if fuzzy and index >= len(second):
            return 0
        if a[0] == 2 and a[1] < 0:
            return -1
        if b[0] == 2 and b[1] < 0:
            return 1
        return (a[0] < b[0]) - (a[0] > b[0])
    return 0


def satisfies(actual, operator, expected):
    """Проверить ограничение зависимости, включая совместимый префикс ~."""
    if not operator:
        return True
    relation = compare(actual, expected, fuzzy=operator == '~')
    accepted = {'=': {0}, '~': {0}, '<': {-1}, '>': {1},
                '<=': {-1, 0}, '>=': {0, 1}}
    return relation in accepted[operator]
