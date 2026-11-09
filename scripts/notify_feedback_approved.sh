#!/usr/bin/env bash
# Fire the event-driven retraining workflow (.github/workflows/retrain-on-feedback.yml).
# Call this after reviewers approve a batch of feedback corrections (e.g. from a cron on the
# server, an admin action, or by hand).
#
#   GITHUB_REPOSITORY=sumerashaikh0920/triageflow GITHUB_TOKEN=<token> \
#     ./scripts/notify_feedback_approved.sh [approved_count] [mode]
#
# The token needs permission to create repository dispatch events: a fine-grained PAT with
# "Contents: read and write" on this repository. Store it as a secret where this script runs;
# never put it in the repo.
set -euo pipefail

: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY (owner/repo) is required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
COUNT="${1:-0}"
MODE="${2:-baseline}"

case "$COUNT" in ''|*[!0-9]*) echo "approved_count must be a number" >&2; exit 2 ;; esac
case "$MODE" in baseline|transformer) ;; *) echo "mode must be baseline or transformer" >&2; exit 2 ;; esac

curl -fsS -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/dispatches" \
  -d "{\"event_type\":\"feedback-approved\",\"client_payload\":{\"approved_count\":$COUNT,\"mode\":\"$MODE\"}}"

echo "Dispatched feedback-approved ($COUNT approved, mode=$MODE) to $GITHUB_REPOSITORY"
