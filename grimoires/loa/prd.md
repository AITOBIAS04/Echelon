# PRD — Cycle-026a: Construct Evidence Anchoring + R2 Ingest Foundation

**Cycle:** cycle-026a
**Date:** 17 March 2026
**Depends on:** Cycle-024 (Construct Verification V1), Cycle-025 (WorldMonitor Intelligence Contract v2)
**Sprints:** 4 (0–3)
**Builder:** Loa (backend/infrastructure only)
**Planning source:** Soju construct verification follow-up; external benchmark and standards anchoring

---

## 1. Problem Statement

### 1.1 Construct Verification Still Leans Too Hard On AI-Scored Rubrics

Cycle-024 proved that Echelon can run construct verification end-to-end. But the strongest criticism still stands: too much of the verdict rests on AI-generated scoring rather than deterministic or externally anchored checks.

For a sceptical user, "Echelon evaluated the construct and said PASS" is not enough. The certificate needs a stronger answer to: **what external thing anchors this judgement?**

### 1.2 We Need A Stable Evidence Layer For Reproducible Evaluation

The right anchor set for construct verification is not "more generic live OSINT." It is a mix of:

- deterministic validators
- benchmark/reference datasets
- public standards/specifications
- live external evidence sources when the construct claims real-world expertise

Right now these inputs are scattered, implicit, or not versioned.

### 1.3 R2 Needs A Policy Before It Becomes A Dumping Ground

We are already uploading large assets into Cloudflare R2. Without a policy layer, we risk mixing:

- immutable benchmark corpora
- standards snapshots
- live data feeds
- one-off ad hoc files

That creates provenance ambiguity and makes later certificates harder to defend.

---

## 2. Product Contracts

### 2.1 Two Anchor Classes

Cycle-026a introduces two explicit evidence-anchor classes:

**A. Snapshot assets in R2**
- versioned or pinned datasets/specifications
- treated as reproducible evaluation inputs
- hashed and listed in registry manifests

**B. Live external evidence sources**
- freshness matters
- should remain API/collector-driven
- may have small cache artifacts, but are not treated as canonical static ground truth

### 2.2 First Snapshot Pack For R2

Load the following into R2 as the initial construct-evaluation anchor set:

| Asset | Class | Why it belongs |
|---|---|---|
| HumanEval | benchmark | deterministic coding benchmark |
| MBPP | benchmark | code generation benchmark |
| HellaSwag | benchmark | reasoning/common-sense reference set |
| MMLU | benchmark | broad cognitive/domain benchmark |
| MMLU-Pro | benchmark | harder benchmark for stronger constructs |
| SWE-bench Verified metadata/splits | benchmark | software maintenance / repo-task reference |
| WCAG 2.2 | standard | accessibility anchor for UI/frontend constructs |
| ARIA APG | standard | interaction/accessibility pattern anchor |

### 2.3 Live Sources Stay Live

These sources are recognized as valuable anchors for some verification workloads, but **must remain live collectors** rather than bucket-first truth snapshots:

| Source | Why live |
|---|---|
| SEC EDGAR | filing freshness matters |
| OFAC sanctions | list changes over time |
| UN sanctions | list changes over time |
| GDELT | event stream freshness matters |
| Global Fishing Watch | activity and time window matter |

### 2.4 R2 Layout Contract

Use a stable, versioned R2 layout:

```text
r2://echelon-eval-assets/
  benchmarks/
    humaneval/{version}/
    mbpp/{version}/
    hellaswag/{version}/
    mmlu/{version}/
    mmlu-pro/{version}/
    swe-bench-verified/{version}/
  standards/
    wcag/{version}/
    aria-apg/{version}/
  manifests/
    dataset_registry.json
    standards_registry.json
```

Each asset folder contains:

```text
{asset}/{version}/raw/
{asset}/{version}/manifest.json
{asset}/{version}/LICENSE
```

### 2.5 Local Staging Root Is Configurable

Cycle-026a must not hardcode a developer-specific absolute filesystem path.

