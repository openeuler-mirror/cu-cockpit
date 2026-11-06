import sqlite3
from contextlib import closing
from pathlib import Path


def backup_sqlite(source: Path, destination: Path) -> None:
    with closing(sqlite3.connect(f'{source.as_uri()}?mode=ro', uri=True)) as origin:
        with closing(sqlite3.connect(destination)) as snapshot:
            origin.backup(snapshot)
