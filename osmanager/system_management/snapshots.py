import difflib
import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .models import ConfigSnapshot


MAX_SNAPSHOT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class SnapshotTarget:
    path: Path
    validator: object = None
    apply_hook: object = None


_TARGETS = {}


def register_snapshot_target(name, path, validator=None, apply_hook=None):
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.is_absolute():
        raise ValueError('快照路径必须为绝对路径')
    _TARGETS[name] = SnapshotTarget(path=resolved, validator=validator, apply_hook=apply_hook)


def registered_targets():
    return {name: str(target.path) for name, target in _TARGETS.items()}


def _target(name):
    if name not in _TARGETS:
        raise ValueError('未注册的配置快照目标')
    return _TARGETS[name]


def _read_text(path):
    data = path.read_bytes()
    if len(data) > MAX_SNAPSHOT_BYTES:
        raise ValueError('配置文件超过快照大小限制')
    return data.decode('utf-8')


def _checksum(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def create_snapshot(actor, module, target_name, reason='', metadata=None):
    target = _target(target_name)
    content = _read_text(target.path)
    return ConfigSnapshot.objects.create(
        actor=actor,
        module=module,
        target=target_name,
        path=str(target.path),
        checksum=_checksum(content),
        content=content,
        reason=reason,
        metadata=metadata or {},
    )


def diff_snapshot(snapshot):
    target = _target(snapshot.target)
    current = _read_text(target.path)
    return ''.join(difflib.unified_diff(
        snapshot.content.splitlines(keepends=True),
        current.splitlines(keepends=True),
        fromfile=f'snapshot:{snapshot.id}',
        tofile=f'current:{snapshot.target}',
    ))


def _atomic_write(path, content):
    stat_result = path.stat()
    descriptor, temporary_path = tempfile.mkstemp(prefix=f'.{path.name}.', dir=str(path.parent))
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, stat_result.st_mode)
        if hasattr(os, 'chown'):
            os.chown(temporary_path, stat_result.st_uid, stat_result.st_gid)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def rollback_snapshot(snapshot, actor, reason='回滚配置快照'):
    target = _target(snapshot.target)
    if Path(snapshot.path).resolve(strict=False) != target.path:
        raise ValueError('快照路径与注册目标不一致')
    if target.validator:
        target.validator(snapshot.content)
    current_snapshot = create_snapshot(actor, snapshot.module, snapshot.target, reason=reason,
                                       metadata={'rollback_from': snapshot.id})
    _atomic_write(target.path, snapshot.content)
    try:
        if target.apply_hook:
            target.apply_hook()
    except Exception:
        _atomic_write(target.path, current_snapshot.content)
        if target.apply_hook:
            target.apply_hook()
        raise
    return current_snapshot


def write_registered_text(target_name, content):
    target = _target(target_name)
    if not isinstance(content, str):
        raise ValueError('配置内容必须为文本')
    if len(content.encode('utf-8')) > MAX_SNAPSHOT_BYTES:
        raise ValueError('配置内容超过大小限制')
    if target.validator:
        target.validator(content)
    previous_content = _read_text(target.path)
    _atomic_write(target.path, content)
    try:
        if target.apply_hook:
            target.apply_hook()
    except Exception:
        _atomic_write(target.path, previous_content)
        if target.apply_hook:
            target.apply_hook()
        raise
    return _checksum(content)