All good

## Sprint 89 (Cycle-026a Sprint 0) — Asset Policy + Registry Schema

### Tasks Verified

1. **Registry schema models** — `backend/schemas/eval_asset_registry.py`
   - `RegistryFileEntry`, `DatasetRegistryEntry`, `DatasetRegistryDocument` all present and correctly modeled.
   - `content_hash` validated with `sha256:` prefix via `field_validator` (Pydantic v2 API).
   - `asset_id` validated with regex for filesystem-safe characters.
   - `files` field uses `min_length=1` to reject empty file lists.
   - `Optional[str]` used correctly for the `license` field (not `str | None`, which would need `__future__` on 3.9).

2. **Construct anchor schema** — `backend/schemas/construct_anchor_schema.py`
   - `AnchorClass(str, Enum)` with all 4 values per SDD.
   - `AnchorReference` and `EvaluationDimensionAnchor` match SDD spec exactly.
   - `min_length=1` on required string fields is a good defensive choice.

3. **Asset classification policy** — `backend/services/eval_asset_policy.py`
   - `SNAPSHOT_ASSETS` and `LIVE_ONLY_ASSETS` as `frozenset` (immutable, good).
   - All 8 snapshot and 5 live assets from the PRD are present.
   - `classify_asset` normalizes to lowercase before lookup.
   - `reject_live_as_immutable` provides the enforcement gate with clear error messages.
   - `validate_snapshot_candidate` returns a `(bool, str)` tuple for callers that want the reason without an exception.

### Tests: 14 (exceeds sprint plan target of 8)

Sprint plan called for 8 tests; implementation delivers 14. The additional 6 tests add coverage for:
- Invalid `asset_id` character validation
- Registry document round-trip serialization
- `RegistryFileEntry` hash validation in isolation
- Unknown asset classification
- Case-insensitive classification
- Anchor class enum value completeness

All 14 pass on Python 3.9.6 with Pydantic 2.12.5.

### Observations

- No hardcoded developer paths.
- Pydantic v2 `field_validator` + `@classmethod` used correctly throughout.
- `list[...]` lowercase generics work on Python 3.9 because `list.__class_getitem__` was added in 3.9. Pydantic v2 processes these correctly at class definition time. No issue.
- Clean separation of concerns: schemas define shape, policy defines rules, no cross-contamination.
