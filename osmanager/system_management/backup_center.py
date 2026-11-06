import os
import sqlite3
import stat
from contextlib import closing
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