The implementation should support a configurable local staging root, for example:

- env var: `ECHELON_EVAL_DATA_ROOT`
- or equivalent config setting consumed by the manifest/ingest utilities

Example operator path only:

```text
/Users/tobiasharber/Developer/echelon-datasets/eval-benchmarks
```

This path is a valid local staging location, but it is **not** part of the product contract.

### 2.6 Dataset Registry Contract

Every snapshot asset must have a machine-readable registry entry:

```json
{
  "asset_id": "humaneval_v1",
  "class": "benchmark",
  "source_url": "https://github.com/openai/human-eval",
  "version": "v1",
  "license": "MIT",
  "retrieved_at": "2026-03-17T12:00:00Z",
  "content_hash": "sha256:...",
  "files": [
    {
      "path": "raw/problem_file.jsonl",
      "size_bytes": 12345,
      "content_hash": "sha256:..."
    }
  ]
}
```

### 2.7 Construct Anchor Mapping Contract

Every construct evaluation dimension must declare at least one anchor type:

- `deterministic_check`
- `benchmark_dataset`
- `public_standard`
- `live_external_evidence`

If a scoring dimension maps to none of these, it is flagged as **weakly anchored** in the evaluation contract and the certificate provenance.

---

## 3. What This Cycle Does NOT Do

- **Does NOT replace live OSINT collectors with static bucket snapshots**
- **Does NOT expand the osint_signals schema**
- **Does NOT implement the next construct-spec ingestion cycle in full**
- **Does NOT build frontend views**
- **Does NOT ingest speculative large scientific datasets unless they are already in scope for active construct verification**

---

## 4. Acceptance Criteria

1. R2 contains the first benchmark anchor pack
2. R2 contains WCAG 2.2 and ARIA APG snapshots
3. Each snapshot asset has a manifest with source URL, version, retrieval time, and content hash
4. `dataset_registry.json` and `standards_registry.json` exist and validate
5. Snapshot assets are clearly separated from live evidence sources
6. Construct evaluation dimensions can declare anchor classes
7. Weakly anchored dimensions are explicitly labeled
8. No live source is misrepresented as immutable static ground truth
9. `npm run build` still passes (no frontend changes expected)

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Registry manifest schema | 3 | valid entry, missing field, bad hash prefix |
| R2 path policy | 2 | benchmark path, standards path |
| Snapshot vs live classification | 3 | snapshot accepted, live accepted, invalid mixed class rejected |
| Benchmark ingest manifests | 4 | HumanEval, MBPP, MMLU, SWE-bench metadata |
| Standards ingest manifests | 2 | WCAG, ARIA APG |
| Anchor mapping model | 4 | deterministic, benchmark, standard, weakly anchored |
| Construct anchor policy | 3 | fully anchored contract, mixed contract, weak-only contract flagged |
| **Total** | **~21** | |

---

## 6. Recommended Source URLs

### Snapshot Into R2

- HumanEval: `https://github.com/openai/human-eval`
- MBPP: `https://github.com/google-research/google-research/tree/master/mbpp`
- HellaSwag: `https://github.com/rowanz/hellaswag`
- MMLU: `https://github.com/hendrycks/test`
- MMLU-Pro: `https://github.com/TIGER-AI-Lab/MMLU-Pro`
- SWE-bench: `https://github.com/SWE-bench/SWE-bench`
- WCAG 2.2: `https://www.w3.org/TR/WCAG22/`
- ARIA APG: `https://www.w3.org/WAI/ARIA/apg/`

### Keep Live

- SEC EDGAR: `https://www.sec.gov/edgar/sec-api-documentation`
- OFAC: `https://ofac.treasury.gov/sdn-list-data-formats-data-schemas/tutorial-on-the-use-of-list-related-legacy-flat-files`
- UN sanctions: `https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list`
- GDELT: `https://www.gdeltproject.org/data.html`
- Global Fishing Watch: `https://globalfishingwatch.org/our-apis/documentation`
