"""HTTP-интеграция через локальный сервер, без доступа к сети в тестах."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import tarfile
import tempfile
from threading import Thread
import unittest

from apkgraph.repository import read_remote


class QuietHandler(SimpleHTTPRequestHandler):
    """Тестовый HTTP-сервер без сообщений в stderr."""

    def log_message(self, format_string, *args):
        """Подавить служебный журнал HTTP."""


class RemoteTests(unittest.TestCase):
    """Проверить настоящий HTTP и чтение gzip/tar."""

    def setUp(self):
        """Создать временный репозиторий на свободном localhost-порту."""
        self.folder = tempfile.TemporaryDirectory()
        handler = partial(QuietHandler, directory=self.folder.name)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        """Остановить сервер и удалить временные файлы."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.folder.cleanup()

    def archive(self, content, name='APKINDEX'):
        """Упаковать содержимое APKINDEX для локального HTTP-репозитория."""
        path = Path(self.folder.name) / 'APKINDEX.tar.gz'
        with tarfile.open(path, 'w:gz') as stream:
            member = tarfile.TarInfo(name)
            member.size = len(content)
            stream.addfile(member, BytesIO(content))

    def test_repository_and_exact_url(self):
        """Поддерживаются URL каталога и полный URL архива."""
        self.archive(b'P:demo\nV:1-r0\nD:lib\n\nP:lib\nV:2-r0\n')
        for url in (self.url, self.url + '/APKINDEX.tar.gz'):
            with self.subTest(url=url):
                repo = read_remote(url)
                self.assertEqual(repo.root('demo', '1-r0').dependencies,
                                 ('lib',))

    def test_not_found(self):
        """HTTP 404 не замалчивается."""
        with self.assertRaises(OSError):
            read_remote(self.url)

    def test_bad_tar_and_missing_index(self):
        """Повреждённый архив и архив без APKINDEX диагностируются."""
        path = Path(self.folder.name) / 'APKINDEX.tar.gz'
        path.write_bytes(b'not gzip')
        with self.assertRaises(tarfile.TarError):
            read_remote(self.url)
        self.archive(b'text', name='OTHER')
        with self.assertRaises(KeyError):
            read_remote(self.url)
