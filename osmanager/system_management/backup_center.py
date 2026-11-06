import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import stat
import tempfile
import zipfile
from contextlib import closing, contextmanager, nullcontext
from pathlib import Path


ARCHIVE_FORMAT = 1
MAX_CONFIG_TARGETS = 4
MAX_CONFIG_BYTES = 1024 * 1024
MAX_DATABASE_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100


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


def read_backup_index(root: Path) -> dict:
    validate_backup_root(root)
    descriptor = os.open(root / 'index.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'r', encoding='utf-8') as index_file:
        details = os.fstat(index_file.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
            raise PermissionError('Backup index must be a private regular file')
        if details.st_size > 1048576:
            raise ValueError('Backup index exceeds the size limit')
        index = json.load(index_file)
        encode_backup_index(index)
        return index


def encode_backup_index(index: dict) -> bytes:
    if not isinstance(index, dict) or set(index) != {'tasks', 'backups'}:
        raise ValueError('Backup index requires task and backup mappings')
    for entries in index.values():
        if not isinstance(entries, dict) or len(entries) > 256 or not all(
                isinstance(key, str) for key in entries):
            raise ValueError('Backup index has invalid or excessive entries')
    payload = json.dumps(index, allow_nan=False).encode('utf-8')
    if len(payload) > 1048576:
        raise ValueError('Backup index exceeds the size limit')
    return payload


def write_backup_index(root: Path, index: dict, *, locked: bool = False) -> None:
    payload = encode_backup_index(index)
    with nullcontext() if locked else backup_lock(root):
        if os.path.lexists(root / 'index.json'):
            read_backup_index(root)
        with tempfile.TemporaryDirectory(dir=root, prefix='.index-') as staging:
            temporary = Path(staging) / 'index.json'
            descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'wb') as index_file:
                index_file.write(payload)
                index_file.flush()
                os.fsync(index_file.fileno())
            os.replace(temporary, root / 'index.json')
            directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)


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


def _read_backup_config(path: Path) -> bytes:
    if not isinstance(path, Path) or not path.is_absolute() or '..' in path.parts:
        raise ValueError('Configuration path must be absolute')
    for parent in path.parents:
        details = parent.lstat()
        if not stat.S_ISDIR(details.st_mode) or (
                details.st_mode & 0o022 and not details.st_mode & stat.S_ISVTX):
            raise ValueError('Configuration parent is unsafe')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as config_file:
        details = os.fstat(config_file.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            raise ValueError('Configuration must be an unlinked regular file')
        if details.st_size > MAX_CONFIG_BYTES:
            raise ValueError('Configuration exceeds size limit')
        content = config_file.read(MAX_CONFIG_BYTES + 1)
        if len(content) > MAX_CONFIG_BYTES:
            raise ValueError('Configuration exceeds size limit')
        return content


def _hash_backup_stream(source, limit: int, destination=None) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while chunk := source.read(65536):
        size += len(chunk)
        if size > limit:
            raise ValueError('Archive member exceeds size limit')
        digest.update(chunk)
        if destination is not None:
            destination.write(chunk)
    return size, digest.hexdigest()


def _backup_signature(manifest: dict, key: str) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True, allow_nan=False).encode('utf-8')
    return hmac.new(bytes.fromhex(key), payload, hashlib.sha256).hexdigest()


def _write_backup_archive(archive: Path, snapshot: Path, configs: dict,
                          manifest: dict, key: str) -> None:
    members = {}
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as package:
        for name, path in [('app.sqlite3', snapshot), *[
                (f'configs/{name}.bin', value) for name, value in sorted(configs.items())]]:
            if name == 'app.sqlite3':
                with path.open('rb') as source, package.open(name, 'w', force_zip64=True) as target:
                    size, digest = _hash_backup_stream(source, MAX_DATABASE_BYTES, target)
            else:
                content = _read_backup_config(path)
                with package.open(name, 'w') as target:
                    target.write(content)
                size, digest = len(content), hashlib.sha256(content).hexdigest()
            members[name] = {'size': size, 'sha256': digest}
        manifest['members'] = members
        signed = {**manifest, 'signature': _backup_signature(manifest, key)}
        package.writestr('manifest.json', json.dumps(signed, sort_keys=True,
                                                     separators=(',', ':')))
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('Archive exceeds size limit')


