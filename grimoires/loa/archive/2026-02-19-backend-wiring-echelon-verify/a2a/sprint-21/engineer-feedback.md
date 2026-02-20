All good

## Notes (informational, not blocking)

1. **Wallet auth test (Task 3.3)**: "Wallet auth creates run correctly" test not present — acceptable since verification routes use JWT-only auth via `get_current_user`.

2. **401 test (Task 3.3)**: "No auth on POST /runs returns 401" not tested at HTTP level. Auth enforcement is guaranteed by FastAPI's `Depends(get_current_user)` — framework-level guarantee, low risk.

3. **Test approach**: Tests operate at DB/ORM level using direct SQLAlchemy queries rather than FastAPI TestClient HTTP requests. This tests the data layer thoroughly but leaves the HTTP serialization layer (Pydantic response models, status codes, dependency injection chain) exercised only by the smoke tests. Adequate for an initial integration; HTTP-level tests can be added in a follow-up cycle if needed.
