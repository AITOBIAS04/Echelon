#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# echelon_demo.sh — Escrow Wedge Demo Pack Generator (v0.2)
#
# Patches from v0.1:
#   Fix 1: 6 pass / 4 fail fixture split (rejection scenarios)
#   Fix 2: verification_tier = UNVERIFIED (honest demo labelling)
#   Fix 3: manifest.json is pure path→hash map (deterministic)
#   Fix 4: commitment_hash = sha256(canonical(full_template))
#
# Builds a complete, verifiable escrow certification demo:
#   1. Creates evidence bundle directory structure
#   2. Places template + fixtures in correct locations
#   3. Generates a calibration certificate with computed hashes
#   4. Runs echelon_verify.py to produce the headline PASS report
#
# Requirements: Python 3.10+, no external packages.
# Usage: chmod +x echelon_demo.sh && ./echelon_demo.sh
# ════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[92m'
BLUE='\033[94m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

DEMO_DIR="echelon_demo_pack"
EVIDENCE_DIR="${DEMO_DIR}/evidence_bundle"

echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  ECHELON — Escrow Wedge Demo Pack Generator v0.2${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo ""

# ── Step 1: Clean slate ──
echo -e "${BLUE}[1/6]${RESET} Creating demo pack directory structure..."
rm -rf "${DEMO_DIR}"
mkdir -p "${EVIDENCE_DIR}/inputs"
mkdir -p "${EVIDENCE_DIR}/policy"
mkdir -p "${EVIDENCE_DIR}/expected"
echo "      ${DEMO_DIR}/"
echo "      ├── evidence_bundle/"
echo "      │   ├── inputs/"
echo "      │   ├── policy/"
echo "      │   ├── expected/"
echo "      │   └── manifest.json"
echo "      ├── certificate.json"
echo "      └── echelon_verify.py"
echo ""

# ── Step 2: Locate source files ──
echo -e "${BLUE}[2/6]${RESET} Locating source artefacts..."

TEMPLATE_SRC=""
FIXTURES_SRC=""
VERIFIER_SRC=""

# v0.2 fixtures preferred; fall back to v0.1
for dir in "." ".." "/mnt/project" "/mnt/user-data/outputs"; do
    [ -f "${dir}/ESCROW_MILESTONE_RELEASE_V1_template.json" ] && TEMPLATE_SRC="${dir}/ESCROW_MILESTONE_RELEASE_V1_template.json"
    [ -z "${FIXTURES_SRC}" ] && [ -f "${dir}/escrow_fixtures_v02_11.json" ] && FIXTURES_SRC="${dir}/escrow_fixtures_v02_11.json"
    [ -z "${FIXTURES_SRC}" ] && [ -f "${dir}/escrow_fixtures_v02_10.json" ] && FIXTURES_SRC="${dir}/escrow_fixtures_v02_10.json"
    [ -z "${FIXTURES_SRC}" ] && [ -f "${dir}/escrow_fixtures_10.json" ] && FIXTURES_SRC="${dir}/escrow_fixtures_10.json"
    [ -f "${dir}/echelon_verify.py" ] && VERIFIER_SRC="${dir}/echelon_verify.py"
done

if [ -z "${TEMPLATE_SRC}" ] || [ -z "${FIXTURES_SRC}" ] || [ -z "${VERIFIER_SRC}" ]; then
    echo "  Missing files. Ensure these exist in the current directory or /mnt/project/:"
    [ -z "${TEMPLATE_SRC}" ] && echo "    ✗ ESCROW_MILESTONE_RELEASE_V1_template.json"
    [ -z "${FIXTURES_SRC}" ] && echo "    ✗ escrow_fixtures_v02_10.json (or escrow_fixtures_10.json)"
    [ -z "${VERIFIER_SRC}" ] && echo "    ✗ echelon_verify.py"
    exit 2
fi

echo "      Template: ${TEMPLATE_SRC}"
echo "      Fixtures: ${FIXTURES_SRC}"
echo "      Verifier: ${VERIFIER_SRC}"
echo ""

# ── Step 3: Populate evidence bundle ──
echo -e "${BLUE}[3/6]${RESET} Populating evidence bundle..."
cp "${FIXTURES_SRC}" "${EVIDENCE_DIR}/inputs/escrow_fixtures_10.json"
cp "${TEMPLATE_SRC}" "${EVIDENCE_DIR}/policy/ESCROW_MILESTONE_RELEASE_V1_template.json"

# Patch template dataset_hashes to match v0.2 fixtures
python3 -c "
import json, hashlib
with open('${FIXTURES_SRC}') as f:
    data = json.load(f)
h = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode('utf-8')).hexdigest()
tmpl_path = '${EVIDENCE_DIR}/policy/ESCROW_MILESTONE_RELEASE_V1_template.json'
with open(tmpl_path) as f:
    tmpl = json.load(f)
