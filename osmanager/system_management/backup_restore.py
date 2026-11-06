"""Maintenance-only restore workflow for registered local backup targets."""

import stat
from pathlib import Path

from .backup_center import MAX_CONFIG_TARGETS


def _restore_targets(db_path: Path, configs: dict) -> dict:
    if not isinstance(configs, dict) or len(configs) > MAX_CONFIG_TARGETS:
        raise ValueError('Invalid restore configuration registry')
    targets = {'app.sqlite3': db_path}
    for name, path in configs.items():
        if not isinstance(name, str) or not name or not name.replace('_', '').replace('-', '').isalnum() or len(name) > 48:
            raise ValueError('Invalid restore configuration name')
        targets[f'configs/{name}.bin'] = path
    if len(set(targets.values())) != len(targets):
        raise ValueError('Restore targets must be distinct')
    for path in targets.values():
        if not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts:
            raise ValueError('Restore target must be an absolute registered path')
        for parent in path.parents:
            details = parent.lstat()
            if not stat.S_ISDIR(details.st_mode) or (
                    details.st_mode & 0o022 and not details.st_mode & stat.S_ISVTX):
                raise ValueError('Restore parent is unsafe')
        details = path.lstat()
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            raise ValueError('Restore target must be an unlinked regular file')
    return {name: str(path) for name, path in targets.items()}