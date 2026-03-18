# Review Feedback — sprint-bug-4

All good

## Review Notes

- Route fix is correct and surgical
- Gate logic matches the triage behavior matrix exactly
- DEFERRED path correctly preserves cert without transitioning
- REJECTED path marks registration FAILED without lifecycle transition
- Backward compatibility for pre-037 runs is preserved (default READY)
- `run_evaluation.py` also fixed (same pattern, consistency)
- Tests cover all issuance states (7 new tests)
- 49/49 tests pass
- Response still surfaces `issuance_status` so callers see DEFERRED/REJECTED
