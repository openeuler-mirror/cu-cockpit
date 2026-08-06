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
    return sorted({path.resolve() for path in paths if path.is_file()})
