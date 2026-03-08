# SDD — Cycle-021: Investigation Certificate Lifecycle + Domain Filter Enforcement

**Cycle:** cycle-021
**Date:** 7 March 2026
**PRD:** `grimoires/loa/prd.md`
**Builder:** Loa (backend/runtime only)

> Sources: PRD FR-1 through FR-4; codebase exploration of `backend/investigation/`, `backend/api/investigation_routes.py`, `backend/database/models.py`, `backend/websockets/realtime_manager.py`, `backend/services/`

---

## 1. Executive Summary

Cycle-021 closes 4 gaps in the investigation certificate pipeline:

1. **Domain filter enforcement** — a reusable validator that rejects out-of-scope evidence/signals at ingestion time
2. **Automated stop condition evaluation** — an orchestrator that evaluates stop conditions after every material mutation (drift, evidence, counter-signal, claim change)
3. **Certificate lifecycle state machine** — READY / ANCHORED / ISSUED with persisted timestamps and no skippable states
4. **Daily batch anchor** — certificates are only ISSUED during the 00:00 UTC batch window; readiness can precede issuance by hours

All 4 items are backend-only. Alexander consumes the API and WebSocket events.

---

## 2. System Architecture

### 2.1 Component Interaction

```
                    API Layer (investigation_routes.py)
                    ┌──────────────────────────────────┐
                    │  POST /{id}/evidence              │
                    │  POST /{id}/counter-signals       │
                    │  POST /{id}/drift                 │
  Ingestion ───────►│  POST /{id}/certificate/build     │
                    │  GET  /{id}/certificate            │
                    │  GET  /{id}/readiness              │
                    │  POST /certificates/anchor-batch   │
                    └──────┬───────────────────────────┘
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
   DomainFilterValidator  StopCondition   CertificateLifecycle
   (pure function)        Orchestrator    Service
              │            │                │
              │            ▼                ▼
              │   InvestigationStop    InvestigationCertificate
              │   ConditionEvaluator  Builder (existing)
              │   (existing)               │
              │            │                │
              ▼            ▼                ▼
         ┌─────────────────────────────────────┐
         │  InvestigationRepository (existing)  │
         │  + new columns on Investigation      │
         │  + new columns on CertificateRecord  │
         └──────────────┬──────────────────────┘
                        │
                        ▼
                   WebSocket Manager
                   (realtime_manager.py)
```

### 2.2 Data Flow per Mutation Path

**Evidence submission** (`POST /{id}/evidence`):
1. DomainFilterValidator.validate() — reject if out-of-scope
2. Existing evidence persistence
3. StopConditionOrchestrator.evaluate_after_mutation() — check readiness
4. Existing paradox-risk recompute

**Counter-signal ingestion** (`POST /{id}/counter-signals`):
1. DomainFilterValidator.validate() — reject if out-of-scope
2. Existing counter-signal persistence
3. StopConditionOrchestrator.evaluate_after_mutation()

**Drift event** (`POST /{id}/drift`):
1. Existing drift persistence
2. StopConditionOrchestrator.evaluate_after_mutation() — includes material drift as factor

**Certificate build** (`POST /{id}/certificate/build`):
1. Verify stop conditions are satisfied (or override)
2. Build certificate via existing builder
3. CertificateLifecycleService.transition_to_ready()
4. Investigation status → CERTIFICATE_READY

**Batch anchor** (`POST /certificates/anchor-batch`):
1. CertificateLifecycleService.run_batch_anchor()
2. READY → ANCHORED → ISSUED for all qualifying certificates
3. Investigation status → COMPLETED for each
4. WebSocket events emitted per certificate

---

## 3. Technology Stack

No new dependencies. All work uses existing stack:

| Layer | Technology | Notes |
|-------|-----------|-------|
| Runtime | Python 3.11+ | Existing |
| Web framework | FastAPI | Existing |
| ORM | SQLAlchemy 2.0 (async) | Existing |
| Database | SQLite (dev) / PostgreSQL (prod) | Existing |
| Migrations | Alembic | Existing |
| WebSocket | FastAPI WebSocket + ConnectionManager | Existing singleton |
| Validation | Pydantic v2 | Existing |
| Hashing | hashlib (SHA-256) | Existing stdlib |

---

## 4. Component Design

### 4.1 DomainFilterValidator

**File:** `backend/services/domain_filter_validator.py`

**Design:** Pure function, no DB access. Takes domain filters and source metadata, returns pass/fail.

