#!/usr/bin/env bats
# tests/unit/invariant-verification.bats
#
# BATS tests for verify-invariants.sh
# Sprint 8, Task 8.4: Invariant verification test suite
#
# Run with: bats tests/unit/invariant-verification.bats

setup() {
    export PROJECT_ROOT="$(git rev-parse --show-toplevel)"
    export VERIFY_SCRIPT="$PROJECT_ROOT/.claude/scripts/verify-invariants.sh"
    export TEST_DIR="$(mktemp -d)"

    # Create a minimal Python file to serve as a valid verification target
    mkdir -p "$TEST_DIR/src"
    cat > "$TEST_DIR/src/example.py" <<'PYEOF'
class ExampleClass:
    def example_method(self):
        pass

def standalone_function(x):
    return x + 1
PYEOF

    # Create a minimal YAML file to serve as a valid YAML verification target
    cat > "$TEST_DIR/src/config.yaml" <<'YAMLEOF'
model_permissions:
  claude:
    trust_level: high
YAMLEOF
}

teardown() {
    rm -rf "$TEST_DIR"
}

# Helper: create a test invariants.yaml
create_invariants_yaml() {
    local dest="$1"
    shift
    cat > "$dest" "$@"
}

# ─────────────────────────────────────────────────
# Test 1: Script finds all declared invariants in valid codebase
# ─────────────────────────────────────────────────

@test "finds all declared invariants in valid codebase" {
    # Use the real invariants.yaml against the real codebase
    run bash "$VERIFY_SCRIPT" --file "$PROJECT_ROOT/grimoires/loa/invariants.yaml"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Status: PASS" ]]
    [[ "$output" =~ "0 failed" ]]
}

@test "JSON output mode works for valid codebase" {
    run bash "$VERIFY_SCRIPT" --file "$PROJECT_ROOT/grimoires/loa/invariants.yaml" --json
    [ "$status" -eq 0 ]

    # Validate JSON structure
    echo "$output" | jq -e '.status == "pass"'
    echo "$output" | jq -e '.failures == 0'
    echo "$output" | jq -e '.passes > 0'
}

# ─────────────────────────────────────────────────
# Test 2: Script detects missing function
# ─────────────────────────────────────────────────

@test "detects missing function (symbol not found in file)" {
    # Create an invariants file referencing a non-existent function
    create_invariants_yaml "$TEST_DIR/invariants-bad-symbol.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-999
    description: "Test invariant with non-existent symbol reference"
    severity: advisory
    category: conservation
    properties:
      - "test property"
    verified_in:
      - repo: loa
        file: ".claude/adapters/loa_cheval/metering/pricing.py"
        symbol: "NonExistentFunction_XYZ_12345"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-bad-symbol.yaml"
    [ "$status" -eq 1 ]
    [[ "$output" =~ "FAIL" ]]
    [[ "$output" =~ "symbol not found" ]] || [[ "$output" =~ "not found" ]]
}

@test "JSON output reports failure for missing function" {
    create_invariants_yaml "$TEST_DIR/invariants-bad-symbol.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-999
    description: "Test invariant with non-existent symbol reference"
    severity: advisory
    category: conservation
    properties:
      - "test property"
    verified_in:
      - repo: loa
        file: ".claude/adapters/loa_cheval/metering/pricing.py"
        symbol: "NonExistentFunction_XYZ_12345"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-bad-symbol.yaml" --json
    [ "$status" -eq 1 ]
    echo "$output" | jq -e '.status == "fail"'
    echo "$output" | jq -e '.failures > 0'
}

# ─────────────────────────────────────────────────
# Test 3: Script detects missing file
# ─────────────────────────────────────────────────

@test "detects missing file" {
    create_invariants_yaml "$TEST_DIR/invariants-bad-file.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-998
    description: "Test invariant with non-existent file reference"
    severity: advisory
    category: bounded
    properties:
      - "test property"
    verified_in:
      - repo: loa
        file: "path/to/nonexistent/file_that_does_not_exist.py"
        symbol: "SomeFunction"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-bad-file.yaml"
    [ "$status" -eq 1 ]
    [[ "$output" =~ "FAIL" ]]
    [[ "$output" =~ "file not found" ]] || [[ "$output" =~ "not found" ]]
}

# ─────────────────────────────────────────────────
# Test 4: Script handles empty invariants.yaml gracefully
# ─────────────────────────────────────────────────

@test "handles empty invariants array gracefully" {
    create_invariants_yaml "$TEST_DIR/invariants-empty.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants: []
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-empty.yaml"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "No invariants declared" ]]
}

