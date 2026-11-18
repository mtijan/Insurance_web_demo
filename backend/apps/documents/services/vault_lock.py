"""Bounded OS locks supporting concurrent per-assurance writes and global recovery."""
from contextlib import ExitStack, contextmanager
import os
from pathlib import Path
from time import monotonic, sleep

from django.conf import settings
from apps.documents.services.vault_paths import StorageUnavailable


def lock_once(stream, shared=False):
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        mode = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
        fcntl.flock(stream.fileno(), mode | fcntl.LOCK_NB)


def unlock(stream):
    if os.name == "nt":
        import msvcrt
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def ensure_lock_byte(stream):
    stream.seek(0, os.SEEK_END)
    if stream.tell() == 0:
        stream.write(b"0")
        stream.flush()


@contextmanager
def acquire_file_lock(path, shared=False):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        stream = path.open("a+b")
    except OSError as exc:
        raise StorageUnavailable() from exc
    acquired = False
    try:
        ensure_lock_byte(stream)
        deadline = monotonic() + getattr(settings, "VAULT_LOCK_TIMEOUT", 10)
        while not acquired:
            try:
                lock_once(stream, shared=shared)
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


@contextmanager
def vault_write_lock(scope=None, shared=False):
    root = Path(settings.MEDIA_ROOT)
    with ExitStack() as stack:
        if scope is None:
            stack.enter_context(acquire_file_lock(root / ".vault-write.lock", shared=False))
        else:
            if os.name != "nt":
                stack.enter_context(acquire_file_lock(root / ".vault-write.lock", shared=shared))
            lock_path = root / "vault" / ".locks" / f"{scope}.lock"
            stack.enter_context(acquire_file_lock(lock_path, shared=False))
        yield