```python
# Imports
from backend.investigation.signal_scanner import DomainFilter, DOMAIN_FILTER_SOURCE_GROUPS

class DomainFilterViolation(Exception):
    """Raised when evidence/signal source is outside committed domain filters."""
    def __init__(self, source: str, allowed_sources: list[str], domain_filters: list[str]):
        self.source = source
        self.allowed_sources = allowed_sources
        self.domain_filters = domain_filters
        super().__init__(
            f"Source '{source}' is outside committed domain filters {domain_filters}. "
            f"Allowed sources: {allowed_sources}"
        )

def get_allowed_sources(domain_filters: list[str]) -> set[str]:
    """Expand domain filter enum values into the set of allowed source groups.

    Uses DOMAIN_FILTER_SOURCE_GROUPS mapping from signal_scanner.py.
    Returns empty set if domain_filters is empty (no enforcement).
    """
    allowed: set[str] = set()
    for df_value in domain_filters:
        try:
            df = DomainFilter(df_value)
        except ValueError:
            continue  # unknown filter — skip gracefully
        allowed.update(DOMAIN_FILTER_SOURCE_GROUPS.get(df, []))
    return allowed

def validate_evidence_source(
    domain_filters_json: list[str],
    source_id: str,
    source_description: str = "",
) -> None:
    """Validate that evidence source falls within committed domain filters.

    No-op if domain_filters_json is empty (backward compatible).
    Raises DomainFilterViolation if source is out of scope.
    """
    if not domain_filters_json:
        return  # no enforcement

    allowed = get_allowed_sources(domain_filters_json)
    if not allowed:
        return  # no resolvable filters — no enforcement

    # Match source_id against allowed source groups
    # source_id format examples: "market_data", "corporate_filing", "maritime_ais"
    if source_id and source_id not in allowed:
        raise DomainFilterViolation(source_id, sorted(allowed), domain_filters_json)

def validate_signal_source(
    domain_filters_json: list[str],
    detection_method: str,
    source_ref: str = "",
) -> None:
    """Validate counter-signal/scanner source against domain filters.

    Same logic as evidence but checks detection_method and source_ref.
    No-op if domain_filters_json is empty.
    Raises DomainFilterViolation if out of scope.
    """
    if not domain_filters_json:
        return

    allowed = get_allowed_sources(domain_filters_json)
    if not allowed:
        return

    # For automated signals, source_ref indicates the source group
    source_to_check = source_ref or detection_method
    if source_to_check and source_to_check not in allowed:
        # "automated_osint" and "human_submitted" are meta-methods, always allowed
        if source_to_check in ("automated_osint", "paradox_engine", "human_submitted"):
            return
        raise DomainFilterViolation(source_to_check, sorted(allowed), domain_filters_json)
```

**Key decisions:**
- **Pure function** — no session param, no DB access. Caller fetches investigation and passes `domain_filters_json`.
- **Empty filters = no enforcement** — backward compatible per PRD.
- **Uses existing `DOMAIN_FILTER_SOURCE_GROUPS`** mapping from `signal_scanner.py` — single source of truth for domain-to-source mapping.
- **Custom exception** — `DomainFilterViolation` carries source, allowed list, and filters for clear 422 responses.
- **Meta-methods pass through** — `automated_osint`, `paradox_engine`, `human_submitted` are detection methods, not domain sources.

### 4.2 StopConditionOrchestrator

**File:** `backend/services/stop_condition_orchestrator.py`

**Design:** Async service function that wraps `InvestigationStopConditionEvaluator` with automatic triggering, drift awareness, and persistence.

