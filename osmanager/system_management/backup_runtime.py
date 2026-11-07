"""Deployment-owned inputs for the local backup service."""

import os
from pathlib import Path

from django.conf import settings

from .config_center import CHRONY_PATH, CHRONY_TARGET
from .backup_restore import _restore_services
from .snapshots import registered_targets

BACKUP_COMPAT_VERSION = '1'


def backup_database() -> Path:
	database = settings.DATABASES['default']
	if database['ENGINE'] != 'django.db.backends.sqlite3':
		raise ValueError('Backup requires the default SQLite database')
	path = Path(database['NAME'])
	if not path.is_absolute() or str(path) == ':memory:':
		raise ValueError('Backup requires an absolute on-disk SQLite database')
	return path


def backup_configs() -> dict:
	registered = registered_targets().get(CHRONY_TARGET)
	if registered != str(CHRONY_PATH.resolve(strict=False)):
		raise ValueError('Chrony is not registered at its deployment target')
	if not Path(registered).is_file():
		raise FileNotFoundError('Chrony configuration is unavailable on this host')
	return {CHRONY_TARGET: Path(registered)}


def maintenance_services() -> list:
	configured = os.environ.get('BACKUP_RESTORE_SERVICES', '').split(',')
	return _restore_services(configured)