def _publish_backup_archive(root: Path, staged: Path, manifest: dict, actor: str,
                            *, locked: bool = False) -> dict:
    archive_id = manifest['archive_id']
    destination = root / f'{archive_id}.zip'
    record = {'archive_id': archive_id, 'application_version': manifest['application_version'],
              'installation_id': manifest['installation_id'], 'actor': actor,
              'size': staged.stat().st_size}
    with nullcontext() if locked else backup_lock(root):
        index = read_backup_index(root) if os.path.lexists(root / 'index.json') else {
            'tasks': {}, 'backups': {}}
        if len(index['backups']) >= 256 or archive_id in index['backups']:
            raise ValueError('Backup index is full or archive ID already exists')
        os.chmod(staged, 0o600)
        os.link(staged, destination, follow_symlinks=False)
        try:
            index['backups'][archive_id] = record
            write_backup_index(root, index, locked=True)
        except Exception:
            try:
                published = read_backup_index(root)['backups'] if os.path.lexists(
                    root / 'index.json') else {}
            except Exception:
                pass
            else:
                if archive_id not in published:
                    destination.unlink()
            raise
    return record


def _check_backup_inputs(db_path: Path, config_targets: dict, actor: str) -> None:
    if not isinstance(db_path, Path) or not db_path.is_absolute() or '..' in db_path.parts:
        raise ValueError('Database path must be absolute')
    if not stat.S_ISREG(db_path.lstat().st_mode):
        raise ValueError('Database must be a regular file')
    if not isinstance(config_targets, dict) or len(config_targets) > MAX_CONFIG_TARGETS:
        raise ValueError('Too many configuration targets')
    for name, path in config_targets.items():
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', name):
            raise ValueError('Invalid configuration target name')
        if not isinstance(path, Path):
            raise ValueError('Configuration path must be a Path')
    if not isinstance(actor, str) or not actor or len(actor) > 128:
        raise ValueError('Invalid backup actor')


def create_backup_archive(root: Path, db_path: Path, config_targets: dict,
                          app_version: str, actor: str) -> dict:
    _check_backup_inputs(db_path, config_targets, actor)
    identity = read_installation(root, app_version)
    if db_path.stat().st_size > MAX_DATABASE_BYTES:
        raise ValueError('Database exceeds size limit')
    manifest = {'format': ARCHIVE_FORMAT, 'application_version': app_version,
                'installation_id': identity['installation_id'],
                'archive_id': secrets.token_hex(16)}
    with tempfile.TemporaryDirectory(dir=root, prefix='.archive-') as staging:
        directory = Path(staging)
        snapshot = directory / 'snapshot.sqlite3'
        archive = directory / 'archive.zip'
        backup_sqlite(db_path, snapshot)
        if snapshot.stat().st_size > MAX_DATABASE_BYTES or not verify_sqlite(snapshot):
            raise ValueError('Database snapshot is too large or damaged')
        _write_backup_archive(archive, snapshot, config_targets, manifest, identity['hmac_key'])
        with archive.open('rb') as archive_file:
            os.fsync(archive_file.fileno())
        return _publish_backup_archive(root, archive, manifest, actor)


def _check_archive_members(package: zipfile.ZipFile) -> dict:
    entries = package.infolist()
    if not 2 <= len(entries) <= MAX_CONFIG_TARGETS + 2:
        raise ValueError('Archive has invalid member count')
    names = [entry.filename for entry in entries]
    if len(set(names)) != len(names) or not {'manifest.json', 'app.sqlite3'} <= set(names):
        raise ValueError('Archive has missing or duplicate members')
    expanded = 0
    for entry in entries:
        name = entry.filename
        if name not in ('manifest.json', 'app.sqlite3') and not re.fullmatch(
                r'configs/[A-Za-z0-9_-]{1,48}\.bin', name):
            raise ValueError('Archive contains an unexpected member')
        mode = entry.external_attr >> 16
        if (entry.flag_bits & 1 or entry.compress_type not in (
                zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) or
                (entry.create_system == 3 and stat.S_IFMT(mode) not in (0, stat.S_IFREG))):
            raise ValueError('Archive contains a special or encrypted member')
        limit = (16384 if name == 'manifest.json' else
                 MAX_DATABASE_BYTES if name == 'app.sqlite3' else MAX_CONFIG_BYTES)
        if (entry.file_size > limit or entry.compress_size > MAX_ARCHIVE_BYTES or
                entry.file_size > MAX_COMPRESSION_RATIO * max(1, entry.compress_size)):
            raise ValueError('Archive member exceeds resource limits')
        expanded += entry.file_size
    if expanded > MAX_EXPANDED_BYTES:
        raise ValueError('Archive exceeds expanded size limit')
    return {entry.filename: entry for entry in entries}


