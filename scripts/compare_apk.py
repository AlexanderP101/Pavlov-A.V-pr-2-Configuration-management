"""Независимая проверка результата штатным apk на одном снимке индекса."""

import argparse
from pathlib import Path
import re
import random
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from apkgraph.graph import build_graph, dependency_order
from apkgraph.repository import parse_index
from apkgraph.versions import compare


def run_apk(base, arguments):
    """Запустить внешнюю проверку и вернуть текст и код завершения."""
    return subprocess.run(base + arguments, text=True,
                          capture_output=True, check=False)


def compare_package(repository, base, name):
    """Сопоставить рёбра dot и порядок симуляции установки с графом."""
    root = repository.resolve(name)
    graph = build_graph(repository, root, len(repository.packages))
    labels = {key: f'{p.name}-{p.version}' for key, p in graph.nodes.items()}
    expected = {(labels[a], labels[b]) for a, children in graph.edges.items()
                for b in children}
    result = run_apk(base, ['dot', name])
    actual = set(re.findall(r'"([^"\n]+)" -> "([^"\n]+)"', result.stdout))
    if expected != actual or result.returncode not in (0, 1):
        raise ValueError(f'{name}: рёбра отличаются\n{result.stderr}')
    plan = run_apk(base, ['add', '--simulate', '--initdb', name])
    if plan.returncode:
        raise ValueError(f'{name}: ошибка apk add\n{plan.stderr}')
    installed = re.findall(r'Installing (\S+) \(([^)]+)\)', plan.stdout)
    actual_order = [f'{name}@{version}' for name, version in installed]
    expected_order = dependency_order(graph)
    if actual_order != expected_order:
        raise ValueError(f'{name}: порядок отличается: {actual_order}')
    print(f'{root.key}: рёбра и порядок совпали')


def compare_snapshot(executable, archive):
    """Создать пустую базу apk, сохранив один и тот же индекс обеим сторонам."""
    with tarfile.open(archive, 'r:gz') as stream:
        with stream.extractfile('APKINDEX') as index:
            repository = parse_index(index.read().decode('utf-8'))
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        root = folder / 'root'
        repo = folder / 'repository' / 'x86_64'
        repo.mkdir(parents=True)
        (repo / 'APKINDEX.tar.gz').write_bytes(archive.read_bytes())
        for name in ('lib/apk/db/installed', 'etc/apk/world'):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        base = [str(executable), '--root', str(root), '--arch', 'x86_64',
                '--allow-untrusted', '--repository', str(repo.parent),
                '--repositories-file', '/dev/null', '--no-network']
        for name in ('busybox', 'zlib', 'musl'):
            compare_package(repository, base, name)



def compare_versions(executable):
    """Сопоставить 39 × 39 примеров с apk version -t."""
    rng = random.Random(18)
    versions = ['1', '1.0', '1.00', '1.01', '1.001', '1.0a', '1.0a1',
                '1.0_alpha', '1.0_alpha1', '1.0_rc1', '1.0_p1',
                '1.0-r0', '1.0-r1', '1.0.0', '1.0_git20250101',
                '1_alpha_alpha', '1_alpha1', '1_alpha1_alpha2', '1.01a2']
    versions += [f'{rng.randrange(5)}.{rng.randrange(20)}-r{rng.randrange(10)}'
                 for _ in range(20)]
    for left in versions:
        for right in versions:
            actual = ['<', '=', '>'][compare(left, right) + 1]
            result = run_apk([str(executable)],
                             ['version', '-t', left, right])
            if result.returncode or actual != result.stdout.strip():
                raise ValueError(f'Версии {left}, {right}: расхождение')
    print(f'Сравнение версий: {len(versions) ** 2} пар, расхождений нет')


def main():
    """Принять локальные пути без скачивания или установки пакетов."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path, help='путь к apk.static x86_64')
    parser.add_argument('index', type=Path, help='путь к APKINDEX.tar.gz')
    args = parser.parse_args()
    compare_snapshot(args.apk.resolve(), args.index.resolve())
    compare_versions(args.apk.resolve())


if __name__ == '__main__':
    main()
