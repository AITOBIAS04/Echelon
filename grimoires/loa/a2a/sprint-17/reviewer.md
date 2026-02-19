# Sprint 17 (local sprint-4) — Implementation Report

## Scoring Engine + Certificate Generator

### Tasks Completed

#### 4.1 — ScoringProvider ABC (`scoring/base.py`) ✓
- Abstract base with 4 methods: `score_precision`, `score_recall`, `score_reply_accuracy`, `generate_follow_up_question`
- Return types match SDD §6.3

#### 4.2 — Versioned prompt templates (`scoring/prompts/v1/`) ✓
- 4 prompt files: precision.txt, recall.txt, reply_accuracy.txt, follow_up_question.txt
- manifest.json linking version metadata to files
- All prompts request structured JSON output with defined schemas

#### 4.3 — AnthropicScorer (`scoring/anthropic_scorer.py`) ✓
- Uses `anthropic.AsyncAnthropic` with configurable model and temperature
- `PromptLoader` class loads and caches templates, fills `{placeholders}`
- `_call_llm_json()` with one-retry on JSON parse failure (stricter prompt on retry)
- Strips markdown fences (```` ``` ````) from retry responses
- Records `raw_scoring_output` for audit trail
- All 4 scoring methods implemented

#### 4.4 — CertificateGenerator (`certificate/generator.py`) ✓
- `precision` = mean of all ReplayScore.precision
- `recall` = mean of all ReplayScore.recall
- `reply_accuracy` = mean of all ReplayScore.reply_accuracy
- `composite_score` = weighted average with normalized weights
- `brier` = `(1 - composite_score) * 0.5` for RLMF [0, 0.5] range
- `sample_size` = `replay_count` = len(scores)
- Validates against CalibrationCertificate model
- Raises ValueError on empty scores or all-zero weights

#### 4.5 — Tests ✓
- **test_scoring.py** (9 tests): PromptLoader placeholder fill, caching, unknown key; AnthropicScorer precision/recall/reply_accuracy/follow_up; JSON retry; markdown fence stripping
- **test_certificate.py** (10 tests): mean aggregation, composite weights (equal + custom), Brier score, sample size, model validation, individual scores, empty scores error, zero weights error, JSON round-trip

### Test Results

85 tests passing (19 new in this sprint), 0 failures.

### Files Created/Modified

| File | Action | Lines |
|------|--------|-------|
| `scoring/anthropic_scorer.py` | Created | 127 |
| `certificate/generator.py` | Created | 82 |
| `tests/test_scoring.py` | Created | 176 |
| `tests/test_certificate.py` | Created | 141 |

### Notes

- AnthropicScorer mocked in tests (no live API calls required)
- PromptLoader reads from filesystem at runtime — templates can be updated independently
- CertificateGenerator is deterministic given the same input scores
