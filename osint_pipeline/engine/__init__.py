"""Engine layer — canonical hashing, collection runner, corroboration, scoring.

Note: CollectionRunner, CorroborationEngine, CounterSignalChecker, and Scorer
are NOT re-exported here to avoid circular imports with collectors.base.
Import them directly from their modules.
"""

from osint_pipeline.engine.canonical import (
    canonical_hash,
    canonical_json,
    http_transcript_canonical,
    http_transcript_hash,
    sha256_hex,
)
