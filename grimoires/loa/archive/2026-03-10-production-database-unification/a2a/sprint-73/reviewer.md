# Sprint-73 (Cycle-023 Sprint-0) — Implementation Report

**Sprint:** Grep Sweep + User Model Migration
**Date:** 2026-03-10
**Status:** Complete

---

## Task 1: Grep Sweep

All files importing from `backend.core.database`:

| File | Line | Import | Action Required |
|------|------|--------|-----------------|
| `backend/main.py` | 34 | `SessionLocal, engine, Base, User as DBUser` | **Replace** — Sprint 1 |
| `backend/start.sh` | 35 | `from backend.core.database import engine, Base` | **Replace** — Sprint 1 |
| `backend/IMPORT_FIXES_COMPLETE.md` | 12, 106, 114 | Documentation only | No action |
| `backend/IMPORT_FIX_SUMMARY.md` | 18, 24, 49, 71 | Documentation only | No action |
| `backend/README_DOCKER.md` | 332 | Documentation only | No action |

**Additional consumers needing `USE_MOCKS` removal (Sprint 1):**

| File | USE_MOCKS refs | Action |
|------|---------------|--------|
| `backend/dependencies.py` | 11 | Delete USE_MOCKS var, _EmptyRepo, conditional branches |
| `backend/main.py` | 8 | Delete mock engine warning block |
| `backend/api/butterfly_routes.py` | 16 | Delete mock fallback branches |
| `backend/api/paradox_routes.py` | 14 | Delete mock fallback branches |
| `backend/api/osint_routes.py` | 2 | Delete mock checks |

**Test files (no core.database imports — already on async layer):**
- `backend/test_db.py` — Uses `backend.database.connection` ✓
- `backend/test_db_connection.py` — Uses `backend.database.connection` ✓

---

## Task 2: Verify User Model

**Confirmed** at `backend/database/models.py:78`:

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(20), default="free")
    balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    balance_echelon: Mapped[int] = mapped_column(Integer, default=0)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Relationships: `agents`, `positions`, `watchlist_items`, `private_forks` — all intact.

**Reconciliation notes for auth_routes.py (Sprint 2):**
- `hashed_password` → must use `password_hash`
- `play_money_balance` → must use `balance_usdc` / `balance_echelon`
- `id` type: `String(50)` — use `str(uuid.uuid4())`

---

## Task 3: Alembic Migration

**No new migration needed.** The `users` table already exists in the initial migration:

- File: `backend/alembic/versions/347c30465dba_initial_tables.py`
- Lines 23-37: Creates `users` table with all fields matching the model
- Indexes on `email` (unique) and `username` (unique) included

Full migration chain:
```
347c30465dba_initial_tables
  → a1b2c3d4e5f6_add_verification_tables
    → c014_add_inquiry_class_columns
      → c014c_add_stop_condition_columns
        → c016_engine_coherence
          → c017_policy_surface
            → c018_scenario_packs
              → c020_replay_source_run_id
                → c021_certificate_lifecycle
                  → c022_investigation_templates
```

`alembic upgrade head` creates the `users` table as part of the initial migration.

---

## Task 4: Migration Chain Verification

Alembic env.py (`backend/alembic/env.py`) correctly:
- Reads `DATABASE_URL` from environment
- Converts `postgresql://` to `postgresql+psycopg2://` for sync migrations
- Uses `Base.metadata` from `database.connection` as target

---

## Exit Criteria

- [x] Complete list of files needing `core.database` import changes (2 code files: main.py, start.sh)
- [x] `User` model importable from `backend.database.models` (confirmed at line 78)
- [x] Migration for `users` table exists and applies cleanly (initial migration, line 23)
- [x] Complete USE_MOCKS consumer map (5 files, 51 references)
