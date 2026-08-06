from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_DOCUMENT_BYTES = 1024 * 1024


class AIKnowledgeError(ValueError):
    pass
