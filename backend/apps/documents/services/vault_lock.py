"""One bounded OS lock shared by supported writes and recovery on this host."""
from contextlib import contextmanager
import os
from pathlib import Path
from time import monotonic, sleep

from django.conf import settings
from apps.documents.services.vault_paths import StorageUnavailable


def lock_once(stream):
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def unlock(stream):
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def vault_write_lock():
    try:
        root = Path(settings.MEDIA_ROOT)
        root.mkdir(parents=True, exist_ok=True)
        stream = (root / ".vault-write.lock").open("a+b")
    except OSError as exc:
        raise StorageUnavailable() from exc
    acquired = False
    try:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        deadline = monotonic() + getattr(settings, "VAULT_LOCK_TIMEOUT", 10)
        while not acquired:
            try:
                lock_once(stream)
                acquired = True
            except OSError as exc:
                if monotonic() >= deadline:
                    raise StorageUnavailable() from exc
                sleep(.02)
        yield
    finally:
        try:
            if acquired:
                unlock(stream)
        finally:
            stream.close()
