"""Deployment-owned inputs for the local backup service."""

from pathlib import Path

from django.conf import settings

BACKUP_COMPAT_VERSION = '1'


def backup_database() -> Path:
	database = settings.DATABASES['default']
	if database['ENGINE'] != 'django.db.backends.sqlite3':
		raise ValueError('Backup requires the default SQLite database')
	path = Path(database['NAME'])
	if not path.is_absolute() or str(path) == ':memory:':
		raise ValueError('Backup requires an absolute on-disk SQLite database')
	return path