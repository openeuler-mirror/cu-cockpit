import fcntl
import json
import os
import secrets
import sqlite3
import stat
import tempfile
from contextlib import closing, contextmanager
from pathlib import Path


def backup_root(base_dir: Path) -> Path:
    return Path(os.environ.get('BACKUP_ROOT') or base_dir / 'var' / 'backups')


def validate_backup_root(root: Path) -> None:
    if not root.is_absolute() or '..' in root.parts:
        raise ValueError('Backup root must be an absolute path without traversal')
    for path in (root, *root.parents):
        try:
            details = path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(details.st_mode):
            raise ValueError('Backup root must not contain links or non-directories')
        if path == root and details.st_mode & 0o077:
            raise PermissionError('Backup root must be private')


def initialize_backup_root(root: Path) -> Path:
    validate_backup_root(root)
    for path in reversed((root, *root.parents)):
        if not path.exists():
            path.mkdir(mode=0o700)
            validate_backup_root(root)
    validate_backup_root(root)
    return root


def initialize_installation(root: Path, application_version: str) -> dict:
    validate_backup_root(root)
    if os.path.lexists(root / 'metadata.json'):
        return read_installation(root, application_version)
    identity = {
        'installation_id': secrets.token_hex(16),
        'hmac_key': secrets.token_hex(32),
        'application_version': application_version,
    }
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=root,
                                     prefix='.metadata-', delete=True) as temporary:
        os.chmod(temporary.name, 0o600)
        json.dump(identity, temporary)
        temporary.flush()
        os.fsync(temporary.fileno())
        try:
            os.link(temporary.name, root / 'metadata.json', follow_symlinks=False)
        except FileExistsError:
            return read_installation(root, application_version)
    return identity


def read_installation(root: Path, application_version: str) -> dict:
    validate_backup_root(root)
    descriptor = os.open(root / 'metadata.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'r', encoding='utf-8') as metadata:
        details = os.fstat(metadata.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
            raise PermissionError('Installation metadata must be a private regular file')
        if details.st_size > 4096:
            raise ValueError('Installation metadata exceeds the size limit')
        identity = json.load(metadata)
        if not isinstance(identity, dict) or set(identity) != {
                'installation_id', 'hmac_key', 'application_version'}:
            raise ValueError('Installation metadata has invalid fields')
        for field, size in (('installation_id', 16), ('hmac_key', 32)):
            value = identity[field]
            if not isinstance(value, str) or len(value) != size * 2:
                raise ValueError('Installation metadata has invalid identity')
            try:
                bytes.fromhex(value)
            except ValueError as error:
                raise ValueError('Installation metadata has invalid identity') from error
        if not isinstance(identity['application_version'], str) or not identity['application_version']:
            raise ValueError('Installation metadata has invalid version')
        if identity['application_version'] != application_version:
            raise ValueError('Installation metadata belongs to another application version')
        return identity


@contextmanager
def backup_lock(root: Path):
    validate_backup_root(root)
    descriptor = os.open(root / '.backup.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW |
                         os.O_NONBLOCK, 0o600)
    with os.fdopen(descriptor, 'r+b') as lockfile:
        details = os.fstat(lockfile.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
            raise PermissionError('Backup lock must be a private regular file')
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def backup_sqlite(source: Path, destination: Path) -> None:
    with closing(sqlite3.connect(f'{source.as_uri()}?mode=ro', uri=True)) as origin:
        with closing(sqlite3.connect(destination)) as snapshot:
            origin.backup(snapshot)


def verify_sqlite(path: Path) -> bool:
    try:
        with closing(sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True)) as database:
            return database.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    except sqlite3.DatabaseError:
        return False
