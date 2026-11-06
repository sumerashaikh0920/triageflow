#!/usr/bin/env bash
# Drive the ML service's retraining pipeline over HTTP. Used by the GitHub Actions retraining
# workflows, and safe to run by hand.
#
#   ML_SERVICE_URL=http://localhost:8001 ./scripts/retrain_via_api.sh
#
# Environment:
#   ML_SERVICE_URL          required  base URL of the ML service
#   ML_SERVICE_AUTH_HEADER  optional  e.g. "X-Api-Key: abc" (sent on every request)
#   MODE                    baseline | transformer          (default: baseline)
#   FORCE                   true | false                    (default: false)
#   ONLY_IF_TRIGGERED       true | false                    (default: true)
#                           true = call /retrain/check first and stop if no trigger fired
#   REPORT_FILE             where to write the JSON report  (default: retrain-report.json)
#
# This script only REGISTERS a candidate. It never calls /models/{version}/approve or
# /activate: promoting a model stays a deliberate human action.
set -euo pipefail

: "${ML_SERVICE_URL:?ML_SERVICE_URL is required}"
MODE="${MODE:-baseline}"
FORCE="${FORCE:-false}"
ONLY_IF_TRIGGERED="${ONLY_IF_TRIGGERED:-true}"
REPORT_FILE="${REPORT_FILE:-retrain-report.json}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/stdout}"

case "$MODE" in baseline|transformer) ;; *) echo "::error::MODE must be baseline or transformer (got '$MODE')"; exit 2 ;; esac
case "$FORCE" in true|false) ;; *) echo "::error::FORCE must be true or false (got '$FORCE')"; exit 2 ;; esac
case "$ONLY_IF_TRIGGERED" in true|false) ;; *) echo "::error::ONLY_IF_TRIGGERED must be true or false"; exit 2 ;; esac

BASE="${ML_SERVICE_URL%/}"
CURL=(curl -fsS --retry 3 --retry-connrefused --retry-delay 5 --max-time "${CURL_TIMEOUT:-1800}" -X POST)
if [ -n "${ML_SERVICE_AUTH_HEADER:-}" ]; then CURL+=(-H "$ML_SERVICE_AUTH_HEADER"); fi

out() { if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "$1=$2" >> "$GITHUB_OUTPUT"; fi; }

echo "Checking retraining triggers (mode=$MODE force=$FORCE)..."
check_json="$("${CURL[@]}" "$BASE/retrain/check")"
triggered="$(jq -r '.triggered' <<<"$check_json")"
reason="$(jq -r '.reason' <<<"$check_json")"
echo "Trigger check: triggered=$triggered"
echo "  $reason"
out triggered "$triggered"

if [ "$ONLY_IF_TRIGGERED" = "true" ] && [ "$triggered" != "true" ] && [ "$FORCE" != "true" ]; then
  {
    echo "### Retraining skipped"
    echo "No retraining trigger fired, so nothing was trained."
    echo
    echo "> $reason"
  } >> "$SUMMARY"
  out skipped true
  exit 0
fi

echo "Running retraining pipeline..."
run_json="$("${CURL[@]}" "$BASE/retrain/run?mode=$MODE&force=$FORCE")"
printf '%s\n' "$run_json" > "$REPORT_FILE"

ran="$(jq -r '.triggered' <<<"$run_json")"
candidate="$(jq -r '.candidate_version // "none"' <<<"$run_json")"
regressed="$(jq -r '.regressed // false' <<<"$run_json")"
stage="$(jq -r '.report.stage_reached // "unknown"' <<<"$run_json")"
run_reason="$(jq -r '.reason' <<<"$run_json")"
f1="$(jq -r '.report.candidate_metrics.overall.category_weighted_f1 // "n/a"' <<<"$run_json")"
p95="$(jq -r '.report.candidate_metrics.overall.latency_ms.p95 // "n/a"' <<<"$run_json")"
active="$(jq -r '.report.active_version // "none"' <<<"$run_json")"

out candidate_version "$candidate"
out regressed "$regressed"

{
  echo "### Retraining result"
  echo
  echo "| Field | Value |"
  echo "|---|---|"
  echo "| Mode | \`$MODE\` |"
  echo "| Candidate registered | \`$candidate\` |"
  echo "| Compared against active | \`$active\` |"
  echo "| Category weighted F1 | $f1 |"
  echo "| Latency p95 (ms) | $p95 |"
  echo "| Regressed vs active | $regressed |"
  echo "| Pipeline stage reached | \`$stage\` |"
  echo
  echo "> $run_reason"
  echo
  if [ "$ran" = "true" ] && [ "$regressed" != "true" ]; then
    echo "**Next step:** review the candidate, then approve and activate it via the ML service (\`POST /models/$candidate/approve\`, then \`/activate\`). Nothing was deployed automatically."
  fi
} >> "$SUMMARY"

if [ "$ran" != "true" ]; then
  echo "::notice::Pipeline did not train a candidate: $run_reason"
elif [ "$regressed" = "true" ]; then
  echo "::warning::Candidate $candidate regressed vs the active model and is blocked from deployment."
else
  echo "Candidate $candidate registered; awaiting human approval."
fi