```python
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Investigation
from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
from backend.investigation.commitment_monitor import CommitmentMonitor, DriftImpact
from backend.investigation.toolset import InvestigationToolset, InvestigationConfig
from backend.websockets.realtime_manager import manager as ws_manager

class StopConditionResult:
    """Immutable result of stop condition evaluation."""
    __slots__ = ("ready", "reason", "drift_material", "trigger")

    def __init__(self, ready: bool, reason: str, drift_material: bool, trigger: str):
        self.ready = ready
        self.reason = reason
        self.drift_material = drift_material
        self.trigger = trigger  # "drift" | "evidence" | "counter_signal" | "claim" | "manual"

async def evaluate_after_mutation(
    session: AsyncSession,
    investigation: Investigation,
    trigger: str,
    time_remaining: float | None = None,
) -> StopConditionResult:
    """Evaluate stop conditions after a material mutation.

    Rebuilds toolset from DB state, checks drift, evaluates stop condition,
    persists result to investigation record, emits WS event on readiness change.

    Args:
        session: Active async session (caller manages transaction).
        investigation: Eagerly-loaded Investigation with relationships.
        trigger: What caused this evaluation.
        time_remaining: Override for time-based stop conditions. If None, computed from stop_config.

    Returns:
        StopConditionResult with ready/not-ready + reason.
    """
    # Skip if investigation is already completed or has certificate
    if investigation.status in ("COMPLETED", "CERTIFICATE_READY"):
        return StopConditionResult(
            ready=True,
            reason="already_ready_or_completed",
            drift_material=False,
            trigger=trigger,
        )

    # Rebuild toolset from persisted state
    config = InvestigationConfig(
        domain_filters=investigation.domain_filters_json or [],
        stop_condition=investigation.stop_condition,
        stop_config=investigation.stop_config_json or {},
    )
    toolset = InvestigationToolset(
        config=config,
        theatre_id=investigation.theatre_id,
        construct_id=investigation.construct_id,
        inquiry_class=investigation.inquiry_class,
    )
    toolset.rebuild_from_persisted(investigation)

    # Check material drift
    has_drift = toolset.commitment_monitor.has_material_drift()

    # Compute time_remaining if not provided
    if time_remaining is None:
        time_remaining = _compute_time_remaining(investigation.stop_config_json or {})

    # Evaluate stop condition
    evaluator = InvestigationStopConditionEvaluator()
    ready, reason = evaluator.evaluate(
        stop_condition=investigation.stop_condition,
        stop_config=investigation.stop_config_json or {},
        claim_graph=toolset.claim_graph,
        evidence_envelope=toolset.evidence_envelope,
        time_remaining=time_remaining,
    )

    # Augment reason with drift state
    if has_drift and trigger == "drift":
        reason = f"drift_material;{reason}"

    # Persist evaluation result
    old_status = investigation.stop_condition_status
    investigation.stop_condition_status = "READY" if ready else "NOT_READY"
    investigation.stop_condition_reason = reason
    investigation.stop_condition_evaluated_at = datetime.now(timezone.utc)
    await session.flush()

    # Emit WS event if readiness changed
    if ready and old_status != "READY":
        await ws_manager.broadcast_global(
            "INVESTIGATION_STOP_CONDITION_MET",
            {
                "investigation_id": investigation.id,
                "reason": reason,
                "trigger": trigger,
                "drift_material": has_drift,
            },
        )

    return StopConditionResult(
        ready=ready,
        reason=reason,
        drift_material=has_drift,
        trigger=trigger,
    )


def _compute_time_remaining(stop_config: dict) -> float:
    """Compute seconds remaining from stop_config milestone or deadline."""
    milestone_str = stop_config.get("milestone_timestamp")
    if milestone_str:
        try:
            milestone = datetime.fromisoformat(milestone_str)
            if milestone.tzinfo is None:
                milestone = milestone.replace(tzinfo=timezone.utc)
            return (milestone - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError):
            pass
    # Default: no time constraint (large positive)
    return 999_999.0
```