@test "handles empty invariants array in JSON mode" {
    create_invariants_yaml "$TEST_DIR/invariants-empty.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants: []
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-empty.yaml" --json
    [ "$status" -eq 0 ]
    echo "$output" | jq -e '.status == "pass"'
    echo "$output" | jq -e '.passes == 0'
    echo "$output" | jq -e '.failures == 0'
}

# ─────────────────────────────────────────────────
# Test 5: Cross-repo references are SKIPped (not FAILed)
# ─────────────────────────────────────────────────

@test "cross-repo references are skipped not failed" {
    create_invariants_yaml "$TEST_DIR/invariants-cross-repo.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-997
    description: "Test invariant with cross-repo reference only"
    severity: important
    category: conservation
    properties:
      - "test cross-repo property"
    verified_in:
      - repo: hounfour
        file: "src/monetary_policy.py"
        symbol: "MonetaryPolicy"
      - repo: arrakis
        file: "src/lot_invariant.py"
        symbol: "lot_invariant"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-cross-repo.yaml"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "SKIP" ]]
    [[ "$output" =~ "external repo" ]]
    [[ "$output" =~ "0 failed" ]]
    [[ "$output" =~ "2 skipped" ]]
}

@test "cross-repo references produce skip status in JSON" {
    create_invariants_yaml "$TEST_DIR/invariants-cross-repo.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-997
    description: "Test invariant with cross-repo reference only"
    severity: important
    category: conservation
    properties:
      - "test cross-repo property"
    verified_in:
      - repo: hounfour
        file: "src/monetary_policy.py"
        symbol: "MonetaryPolicy"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-cross-repo.yaml" --json
    [ "$status" -eq 0 ]
    echo "$output" | jq -e '.skips > 0'
    echo "$output" | jq -e '.failures == 0'
    echo "$output" | jq -e '.checks[0].status == "skip"'
}

# ─────────────────────────────────────────────────
# Test 6: Exit codes
# ─────────────────────────────────────────────────

@test "exit code 0 for all-pass" {
    run bash "$VERIFY_SCRIPT" --file "$PROJECT_ROOT/grimoires/loa/invariants.yaml" --quiet
    [ "$status" -eq 0 ]
}

@test "exit code 1 for any-fail" {
    create_invariants_yaml "$TEST_DIR/invariants-fail.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-996
    description: "Test invariant that will fail verification"
    severity: critical
    category: bounded
    properties:
      - "test fail property"
    verified_in:
      - repo: loa
        file: "this/file/does/not/exist.py"
        symbol: "NoSuchSymbol"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-fail.yaml" --quiet
    [ "$status" -eq 1 ]
}

@test "exit code 2 for missing invariants file" {
    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/nonexistent-file.yaml"
    [ "$status" -eq 2 ]
}

@test "exit code 2 for unsupported schema version" {
    create_invariants_yaml "$TEST_DIR/invariants-bad-version.yaml" <<'EOF'
schema_version: 99
protocol: loa-hounfour@7.0.0
invariants: []
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-bad-version.yaml"
    [ "$status" -eq 2 ]
    [[ "$output" =~ "Unsupported schema_version" ]]
}

# ─────────────────────────────────────────────────
# Test 7: Mixed results (some pass, some fail, some skip)
# ─────────────────────────────────────────────────

@test "mixed results: pass + fail + skip in single run" {
    create_invariants_yaml "$TEST_DIR/invariants-mixed.yaml" <<'EOF'
schema_version: 1
protocol: loa-hounfour@7.0.0
invariants:
  - id: INV-100
    description: "Valid local invariant that should pass"
    severity: critical
    category: conservation
    properties:
      - "test pass"
    verified_in:
      - repo: loa
        file: ".claude/adapters/loa_cheval/metering/pricing.py"
        symbol: "calculate_cost_micro"
  - id: INV-200
    description: "Invalid local invariant that should fail"
    severity: advisory
    category: bounded
    properties:
      - "test fail"
    verified_in:
      - repo: loa
        file: "nonexistent/path.py"
        symbol: "NoSymbol"
  - id: INV-300
    description: "Cross-repo invariant that should skip"
    severity: important
    category: idempotent
    properties:
      - "test skip"
    verified_in:
      - repo: arrakis
        file: "src/lot.py"
        symbol: "lot_invariant"
EOF

    run bash "$VERIFY_SCRIPT" --file "$TEST_DIR/invariants-mixed.yaml" --json
    [ "$status" -eq 1 ]
    echo "$output" | jq -e '.passes == 1'
    echo "$output" | jq -e '.failures == 1'
    echo "$output" | jq -e '.skips == 1'
    echo "$output" | jq -e '.status == "fail"'
}
