# Construct Calibration Pilot — Results Summary

## Construct Under Test

| Field | Value |
|-------|-------|
| Construct | `community_oracle_v1` |
| Template | `CONSTRUCT_CALIBRATION_V1` |
| Execution Path | `replay` (deterministic) |
| Inquiry Class | `INSPECTION` |

## Criteria & Scores

| Criterion | Weight | Score |
|-----------|--------|-------|
| `precision` | 0.40 | 0.8000 |
| `recall` | 0.40 | 0.5417 |
| `reply_accuracy` | 0.20 | 0.8000 |
| **Composite** | — | **0.6967** |

## Evidence & Verification

| Field | Value |
|-------|-------|
| Replay Count | 12 |
| Evidence Bundle Hash | `cabd0288dc5386fbdc8748b8ce6931b1eb6aca2aeadb32a14afaa133788b36c2` |
| Commitment Hash | `1d258c8ce6070b43cd00e1ebe8cc96d0eeba4ccd13162a32ddf5873c18084287` |
| Certificate ID | `a64c7236-d229-5c6d-acb5-b4f6dfc2cd22` |
| Verification Tier | `UNVERIFIED` (12 replays; 50+ required for `BACKTESTED`) |
| MCP `echelon_verify` | **PASS** |

## Independent Verification

```bash
# Re-run pipeline (deterministic — produces identical hash)
python3 scripts/run_construct_calibration.py --construct community_oracle_v1 --output-dir output

# Verify certificate via MCP
echelon_verify verify output/construct_calibration/community_oracle_v1/certificates/CONSTRUCT_CALIBRATION_V1.json output/construct_calibration/community_oracle_v1/evidence/
```

## Notes

- Precision and reply accuracy meet the 0.80 target. Recall is lower (0.54) by design — the fixture dataset models realistic scenarios where constructs miss subtle changes.
- The pipeline is fully deterministic: fixed timestamps, deterministic UUIDs, and bundle cleanup ensure identical evidence hashes across re-runs.
- Tier is `UNVERIFIED` because the dataset contains 12 records (below the 50-replay `BACKTESTED` threshold). Expanding the dataset to 50+ records is a future task.