**Key decisions:**
- **Follows existing service pattern** — async function, takes `session: AsyncSession`, flushes (doesn't commit).
- **Rebuilds toolset** from persisted investigation state (same pattern as certificate endpoint).
- **Drift augments reason** — when trigger is "drift" and drift is material, prefixes reason with `drift_material;`.
- **Only emits WS on state change** — prevents event spam on repeated evaluations.
- **`time_remaining` computed from `stop_config`** — OUTCOME_RESOLUTION and SPONSOR_DEFINED use `milestone_timestamp`.
- **Skips already-completed investigations** — idempotent.

### 4.3 CertificateLifecycleService

**File:** `backend/services/certificate_lifecycle_service.py`

**Design:** Async service with state machine enforcement and batch anchor logic.

```python
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Investigation, InvestigationCertificateRecord
from backend.websockets.realtime_manager import manager as ws_manager

# Certificate Status Constants
CERT_STATUS_READY = "READY"
CERT_STATUS_ANCHORED = "ANCHORED"
CERT_STATUS_ISSUED = "ISSUED"

# Valid Transitions
_VALID_TRANSITIONS = {
    CERT_STATUS_READY: CERT_STATUS_ANCHORED,
    CERT_STATUS_ANCHORED: CERT_STATUS_ISSUED,
}


async def transition_to_ready(
    session: AsyncSession,
    certificate: InvestigationCertificateRecord,
    investigation: Investigation,
) -> InvestigationCertificateRecord:
    """Transition certificate to READY state.

    Called after certificate is built. Sets ready_at, does NOT set issued_at.
    Investigation status becomes CERTIFICATE_READY.

    Raises ValueError if certificate already has a status beyond READY.
    """
    if hasattr(certificate, "certificate_status") and certificate.certificate_status:
        if certificate.certificate_status != CERT_STATUS_READY:
            raise ValueError(
                f"Cannot transition to READY: certificate is already "
                f"'{certificate.certificate_status}'"
            )

    certificate.certificate_status = CERT_STATUS_READY
    certificate.ready_at = datetime.now(timezone.utc)

    investigation.status = "CERTIFICATE_READY"
    await session.flush()

    await ws_manager.broadcast_global(
        "INVESTIGATION_CERTIFICATE_READY",
        {
            "investigation_id": investigation.id,
            "certificate_id": certificate.id,
            "ready_at": certificate.ready_at.isoformat(),
        },
    )

    return certificate


async def run_batch_anchor(
    session: AsyncSession,
    batch_timestamp: datetime | None = None,
) -> list[str]:
    """Process all READY certificates in a single batch.

    1. Query all certificates with certificate_status = 'READY'
    2. Compute batch anchor hash (SHA-256 of sorted certificate hashes)
    3. Transition each to ANCHORED with batch_anchor_hash
    4. Transition each to ISSUED with issued_at = batch_timestamp
    5. Mark investigations as COMPLETED
    6. Emit WS events

    Returns list of issued certificate IDs.
    Idempotent: if no READY certificates exist, returns empty list.
    """
    if batch_timestamp is None:
        batch_timestamp = datetime.now(timezone.utc)

    # 1. Query READY certificates
    result = await session.execute(
        select(InvestigationCertificateRecord)
        .where(InvestigationCertificateRecord.certificate_status == CERT_STATUS_READY)
    )
    ready_certs = list(result.scalars().all())

    if not ready_certs:
        return []  # idempotent no-op

    # 2. Compute batch anchor hash
    sorted_hashes = sorted(cert.certificate_hash for cert in ready_certs)
    batch_hash_input = json.dumps(sorted_hashes, separators=(",", ":"))
    batch_anchor_hash = hashlib.sha256(batch_hash_input.encode()).hexdigest()

    issued_ids: list[str] = []

    for cert in ready_certs:
        # 3. READY -> ANCHORED
        cert.certificate_status = CERT_STATUS_ANCHORED
        cert.anchored_at = batch_timestamp
        cert.batch_anchor_hash = batch_anchor_hash

        # 4. ANCHORED -> ISSUED
        cert.certificate_status = CERT_STATUS_ISSUED
        cert.issued_at = batch_timestamp

        # 5. Mark investigation COMPLETED
        investigation = await session.get(Investigation, cert.investigation_id)
        if investigation:
            investigation.status = "COMPLETED"
            investigation.completed_at = batch_timestamp

        issued_ids.append(cert.id)

    await session.flush()

    # 6. Emit WS events (after flush to ensure persistence)
    for cert in ready_certs:
        await ws_manager.broadcast_global(
            "INVESTIGATION_CERTIFICATE_ISSUED",
            {
                "investigation_id": cert.investigation_id,
                "certificate_id": cert.id,
                "issued_at": batch_timestamp.isoformat(),
                "batch_anchor_hash": batch_anchor_hash,
            },
        )

    return issued_ids
```

**Key decisions:**
- **READY -> ANCHORED -> ISSUED in batch** — both transitions happen atomically in `run_batch_anchor()`. The intermediate ANCHORED state is persisted (with `anchored_at` and `batch_anchor_hash`) but the batch processes both transitions in a single call.
- **Batch anchor hash** — SHA-256 of JSON array of sorted certificate hashes. Deterministic.
- **Idempotent** — queries only READY certificates. Second run finds none, returns empty list.
- **`issued_at` = batch timestamp** — not certificate build time, per PRD.
- **Investigation COMPLETED only after ISSUED** — never at READY time.
- **`transition_to_ready` is separate** — called from certificate build endpoint, not from batch.

---

## 5. Data Architecture

### 5.1 Schema Changes

#### Table: `investigations` (existing — add 3 columns)

| Column | Type | Default | Nullable | Purpose |
|--------|------|---------|----------|---------|
| `stop_condition_status` | String(20) | `NULL` | Yes | `"READY"` or `"NOT_READY"` — persisted evaluation result |
| `stop_condition_reason` | String(500) | `NULL` | Yes | Human-readable reason from evaluator |
| `stop_condition_evaluated_at` | DateTime | `NULL` | Yes | When last evaluated |

**Status values extended:** `ACTIVE` | `CERTIFICATE_READY` | `COMPLETED`

`CERTIFICATE_READY` is a new intermediate status set when certificate is built but not yet issued.

#### Table: `investigation_certificates` (existing — add 4 columns)

| Column | Type | Default | Nullable | Purpose |
|--------|------|---------|----------|---------|
| `certificate_status` | String(20) | `"READY"` | No | `READY` / `ANCHORED` / `ISSUED` |
| `ready_at` | DateTime | `NULL` | Yes | When certificate entered READY state |
| `anchored_at` | DateTime | `NULL` | Yes | When included in batch anchor |
| `batch_anchor_hash` | String(64) | `NULL` | Yes | SHA-256 of the batch anchor |

**Existing `issued_at`:** Semantics change — no longer set at build time. Set only during batch anchor.

**Existing `anchoring_status`:** Deprecated in favor of `certificate_status`. Left in place for backward compatibility but no longer written to by new code.

### 5.2 Alembic Migration

**File:** `backend/alembic/versions/c021_certificate_lifecycle.py`

**Revision chain:** `c020_replay_source_run_id` -> `c021_certificate_lifecycle`

```python
revision = "c021_certificate_lifecycle"
down_revision = "c020_replay_source_run_id"
```

**Operations (all idempotent with column-existence checks):**

1. Add `stop_condition_status` to `investigations`
2. Add `stop_condition_reason` to `investigations`
3. Add `stop_condition_evaluated_at` to `investigations`
4. Add `certificate_status` to `investigation_certificates` (default `'READY'`)
5. Add `ready_at` to `investigation_certificates`
6. Add `anchored_at` to `investigation_certificates`
7. Add `batch_anchor_hash` to `investigation_certificates`

**Downgrade:** Drop all 7 columns.

### 5.3 Model Changes

**`backend/database/models.py` — Investigation class:**

```python
# Add after existing fields:
stop_condition_status: Mapped[Optional[str]] = mapped_column(
    String(20), nullable=True, default=None,
    comment="READY | NOT_READY — persisted stop condition evaluation result"
)
stop_condition_reason: Mapped[Optional[str]] = mapped_column(
    String(500), nullable=True, default=None,
)
stop_condition_evaluated_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True, default=None,
)
```

**Status comment update:** `"ACTIVE | CERTIFICATE_READY | COMPLETED"`

**`backend/database/models.py` — InvestigationCertificateRecord class:**

```python
# Add after existing fields:
certificate_status: Mapped[str] = mapped_column(
    String(20), default="READY",
    comment="READY | ANCHORED | ISSUED"
)
ready_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True, default=None,
)
anchored_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime, nullable=True, default=None,
)
batch_anchor_hash: Mapped[Optional[str]] = mapped_column(
    String(64), nullable=True, default=None,
    comment="SHA-256 of batch anchor (sorted cert hashes)"
)
```

---

## 6. API Design

### 6.1 Modified Endpoints

#### `POST /api/v1/investigations/{investigation_id}/evidence`

**Change:** Add domain filter validation before acceptance.

```python
# In route handler, before existing evidence persistence:
investigation = await repo.get(investigation_id)
validate_evidence_source(
    domain_filters_json=investigation.domain_filters_json or [],
    source_id=body.source_id,
    source_description=body.source_description,
)
# ... existing evidence submission logic ...

# After persistence, trigger stop condition evaluation:
await evaluate_after_mutation(session, investigation, trigger="evidence")
```

**Error response on violation:**
```json
{
    "detail": "Source 'cyber_threat' is outside committed domain filters ['corporate_and_entity', 'finance_and_markets']. Allowed sources: ['corporate_filing', 'entity_resolution', 'market_data', 'central_bank', 'official_gov', 'prediction_market']"
}
```
HTTP 422 Unprocessable Entity.

#### `POST /api/v1/investigations/{investigation_id}/counter-signals`

**Change:** Add domain filter validation + stop condition evaluation.

```python
validate_signal_source(
    domain_filters_json=investigation.domain_filters_json or [],
    detection_method=body.detection_method,
    source_ref=body.source_ref if hasattr(body, 'source_ref') else "",
)
# ... existing counter-signal logic ...
await evaluate_after_mutation(session, investigation, trigger="counter_signal")
```

#### `POST /api/v1/investigations/{investigation_id}/drift`

**Change:** Trigger stop condition evaluation after drift persistence.

```python
# ... existing drift persistence ...
await evaluate_after_mutation(session, investigation, trigger="drift")
```

#### `GET /api/v1/investigations/{investigation_id}/certificate`

**Change:** Returns current certificate state without building. No longer triggers certificate construction.

```python
@router.get("/{investigation_id}/certificate")
async def get_certificate(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Return current certificate state (READY/ANCHORED/ISSUED) without building."""
    investigation = await repo.get(investigation_id)
    if not investigation:
        raise HTTPException(404, "Investigation not found")
    if not investigation.certificate:
        raise HTTPException(404, "No certificate exists. Use POST .../certificate/build.")
    cert = investigation.certificate
    return {
        "certificate_id": cert.id,
        "investigation_id": cert.investigation_id,
        "certificate_status": cert.certificate_status,
        "certificate_hash": cert.certificate_hash,
        "routing_decision": cert.routing_decision,
        "routing_reason": cert.routing_reason,
        "ready_at": cert.ready_at.isoformat() if cert.ready_at else None,
        "anchored_at": cert.anchored_at.isoformat() if cert.anchored_at else None,
        "issued_at": cert.issued_at.isoformat() if cert.issued_at else None,
        "batch_anchor_hash": cert.batch_anchor_hash,
        "certificate_json": cert.certificate_json,
    }
```

### 6.2 New Endpoints

#### `POST /api/v1/investigations/{investigation_id}/certificate/build`

**Purpose:** Build certificate and transition to READY. Replaces the old GET behavior.

```python
@router.post("/{investigation_id}/certificate/build")
async def build_certificate(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Build certificate and transition to READY.

    Prerequisites: Investigation must be ACTIVE with stop conditions satisfied.
    Result: Certificate persisted with status=READY, investigation=CERTIFICATE_READY.
    """
    investigation = await repo.get(investigation_id)
    if not investigation:
        raise HTTPException(404, "Investigation not found")
    if investigation.certificate:
        raise HTTPException(409, "Certificate already exists")

    # Rebuild toolset and build certificate (existing logic)
    toolset = _rebuild_toolset(investigation)
    cert_model = toolset.build_certificate()

    # Persist certificate record (modified: does NOT set COMPLETED)
    cert_record = await repo.persist_certificate_as_ready(
        investigation_id=investigation_id,
        certificate_hash=cert_model.certificate_hash,
        certificate_json=cert_model.model_dump(mode="json"),
        routing_decision=cert_model.routing_decision,
        routing_reason=cert_model.routing_reason,
    )

    # Transition to READY via lifecycle service
    await transition_to_ready(db, cert_record, investigation)

    # Trigger paradox-risk recompute
    await _recompute_theatre_paradox_risk(
        db, investigation.theatre_id, investigation.inquiry_class,
        trigger_reason="certificate_ready",
    )

    return {
        "certificate_id": cert_record.id,
        "certificate_status": cert_record.certificate_status,
        "certificate_hash": cert_record.certificate_hash,
        "ready_at": cert_record.ready_at.isoformat() if cert_record.ready_at else None,
        "routing_decision": cert_record.routing_decision,
    }
```

#### `POST /api/v1/investigations/certificates/anchor-batch`

**Purpose:** Trigger daily batch anchor. Admin/cron endpoint.

```python
@router.post("/certificates/anchor-batch")
async def anchor_batch(db: AsyncSession = Depends(get_db)):
    """Process all READY certificates in a batch anchor.

    Transitions READY -> ANCHORED -> ISSUED atomically.
    Idempotent: second call is a no-op if no READY certificates exist.
    """
    issued_ids = await run_batch_anchor(db)
    return {
        "issued_count": len(issued_ids),
        "issued_certificate_ids": issued_ids,
        "batch_timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

#### `GET /api/v1/investigations/{investigation_id}/readiness`

**Purpose:** Return stop condition evaluation status.

```python
@router.get("/{investigation_id}/readiness")
async def get_readiness(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Return current stop condition evaluation status."""
    investigation = await repo.get(investigation_id)
    if not investigation:
        raise HTTPException(404, "Investigation not found")
    return {
        "investigation_id": investigation.id,
        "status": investigation.status,
        "stop_condition": investigation.stop_condition,
        "stop_condition_status": investigation.stop_condition_status,
        "stop_condition_reason": investigation.stop_condition_reason,
        "stop_condition_evaluated_at": (
            investigation.stop_condition_evaluated_at.isoformat()
            if investigation.stop_condition_evaluated_at else None
        ),
        "has_certificate": investigation.certificate is not None,
        "certificate_status": (
            investigation.certificate.certificate_status
            if investigation.certificate else None
        ),
    }
```

---

## 7. WebSocket Events

All events use existing `ConnectionManager.broadcast_global()` pattern. Message format: `{"type": <event_type>, "timestamp": <iso>, "data": <payload>}`.

| Event Type | Payload | Trigger |
|-----------|---------|---------|
| `INVESTIGATION_STOP_CONDITION_MET` | `{investigation_id, reason, trigger, drift_material}` | `evaluate_after_mutation()` determines readiness (state change from NOT_READY to READY) |
| `INVESTIGATION_CERTIFICATE_READY` | `{investigation_id, certificate_id, ready_at}` | `transition_to_ready()` |
| `INVESTIGATION_CERTIFICATE_ISSUED` | `{investigation_id, certificate_id, issued_at, batch_anchor_hash}` | `run_batch_anchor()` per certificate |

Existing event `INVESTIGATION_STATUS_CHANGED` continues to fire for status transitions but is NOT emitted from the new certificate build path (since we now emit the more specific events above).

---

## 8. Repository Changes

### 8.1 InvestigationRepository Modifications

**`persist_certificate_as_ready()`** — New method replacing part of `persist_certificate()`:

```python
async def persist_certificate_as_ready(
    self,
    investigation_id: str,
    certificate_hash: str,
    certificate_json: dict,
    routing_decision: str,
    routing_reason: str = "",
) -> InvestigationCertificateRecord:
    """Persist certificate record in READY state.

    Unlike persist_certificate(), does NOT set investigation to COMPLETED.
    Does NOT set issued_at. Sets certificate_status='READY' and ready_at.
    """
    cert = InvestigationCertificateRecord(
        investigation_id=investigation_id,
        certificate_hash=certificate_hash,
        certificate_json=certificate_json,
        routing_decision=routing_decision,
        routing_reason=routing_reason,
        certificate_status="READY",
        ready_at=datetime.now(timezone.utc),
    )
    self._session.add(cert)
    await self._session.flush()
    return cert
```

**Existing `persist_certificate()`** — Kept for backward compatibility but deprecated. If called, it sets `certificate_status='ISSUED'` and `issued_at` for legacy behavior.

---

## 9. Integration Points

### 9.1 Existing Toolset Rebuild

The `InvestigationToolset.rebuild_from_persisted(investigation)` method (existing) rebuilds in-memory tool state from DB-persisted investigation. Used by:
- Certificate build endpoint (existing)
- Stop condition orchestrator (new — needs toolset for claim_graph and evidence_envelope)

No changes needed to `rebuild_from_persisted()` itself.

### 9.2 Paradox Risk Orchestrator

Existing `_recompute_theatre_paradox_risk()` is called from:
- Evidence submission (existing)
- Certificate build (existing, reason changes from `"investigation_completed"` to `"certificate_ready"`)
- Batch anchor (new — with reason `"investigation_completed"`)

### 9.3 Signal Scanner

`DOMAIN_FILTER_SOURCE_GROUPS` is imported by `DomainFilterValidator` but not modified. The scanner itself is not changed.

---

## 10. Security Architecture

### 10.1 Domain Filter Enforcement

- **Enforcement boundary:** API layer (routes), before any persistence.
- **Bypass prevention:** `DomainFilterValidator` is called in every ingestion path. No path to submit evidence without passing through validation.
- **Empty filters = open:** Backward compatible. Only committed investigations with non-empty `domain_filters_json` enforce.

### 10.2 Batch Anchor Endpoint

- `POST /certificates/anchor-batch` — should be restricted to admin/cron callers in production. For v1, no auth gate (internal network only).
- Idempotent — safe to call repeatedly.

### 10.3 Certificate Immutability

- Once a certificate reaches `ISSUED` status, no further mutations are allowed.
- `issued_at` is only set during batch anchor — cannot be set via any other path.
- `certificate_hash` is computed at build time and never changes.

---

## 11. Testing Strategy

### 11.1 DomainFilterValidator Tests

| Test | Description |
|------|-------------|
| `test_validate_in_scope_evidence_passes` | Evidence with source_id in allowed sources passes |
| `test_validate_out_of_scope_evidence_rejected` | Evidence with source_id outside allowed sources raises DomainFilterViolation |
| `test_validate_empty_filters_passes_all` | Empty domain_filters_json = no enforcement |
| `test_validate_signal_out_of_scope_rejected` | Counter-signal source outside domain raises violation |
| `test_validate_meta_methods_always_pass` | `automated_osint`, `human_submitted` always allowed |
| `test_get_allowed_sources_expands_correctly` | Domain filter enum values expand to correct source groups |

### 11.2 StopConditionOrchestrator Tests

| Test | Description |
|------|-------------|
| `test_evaluate_persists_ready_status` | Evaluation result written to investigation fields |
| `test_evaluate_emits_ws_on_readiness_change` | WS event fired when NOT_READY -> READY |
| `test_evaluate_no_ws_when_already_ready` | No WS event when status unchanged |
| `test_drift_trigger_includes_drift_in_reason` | Material drift trigger augments reason string |
| `test_skips_completed_investigation` | Returns early for COMPLETED/CERTIFICATE_READY |
| `test_evidence_trigger_evaluates_stop` | Evidence trigger calls evaluator correctly |

### 11.3 CertificateLifecycleService Tests

| Test | Description |
|------|-------------|
| `test_transition_to_ready_sets_fields` | Sets certificate_status=READY, ready_at, investigation=CERTIFICATE_READY |
| `test_transition_to_ready_no_issued_at` | ready_at set, issued_at is None |
| `test_batch_anchor_transitions_ready_to_issued` | READY -> ANCHORED -> ISSUED with correct timestamps |
| `test_batch_anchor_computes_hash` | Batch hash = SHA-256 of sorted cert hashes |
| `test_batch_anchor_idempotent` | Second call returns empty list |
| `test_batch_anchor_sets_completed` | Investigation status = COMPLETED after ISSUED |
| `test_batch_anchor_emits_ws_per_cert` | One WS event per issued certificate |
| `test_cannot_skip_to_issued` | Cannot set ISSUED without going through ANCHORED |

### 11.4 API Integration Tests

| Test | Description |
|------|-------------|
| `test_evidence_rejected_422_on_domain_violation` | POST evidence with out-of-scope source returns 422 |
| `test_drift_triggers_stop_evaluation` | POST drift updates stop_condition_status |
| `test_get_certificate_returns_state` | GET certificate returns READY/ANCHORED/ISSUED |
| `test_build_certificate_creates_ready` | POST certificate/build creates READY cert |
| `test_anchor_batch_issues_all_ready` | POST anchor-batch processes all READY certs |
| `test_readiness_endpoint_returns_status` | GET readiness returns evaluation state |

### 11.5 Test Infrastructure

Following existing patterns:
- **Sync `Session` with SQLite in-memory** for unit tests
- **Selective table creation** (investigation tables only)
- **Direct service function calls** (not through API for unit tests)
- **Mock `ws_manager`** for WebSocket event assertions
- **`_setup_base()` helpers** for investigation + evidence + claims setup

---

## 12. File Manifest

### New Files

| File | Purpose |
|------|---------|
| `backend/services/domain_filter_validator.py` | Domain filter enforcement (pure functions) |
| `backend/services/stop_condition_orchestrator.py` | Automatic stop condition evaluation |
| `backend/services/certificate_lifecycle_service.py` | READY/ANCHORED/ISSUED state machine + batch anchor |
| `backend/alembic/versions/c021_certificate_lifecycle.py` | Migration for 7 new columns |
| `backend/tests/test_c021_domain_filter_validator.py` | Domain filter tests |
| `backend/tests/test_c021_stop_condition_orchestrator.py` | Stop condition orchestrator tests |
| `backend/tests/test_c021_certificate_lifecycle.py` | Certificate lifecycle + batch anchor tests |

### Modified Files

| File | Change |
|------|--------|
| `backend/database/models.py` | Add 3 columns to Investigation, 4 columns to InvestigationCertificateRecord |
| `backend/api/investigation_routes.py` | Add domain filter validation to evidence/counter-signal endpoints; refactor certificate endpoint; add build, batch, readiness endpoints |
| `backend/database/repositories/investigation_repository.py` | Add `persist_certificate_as_ready()` method |
| `backend/websockets/realtime_manager.py` | Add 3 new broadcast methods for investigation certificate events |

### Unchanged Files

| File | Why Unchanged |
|------|--------------|
| `backend/investigation/certificate.py` | Certificate builder logic unchanged; lifecycle is external |
| `backend/investigation/stop_conditions.py` | Evaluator unchanged; orchestrator wraps it |
| `backend/investigation/signal_scanner.py` | Scanner unchanged; validator imports its mapping |
| `backend/investigation/commitment_monitor.py` | Monitor unchanged; orchestrator reads its state |
| `backend/investigation/toolset.py` | Toolset unchanged; rebuild_from_persisted works as-is |

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Domain filter validation rejects legitimate evidence with ambiguous source_id | Medium | Meta-methods (automated_osint, human_submitted) always pass through; empty filters = no enforcement |
| Stop condition evaluation adds latency to every mutation | Low | Evaluation is lightweight: rebuild toolset + pure function. No additional DB queries beyond the eager-loaded investigation |
| Certificate GET behavior change breaks existing consumers | Medium | GET still works, returns current state. Build is now POST. Document migration path for Alexander |
| Batch anchor clock sensitivity | Low | Batch is idempotent; manual trigger available; timestamp is parameterizable for testing |
| Migration on production DB with existing certificates | Low | New columns are nullable or have defaults. Existing certificates get `certificate_status='READY'` default, which is semantically correct (they can be re-issued via batch) |

---

## 14. Future Considerations

**Out of scope for C021 but noted:**

- **Blockchain anchoring** — `batch_anchor_hash` is a local SHA-256 for v1. Future cycles could submit to a blockchain and store the tx hash in `anchoring_tx_hash`.
- **Certificate revocation** — no revocation mechanism exists. ISSUED is final.
- **Batch scheduling** — v1 uses manual trigger. Future: cron job or scheduled task at 00:00 UTC.
- **Channel-scoped WS events** — current events use `broadcast_global`. Future: scope to `investigation:{id}` channel for targeted delivery.
