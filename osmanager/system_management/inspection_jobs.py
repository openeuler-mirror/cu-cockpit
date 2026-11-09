"""Persistent single-host inspection jobs, without HTTP or systemd side effects."""

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings


@contextmanager
def inspection_lock():
    """Exclude other manual and timer workers using an inspection-only lock."""
    root = Path(getattr(settings, 'INSPECTION_STATE_DIR', settings.BASE_DIR / '.inspection'))
    root.mkdir(mode=0o700, exist_ok=True)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        import stat

        metadata = os.fstat(directory)
        if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise PermissionError('Inspection state directory must be private and owned')
        descriptor = os.open('worker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=directory)
        try:
            metadata = os.fstat(descriptor)
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid() or
                    stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1):
                raise PermissionError('Inspection lock must be a private owned regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)