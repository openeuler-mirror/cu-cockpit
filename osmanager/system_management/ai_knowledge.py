import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_DOCUMENT_BYTES = 1024 * 1024


class AIKnowledgeError(ValueError):
    pass


def allowed_document_paths():
    paths = [PROJECT_ROOT / 'README.md', PROJECT_ROOT / 'README.en.md']
    specs = PROJECT_ROOT / 'openspec' / 'specs'
    if specs.is_dir():
        paths.extend(specs.rglob('*.md'))
    configured = os.environ.get('AI_SOP_PATH', '').strip()
    if configured:
        sop_directory = Path(configured).expanduser().resolve()
        if sop_directory.is_dir():
            paths.extend(sop_directory.rglob('*.md'))
    return sorted({path.resolve() for path in paths if path.is_file()})


def validate_document_path(path):
    resolved = Path(path).resolve()
    if resolved not in set(allowed_document_paths()):
        raise AIKnowledgeError('知识文档路径不在允许范围')
    if resolved.stat().st_size > MAX_DOCUMENT_BYTES:
        raise AIKnowledgeError('知识文档超过 1 MiB 限制')
    return resolved


def read_document(path):
    return validate_document_path(path).read_text(encoding='utf-8', errors='replace')
