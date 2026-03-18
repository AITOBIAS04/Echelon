# SDD — Cycle-026a: Construct Evidence Anchoring + R2 Ingest Foundation

**Cycle:** cycle-026a
**Date:** 17 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

### 1.1 Goal

Add a reproducible evidence-anchor layer for construct verification:

```text
external source -> snapshot/live classification -> manifest registry -> construct anchor mapping -> verification contract provenance
```

### 1.2 Change Categories

1. **Asset registry layer** — machine-readable manifests for snapshot assets
2. **R2 path policy** — stable bucket layout and file conventions
3. **Local staging root policy** — configurable local asset root, no hardcoded operator path
4. **Anchor mapping layer** — map evaluation dimensions to anchor classes
5. **Policy enforcement** — flag weakly anchored verification dimensions

No database migrations. No new API routes required for v1. This cycle establishes the storage contract and internal models first.

### 1.3 Snapshot vs Live Rule

Use this rule consistently:

- snapshot into R2 if the asset is versioned/pinned and intended as reproducible evaluation input
- keep live if the asset’s freshness is part of the truth claim

Examples:

- HumanEval -> snapshot
- WCAG 2.2 -> snapshot
- OFAC sanctions -> live
- GDELT -> live

---

## 2. File-Level Changes

### 2.1 Asset Registry Models

**New file:** `backend/schemas/eval_asset_registry.py`

Add Pydantic models:

```python
class RegistryFileEntry(BaseModel):
    path: str
    size_bytes: int
    content_hash: str


class DatasetRegistryEntry(BaseModel):
    asset_id: str
    asset_class: Literal["benchmark", "standard"]
    source_url: str
    version: str
    license: str | None = None
    retrieved_at: datetime
    content_hash: str
    files: list[RegistryFileEntry]


class DatasetRegistryDocument(BaseModel):
    version: str
    generated_at: datetime
    entries: list[DatasetRegistryEntry]
```

Validation rules:
- `content_hash` must begin with `sha256:`
- `asset_id` must be stable and filesystem-safe
- every entry must contain at least one file

### 2.2 Anchor Mapping Models

**New file:** `backend/schemas/construct_anchor_schema.py`

Add:

```python
class AnchorClass(str, Enum):
    DETERMINISTIC_CHECK = "deterministic_check"
    BENCHMARK_DATASET = "benchmark_dataset"
    PUBLIC_STANDARD = "public_standard"
    LIVE_EXTERNAL_EVIDENCE = "live_external_evidence"


class AnchorReference(BaseModel):
    anchor_class: AnchorClass
    anchor_id: str
    rationale: str


class EvaluationDimensionAnchor(BaseModel):
    dimension: str
    anchors: list[AnchorReference]
    weakly_anchored: bool = False
```

### 2.3 Asset Classification Policy

**New file:** `backend/services/eval_asset_policy.py`

Responsibilities:
- classify asset as `snapshot` or `live`
- validate whether a candidate asset belongs in R2
- reject attempts to treat live feeds as immutable ground truth

Reference implementation:

```python
SNAPSHOT_ASSETS = {
    "humaneval",
    "mbpp",
    "hellaswag",
    "mmlu",
    "mmlu-pro",
    "swe-bench-verified",
    "wcag",
    "aria-apg",
}

LIVE_ONLY_ASSETS = {
    "sec-edgar",
    "ofac",
    "un-sanctions",
    "gdelt",
    "global-fishing-watch",
}
```

### 2.4 Registry Manifest Builder

**New file:** `backend/services/r2_manifest_builder.py`

Responsibilities:
- compute per-file hashes
- compute top-level asset hash
- emit manifest JSON
- enforce R2 path conventions

Reference flow:

```python
def build_manifest(asset_root: Path, *, asset_id: str, asset_class: str, source_url: str, version: str) -> DatasetRegistryEntry:
    files = []
    for file in sorted(asset_root.rglob("*")):
        if file.is_file():
            digest = sha256_file(file)
            files.append(
                RegistryFileEntry(
                    path=str(file.relative_to(asset_root)),
                    size_bytes=file.stat().st_size,
                    content_hash=f"sha256:{digest}",
                )
            )

    top_hash = sha256_json([f.model_dump() for f in files])
    return DatasetRegistryEntry(
        asset_id=asset_id,
        asset_class=asset_class,
        source_url=source_url,
        version=version,
        retrieved_at=datetime.utcnow(),
        content_hash=f"sha256:{top_hash}",
        files=files,
    )
```

