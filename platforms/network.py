"""Trasporto limitato, annullabile e senza credenziali nei messaggi pubblici."""
import threading
import time
from contextlib import contextmanager
from urllib.parse import urlsplit
import requests as _requests

_local = threading.local()

class Cancelled(RuntimeError):
    pass

class Operation:
    def __init__(self, event):
        self.event = event
        self.deadline = time.monotonic() + 15 * 60
        self.bytes = 0
        self.byte_limit = 2 * 1024**3
        self.lock = threading.Lock()
    def check(self):
        if self.event.is_set():
            raise Cancelled("Operazione annullata. Nessun PDF parziale salvato.")
        if time.monotonic() > self.deadline:
            raise RuntimeError("Tempo massimo dell’operazione superato. Riprova.")
    def consume(self, count):
        with self.lock:
            self.bytes += count
            if self.bytes > self.byte_limit:
                raise RuntimeError("Download troppo grande: limite di sicurezza superato.")
        self.check()

def current():
    return getattr(_local, 'operation', None)

@contextmanager
def scope(operation):
    old = current()
    _local.operation = operation
    try:
        yield
    finally:
        _local.operation = old

def check():
    if current():
        current().check()

class Session(_requests.Session):
    def rebuild_auth(self, prepared_request, response):
        super().rebuild_auth(prepared_request, response)
        if (urlsplit(response.request.url).scheme, urlsplit(response.request.url).netloc) != (urlsplit(prepared_request.url).scheme, urlsplit(prepared_request.url).netloc):
            for key in list(prepared_request.headers):
                if key.lower() in {'authorization','auth_token','token-session','x-auth-token','usertoken','cookie'}:
                    del prepared_request.headers[key]
    def send(self, request, **kwargs):
        check()
        if urlsplit(request.url).scheme != "https":
            raise RuntimeError("Connessione non sicura: il servizio deve usare HTTPS.")
        redirects = kwargs.pop('allow_redirects', True)
        kwargs['stream'] = True
        from datetime import timedelta
        from requests.hooks import dispatch_hook
        from requests.cookies import extract_cookies_to_jar
        started = time.monotonic()
        adapter = self.get_adapter(request.url)
        response = adapter.send(request, **kwargs)
        response.elapsed = timedelta(seconds=time.monotonic() - started)
        response = dispatch_hook('response', request.hooks, response, **kwargs)
        extract_cookies_to_jar(self.cookies, request, response.raw)
        file_sink = getattr(self, '_file_sink', None)
        if file_sink is not None and response.status_code == 200:
            try:
                file_sink.receive(response)
                response._content = b''
                response._content_consumed = True
            finally:
                response.close()
            return response
        chunks, size = [], 0
        try:
            for chunk in response.iter_content(65536):
                check()
                size += len(chunk)
                if size > 512 * 1024**2:
                    raise RuntimeError('Risposta troppo grande.')
                if current():
                    current().consume(len(chunk))
                chunks.append(chunk)
            response._content = b''.join(chunks)
            response._content_consumed = True
        finally:
            response.close()
        if redirects:
            history = list(self.resolve_redirects(response, request, **kwargs))
            if history:
                history.insert(0, response)
                response = history.pop()
                response.history = history
        return response

    def request(self, method, url, **kwargs):
        check()
        kwargs['timeout'] = (10, 30)
        kwargs['stream'] = True
        attempts = 3 if method.upper() == 'GET' else 1
        for attempt in range(attempts):
            try:
                response = super().request(method, url, **kwargs)
                if response.status_code not in (429, 500, 502, 503, 504) or attempt + 1 == attempts:
                    return response
            except (_requests.Timeout, _requests.ConnectionError):
                check()
                if attempt + 1 == attempts:
                    raise
            delay = attempt + 1
            if current():
                current().event.wait(delay)
            else:
                time.sleep(delay)
            check()

def request(method, url, **kwargs):
    with Session() as session:
        return session.request(method, url, **kwargs)

def get(url, **kwargs):
    return request('GET', url, **kwargs)

def post(url, **kwargs):
    return request('POST', url, **kwargs)

def __getattr__(name):
    return getattr(_requests, name)


class _FileSink:
    def __init__(self, file, max_bytes, progress):
        self.file, self.max_bytes, self.progress = file, max_bytes, progress
        self.size = 0

    def receive(self, response):
        # A retried GET starts from zero; partial attempts still count toward the budget.
        self.file.seek(0)
        self.file.truncate()
        self.size = 0
        value = response.headers.get('Content-Length', '')
        total = int(value) if value.isdigit() else 0
        if total > self.max_bytes:
            raise RuntimeError(f'Archivio troppo grande: {total // 1024**2} MB, limite {self.max_bytes // 1024**2} MB.')
        last_progress = 0.0
        for chunk in response.iter_content(65536):
            check()
            if not chunk:
                continue
            self.size += len(chunk)
            if self.size > self.max_bytes:
                raise RuntimeError('Archivio troppo grande: limite di download superato.')
            if current():
                current().consume(len(chunk))
            self.file.write(chunk)
            now = time.monotonic()
            if self.progress and now - last_progress >= 0.2:
                self.progress(self.size, total)
                last_progress = now
        if total and not response.headers.get('Content-Encoding') and self.size != total:
            raise RuntimeError('Archivio incompleto: dimensione scaricata diversa da quella prevista.')
        if self.progress:
            self.progress(self.size, total)


def download_file(url, path, *, headers=None, progress=None, max_bytes=4 * 1024**3):
    """Stream a bounded archive to disk; publish only a complete successful response."""
    import os
    from pathlib import Path
    import tempfile
    destination = Path(path)
    temporary = None
    operation = current()
    old_limit = operation.byte_limit if operation else None
    try:
        if operation:
            # Up to two full transfer attempts, still bounded across redirects/retries.
            operation.byte_limit = max(old_limit, 2 * max_bytes)
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.part', delete=False) as file:
            temporary = Path(file.name)
            with Session() as session:
                sink = _FileSink(file, max_bytes, progress)
                session._file_sink = sink
                response = session.get(url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(f'Download archivio non riuscito (HTTP {response.status_code}).')
                if not sink.size:
                    raise RuntimeError('Il server ha restituito un archivio vuoto.')
            file.flush()
            os.fsync(file.fileno())
        check()
        os.replace(temporary, destination)
        return str(destination)
    finally:
        if operation:
            operation.byte_limit = old_limit
        if temporary and temporary.exists():
            temporary.unlink()
