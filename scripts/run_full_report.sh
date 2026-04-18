#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

NETWORK="${1:-bradbury}"
case "$NETWORK" in
  bradbury) ENV_FILE="${2:-.env.bradbury}" ;;
  asimov) ENV_FILE="${2:-.env.asimov}" ;;
  *) echo "Unsupported network: $NETWORK" >&2; exit 1 ;;
esac

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

export HARNESS_DEFAULT_NETWORK="${HARNESS_DEFAULT_NETWORK:-$NETWORK}"
export PYTHONPATH="${PYTHONPATH:-.}"
export HARNESS_VERBOSE="${HARNESS_VERBOSE:-1}"
export HARNESS_PRINT_LOGS="${HARNESS_PRINT_LOGS:-1}"

if ! command -v genlayer >/dev/null 2>&1; then
  echo "genlayer CLI not found in PATH" >&2
  exit 1
fi

SESSION_ROOT="${HARNESS_OUTPUT_DIR:-artifacts}/full-report-${HARNESS_DEFAULT_NETWORK}-$(date -u +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$SESSION_ROOT"
SESSION_LOG="$SESSION_ROOT/session.log"

echo "Session root: $SESSION_ROOT" | tee -a "$SESSION_LOG"
echo "Using env: $ENV_FILE" | tee -a "$SESSION_LOG"
echo "Verbose: HARNESS_VERBOSE=$HARNESS_VERBOSE HARNESS_PRINT_LOGS=$HARNESS_PRINT_LOGS" | tee -a "$SESSION_LOG"

DEPLOY_RUN_ROOT=""
CONTRACT_ADDRESS="${GLH_TEST_CONTRACT_ADDRESS:-}"

if [[ -z "$CONTRACT_ADDRESS" || "${GLH_AUTO_DEPLOY:-0}" == "1" ]]; then
  if [[ -z "${GLH_TEST_CONTRACT_FILE:-}" ]]; then
    echo "GLH_TEST_CONTRACT_FILE is required for auto deploy" | tee -a "$SESSION_LOG" >&2
    exit 1
  fi

  echo "[1/3] Deploying fixture contract on ${HARNESS_DEFAULT_NETWORK}" | tee -a "$SESSION_LOG"
  DEPLOY_OUTPUT=$(python -m src.main --scenario scenarios/report_bootstrap/deploy_fixture.yaml --adapter command --debug on-fail --wait-status finalized --out "$SESSION_ROOT/deploy" --verbose --print-logs | tee -a "$SESSION_LOG")
  echo "$DEPLOY_OUTPUT" >> "$SESSION_LOG"
  DEPLOY_RUN_ROOT=$(printf '%s\n' "$DEPLOY_OUTPUT" | awk -F': ' '/^Run root:/ {print $2}' | tail -n1)
  if [[ -z "$DEPLOY_RUN_ROOT" ]]; then
    echo "Failed to detect deploy run root" | tee -a "$SESSION_LOG" >&2
    exit 1
  fi

  CONTRACT_ADDRESS=$(python - <<'PY' "$DEPLOY_RUN_ROOT/runs.csv"
import csv, sys
path = sys.argv[1]
with open(path, newline='', encoding='utf-8') as fh:
    rows = list(csv.DictReader(fh))
for row in rows:
    addr = (row.get('contract_address') or '').strip()
    if addr and row.get('actual_pass', '').lower() in {'true', '1'}:
        print(addr)
        break
PY
)
  if [[ -z "$CONTRACT_ADDRESS" ]]; then
    echo "Deploy finished but contract_address not found in runs.csv" | tee -a "$SESSION_LOG" >&2
    exit 1
  fi
fi

export GLH_TEST_CONTRACT_ADDRESS="$CONTRACT_ADDRESS"
echo "Contract address: $GLH_TEST_CONTRACT_ADDRESS" | tee -a "$SESSION_LOG"

echo "[2/3] Running transaction report suite on ${HARNESS_DEFAULT_NETWORK}" | tee -a "$SESSION_LOG"
SUITE_OUTPUT=$(python -m src.main --scenario scenarios/report_suite --adapter command --debug on-fail --wait-status finalized --out "$SESSION_ROOT/suite" --verbose --print-logs | tee -a "$SESSION_LOG")
echo "$SUITE_OUTPUT" >> "$SESSION_LOG"
SUITE_RUN_ROOT=$(printf '%s\n' "$SUITE_OUTPUT" | awk -F': ' '/^Run root:/ {print $2}' | tail -n1)
if [[ -z "$SUITE_RUN_ROOT" ]]; then
  echo "Failed to detect suite run root" | tee -a "$SESSION_LOG" >&2
  exit 1
fi

cat > "$SESSION_ROOT/MASTER_REPORT.md" <<EOF
# Master Transaction Test Session

- Network: \`${HARNESS_DEFAULT_NETWORK}\`
- Contract address: \`${GLH_TEST_CONTRACT_ADDRESS}\`
- Deploy run root: \`${DEPLOY_RUN_ROOT:-not-used}\`
- Suite run root: \`${SUITE_RUN_ROOT}\`
- Session log: \`${SESSION_LOG}\`
- Suite live log: \`${SUITE_RUN_ROOT}/logs/live.log\`
- Suite summary: \`${SUITE_RUN_ROOT}/summary.md\`
- Suite full report: \`${SUITE_RUN_ROOT}/full_report.md\`
- Suite summary JSON: \`${SUITE_RUN_ROOT}/summary.json\`
- Suite CSV: \`${SUITE_RUN_ROOT}/runs.csv\`

## What was executed

1. Optional bootstrap deploy to get a fresh contract address.
2. Baseline write.
3. Low gas write.
4. Borderline gas write.
5. High gas write.
6. Invalid function call for error path.
7. Concurrent writes from the same sender.
EOF

echo "[3/3] Done" | tee -a "$SESSION_LOG"
echo "Session root: $SESSION_ROOT" | tee -a "$SESSION_LOG"
echo "Master report: $SESSION_ROOT/MASTER_REPORT.md" | tee -a "$SESSION_LOG"
echo "Suite full report: $SUITE_RUN_ROOT/full_report.md" | tee -a "$SESSION_LOG"
echo "Session log: $SESSION_LOG" | tee -a "$SESSION_LOG"