### 2.5 Construct Anchor Mapper

**New file:** `backend/services/construct_anchor_mapper.py`

Responsibilities:
- map construct evaluation dimensions to anchor references
- mark dimensions with no accepted anchor as weakly anchored

Initial rule set:

- code compilation/lint/test -> `deterministic_check`
- benchmark prompt family -> `benchmark_dataset`
- accessibility/ui compliance -> `public_standard`
- real-world factual expertise -> `live_external_evidence`

### 2.6 R2 Layout Contract

No API needed for v1, but the service code should assume:

```text
benchmarks/{asset}/{version}/raw/
benchmarks/{asset}/{version}/manifest.json
benchmarks/{asset}/{version}/LICENSE

standards/{asset}/{version}/raw/
standards/{asset}/{version}/manifest.json
standards/{asset}/{version}/LICENSE

manifests/dataset_registry.json
manifests/standards_registry.json
```

### 2.7 Local Staging Root Contract

The implementation must support a configurable local staging root for downloaded assets.

Suggested contract:

```python
EVAL_DATA_ROOT = os.environ.get(
    "ECHELON_EVAL_DATA_ROOT",
    "/Users/tobiasharber/Developer/echelon-datasets/eval-benchmarks",  # operator example only
)
```

Rules:
- the absolute example path above is documentation only, not a required runtime constant
- manifest builders and utility scripts should accept an explicit input path
- tests must not assume a developer-specific home directory
- path normalization should exclude transport/cache artifacts (for example `.cache`, `.gitattributes`) from canonical asset manifests unless explicitly promoted into `raw/`

### 2.8 Suggested Optional Utility Script

**Optional script:** `backend/scripts/build_eval_asset_manifest.py`

Purpose:
- generate one asset manifest from a local folder
- update aggregate registry document

This is a convenience layer, not a hard runtime dependency.

---

## 3. Policy Surface

### 3.1 Accepted Snapshot Assets In This Cycle

- HumanEval
- MBPP
- HellaSwag
- MMLU
- MMLU-Pro
- SWE-bench Verified metadata/splits
- WCAG 2.2
- ARIA APG

### 3.2 Explicit Live-Only Assets In This Cycle

- SEC EDGAR
- OFAC
- UN sanctions
- GDELT
- Global Fishing Watch

### 3.3 Weakly Anchored Rule

If an evaluation dimension has:
- no deterministic validator
- no benchmark/reference dataset
- no public standard
- no live external evidence anchor

then it must be emitted as:

```json
{
  "dimension": "output_conformance",
  "anchors": [],
  "weakly_anchored": true
}
```

This does not block evaluation in v1, but it makes the limitation explicit.

---

## 4. Dependency Graph

```text
asset policy
  -> manifest builder
  -> aggregate registry documents
  -> construct anchor mapper
  -> construct verification provenance
```

No dependency on frontend or DB migration work.

---

## 5. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| R2 becomes mixed with ad hoc files | provenance drift | enforce manifest + path policy |
| live feeds treated as static truth | incorrect certificate claims | explicit live-only denylist |
| anchor mapping too permissive | weak verification still looks strong | emit `weakly_anchored` flags |
| dataset license ambiguity | operational/legal risk | store source URL and license field in manifest |

---

## 6. Files Touched

| File | Change |
|---|---|
| `backend/schemas/eval_asset_registry.py` | new registry schema models |
| `backend/schemas/construct_anchor_schema.py` | new anchor mapping models |
| `backend/services/eval_asset_policy.py` | snapshot/live classification |
| `backend/services/r2_manifest_builder.py` | per-asset manifest builder |
| `backend/services/construct_anchor_mapper.py` | map evaluation dimensions to anchors |
| `backend/scripts/build_eval_asset_manifest.py` | optional manifest utility |
| `backend/tests/test_eval_asset_policy.py` | policy tests |
| `backend/tests/test_r2_manifest_builder.py` | manifest tests |
| `backend/tests/test_construct_anchor_mapper.py` | anchor mapping tests |
