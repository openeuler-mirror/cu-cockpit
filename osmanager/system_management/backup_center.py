import sqlite3
from contextlib import closing
from pathlib import Path


def backup_sqlite(source: Path, destination: Path) -> None:
    with closing(sqlite3.connect(f'{source.as_uri()}?mode=ro', uri=True)) as origin:
        with closing(sqlite3.connect(destination)) as snapshot:
            origin.backup(snapshot)


def verify_sqlite(path: Path) -> bool:
    with closing(sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True)) as database:
        return database.execute('PRAGMA integrity_check').fetchone() == ('ok',)