tmpl['dataset_hashes'] = {'escrow_fixtures_10.json': h}
with open(tmpl_path, 'w') as f:
    json.dump(tmpl, f, indent=2)
"

python3 -c "
import json
with open('${FIXTURES_SRC}') as f:
    data = json.load(f)
expected = {
    'dataset_id': data['dataset_id'],
    'expected_outputs': [
        {'record_id': r['record_id'], 'expected_outputs': r['expected_outputs']}
        for r in data['records']
    ]
}
with open('${EVIDENCE_DIR}/expected/escrow_expected_outputs.json', 'w') as f:
    json.dump(expected, f, indent=2)
"

# Count pass/fail
PASS_COUNT=$(python3 -c "
import json
with open('${FIXTURES_SRC}') as f:
    data = json.load(f)
p = sum(1 for r in data['records'] if r['expected_outputs']['release_instruction'].get('release_allowed', True))
f = len(data['records']) - p
print(f'{p} pass / {f} fail')
")

echo "      inputs/escrow_fixtures_10.json ✓"
echo "      policy/ESCROW_MILESTONE_RELEASE_V1_template.json ✓"
echo "      expected/escrow_expected_outputs.json ✓"
echo "      Fixture split: ${PASS_COUNT}"
echo ""

# ── Step 4: Generate certificate + manifest ──
echo -e "${BLUE}[4/6]${RESET} Generating certificate and manifest..."

python3 << 'PYEOF'
import json
import hashlib
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import uuid

DEMO_DIR = "echelon_demo_pack"
EVIDENCE_DIR = f"{DEMO_DIR}/evidence_bundle"

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_json(obj):
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ══ FIX 3: manifest is pure path→hash map, no timestamp ══
manifest = {}
evidence_path = Path(EVIDENCE_DIR)
for fp in sorted(evidence_path.rglob("*")):
    if fp.is_file() and fp.name != "manifest.json":
        rel = str(fp.relative_to(evidence_path))
        if fp.suffix == ".json":
            with open(fp) as f:
                data = json.load(f)
            manifest[rel] = sha256_json(data)
        else:
            manifest[rel] = sha256_file(fp)

with open(f"{EVIDENCE_DIR}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)

# ── Compute hashes ──
with open(f"{EVIDENCE_DIR}/inputs/escrow_fixtures_10.json") as f:
    fixtures = json.load(f)
dataset_hash = sha256_json(fixtures)
evidence_bundle_hash = sha256_json(manifest)

with open(f"{EVIDENCE_DIR}/policy/ESCROW_MILESTONE_RELEASE_V1_template.json") as f:
    template = json.load(f)

# ══ FIX 4: commitment_hash = sha256(canonical(full template)) ══
commitment_hash = sha256_json(template)

now = datetime.now(timezone.utc)

# ══ FIX 1: compute scores from fixture verdicts ══
records = fixtures["records"]
criteria_ids = template["criteria"]["criteria_ids"]
weights = template["criteria"]["weights"]

scores = {}
for cid in criteria_ids:
    verdicts = []
    for r in records:
        cv = r.get("expected_outputs", {}).get("criteria_verdicts", {})
        if cv:
            verdicts.append(1.0 if cv.get(cid, True) else 0.0)
        else:
            verdicts.append(1.0)
    scores[cid] = sum(verdicts) / len(verdicts) if verdicts else 0.0

composite = sum(weights[k] * scores[k] for k in weights)

pass_count = sum(1 for r in records if r["expected_outputs"]["release_instruction"].get("release_allowed", True))
fail_count = len(records) - pass_count

# ══ FIX 2: verification_tier = UNVERIFIED ══
certificate = {
    "certificate_id": str(uuid.uuid4()),
    "theatre_id": template["theatre_id"],
    "template_id": template["template_id"],
    "construct_id": "two_rail_marketplace_core",
    "construct_version": "v0.2-fixtures",
    "criteria": template["criteria"],
    "scores": scores,
    "composite_score": composite,
    "replay_count": len(records),
    "replay_summary": {
        "total_records": len(records),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_count / len(records)
    },
    "evidence_bundle_hash": evidence_bundle_hash,
    "dataset_hash": dataset_hash,
    "ground_truth_hash": dataset_hash,
    "ground_truth_source": "v0.2 fixtures (6 valid releases + 4 rejection scenarios)",
    "commitment_hash": commitment_hash,
    "verification_tier": "UNVERIFIED",
    "execution_path": "replay",
    "scorer_version": "deterministic-v0.2",
    "methodology_version": "1.0.0",
    "issued_at": now.isoformat(),
    "expires_at": (now + timedelta(days=365)).isoformat(),
    "theatre_committed_at": (now - timedelta(minutes=5)).isoformat(),
    "theatre_resolved_at": (now - timedelta(seconds=10)).isoformat(),
}

with open(f"{DEMO_DIR}/certificate.json", "w") as f:
    json.dump(certificate, f, indent=2)

print(f"      Certificate ID: {certificate['certificate_id']}")
print(f"      Verification tier: {certificate['verification_tier']}")
print(f"      Replay count: {certificate['replay_count']} ({pass_count} pass / {fail_count} fail)")
print(f"      Scores:")
for cid in sorted(scores):
    print(f"        {cid}: {scores[cid]:.4f}")
print(f"      Composite score: {composite:.4f}")
print(f"      Dataset hash: {dataset_hash[:16]}...")
print(f"      Evidence hash: {evidence_bundle_hash[:16]}...")
print(f"      Commitment hash: {commitment_hash[:16]}...")
PYEOF

echo ""

# ── Step 5: Copy verifier ──
echo -e "${BLUE}[5/6]${RESET} Packaging verifier CLI..."
cp "${VERIFIER_SRC}" "${DEMO_DIR}/echelon_verify.py"
chmod +x "${DEMO_DIR}/echelon_verify.py"
echo "      echelon_verify.py ✓"
echo ""

# ── Step 6: Run verification ──
echo -e "${BLUE}[6/6]${RESET} Running verification..."
echo ""
python3 "${DEMO_DIR}/echelon_verify.py" verify "${DEMO_DIR}/certificate.json" "${EVIDENCE_DIR}"
echo ""

echo -e "${DIM}Running template replay check...${RESET}"
echo ""
python3 "${DEMO_DIR}/echelon_verify.py" replay \
    "${EVIDENCE_DIR}/policy/ESCROW_MILESTONE_RELEASE_V1_template.json" \
    "${EVIDENCE_DIR}/inputs/escrow_fixtures_10.json"

# ── Summary ──
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  DEMO PACK COMPLETE (v0.2)${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
echo ""
echo "  Fixes applied:"
echo "    ✓ Fix 1: 6 pass / 4 fail fixture split (rejection scenarios)"
echo "    ✓ Fix 2: verification_tier = UNVERIFIED (honest demo labelling)"
echo "    ✓ Fix 3: manifest.json is pure path→hash map (deterministic)"
echo "    ✓ Fix 4: commitment_hash = sha256(canonical(full_template))"
echo ""
echo "  Output directory: ${DEMO_DIR}/"
echo ""
echo "  To verify independently:"
echo "    cd ${DEMO_DIR}"
echo "    python3 echelon_verify.py verify certificate.json evidence_bundle/"
echo "    python3 echelon_verify.py inspect certificate.json"
echo ""
echo "  To share with stakeholders:"
echo "    Send the entire ${DEMO_DIR}/ folder."
echo "    Recipient only needs Python 3.10+ — zero other dependencies."
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