def _read_signed_manifest(package: zipfile.ZipFile, entries: dict, identity: dict) -> dict:
    raw = package.read('manifest.json')
    if len(raw) > 16384:
        raise ValueError('Manifest exceeds size limit')
    manifest = json.loads(raw)
    required = {'format', 'application_version', 'installation_id',
                'archive_id', 'members', 'signature'}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError('Invalid manifest fields')
    if (type(manifest['format']) is not int or manifest['format'] != ARCHIVE_FORMAT or
            manifest['application_version'] != identity['application_version'] or
            manifest['installation_id'] != identity['installation_id']):
        raise ValueError('Archive belongs to a different format or installation')
    if not isinstance(manifest['archive_id'], str) or not re.fullmatch(
            r'[0-9a-f]{32}', manifest['archive_id']):
        raise ValueError('Invalid archive ID')
    members = manifest['members']
    if not isinstance(members, dict) or set(members) != set(entries) - {'manifest.json'}:
        raise ValueError('Archive member list differs from manifest')
    for name, metadata in members.items():
        if (not isinstance(metadata, dict) or set(metadata) != {'size', 'sha256'} or
                type(metadata['size']) is not int or metadata['size'] != entries[name].file_size or
                not isinstance(metadata['sha256'], str) or not re.fullmatch(
                    r'[0-9a-f]{64}', metadata['sha256'])):
            raise ValueError('Invalid archive member metadata')
    signature = manifest['signature']
    unsigned = {key: value for key, value in manifest.items() if key != 'signature'}
    if not isinstance(signature, str) or not hmac.compare_digest(
            signature, _backup_signature(unsigned, identity['hmac_key'])):
        raise ValueError('Invalid archive signature')
    return manifest


def validate_backup_archive(root: Path, archive_path: Path, version: str) -> dict:
    identity = read_installation(root, version)
    if not isinstance(archive_path, Path) or not archive_path.is_absolute():
        raise ValueError('Archive path must be absolute')
    descriptor = os.open(archive_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as archive_file:
        details = os.fstat(archive_file.fileno())
        if not stat.S_ISREG(details.st_mode) or details.st_size > MAX_ARCHIVE_BYTES:
            raise ValueError('Archive is not a bounded regular file')
        import struct

        archive_file.seek(max(0, details.st_size - 65557))
        tail = archive_file.read(65557)
        eocd = tail.rfind(b'PK\x05\x06')
        if eocd < 0 or len(tail) - eocd < 22:
            raise ValueError('Archive has invalid ZIP directory')
        (_, disk, directory_disk, disk_entries, total_entries,
         directory_size, directory_offset, comment_size) = struct.unpack_from(
             '<4s4H2IH', tail, eocd)
        eocd_offset = details.st_size - len(tail) + eocd
        if (disk or directory_disk or disk_entries != total_entries or
                not 2 <= total_entries <= MAX_CONFIG_TARGETS + 2 or
                directory_size > 16384 or directory_size < total_entries * 46 or
                directory_offset == 0xffffffff or directory_size == 0xffffffff or
                directory_offset + directory_size != eocd_offset or
                eocd + 22 + comment_size != len(tail)):
            raise ValueError('Archive has invalid ZIP directory')
        if eocd_offset >= 20:
            archive_file.seek(eocd_offset - 20)
            if archive_file.read(4) == b'PK\x06\x07':
                raise ValueError('Archive has invalid ZIP directory')
        archive_file.seek(directory_offset)
        if archive_file.read(4) != b'PK\x01\x02':
            raise ValueError('Archive has invalid ZIP directory')
        archive_file.seek(0)
        with zipfile.ZipFile(archive_file) as package:
            entries = _check_archive_members(package)
            manifest = _read_signed_manifest(package, entries, identity)
            with tempfile.TemporaryDirectory(dir=root, prefix='.verify-') as staging:
                snapshot = Path(staging) / 'app.sqlite3'
                for name, metadata in manifest['members'].items():
                    limit = MAX_DATABASE_BYTES if name == 'app.sqlite3' else MAX_CONFIG_BYTES
                    with package.open(entries[name]) as source:
                        if name == 'app.sqlite3':
                            with snapshot.open('xb') as destination:
                                size, digest = _hash_backup_stream(source, limit, destination)
                        else:
                            size, digest = _hash_backup_stream(source, limit)
                    if size != metadata['size'] or not hmac.compare_digest(
                            digest, metadata['sha256']):
                        raise ValueError('Archive member hash or size mismatch')
                with snapshot.open('rb') as database_file:
                    if database_file.read(16) != b'SQLite format 3\x00' or not verify_sqlite(snapshot):
                        raise ValueError('Archive database is damaged')
            return manifest


def import_backup_archive(root: Path, uploaded_file, version: str, actor: str) -> dict:
    read_installation(root, version)
    if not callable(getattr(uploaded_file, 'read', None)):
        raise ValueError('Upload must be a readable file object')
    if not isinstance(actor, str) or not actor or len(actor) > 128:
        raise ValueError('Invalid backup actor')
    with tempfile.TemporaryDirectory(dir=root, prefix='.import-') as staging:
        staged = Path(staging) / 'upload.zip'
        descriptor = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, 'wb') as destination:
            _hash_backup_stream(uploaded_file, MAX_ARCHIVE_BYTES, destination)
            destination.flush()
            os.fsync(destination.fileno())
        manifest = validate_backup_archive(root, staged, version)
        return _publish_backup_archive(root, staged, manifest, actor)
