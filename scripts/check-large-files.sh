#!/usr/bin/env bash
# Refuses files over 1 MB before they enter history (T0b, docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md).
#
# One rule, two callers:
#   --staged   the files staged for the next commit. Run by .githooks/pre-commit.
#   --all      every tracked file. Run by CI on the checked-out tree, so a commit made with
#              --no-verify, or from a clone that never set core.hooksPath, is still caught.
#
# The size checked is the blob git holds in the index, not the working-tree file, because the
# blob is what would enter history. The limit is 1 MB as 1,048,576 bytes; override with
# LARGE_FILE_LIMIT_BYTES for a test, never in a hook or a workflow.
set -euo pipefail

LIMIT_BYTES="${LARGE_FILE_LIMIT_BYTES:-1048576}"
mode="${1:---staged}"

case "$mode" in
  --staged) staged="$(git diff --cached --name-only --diff-filter=ACMR)" ;;
  --all)    staged="" ;;
  *) echo "usage: $0 [--staged|--all]" >&2; exit 2 ;;
esac

fail=0
checked=0
while IFS= read -r -d '' entry; do
  meta="${entry%%$'\t'*}"
  path="${entry#*$'\t'}"
  sha="$(printf '%s' "$meta" | awk '{print $2}')"
  if [ "$mode" = "--staged" ]; then
    grep -qxF -- "$path" <<<"$staged" || continue
  fi
  size="$(git cat-file -s "$sha")"
  checked=$((checked + 1))
  if [ "$size" -gt "$LIMIT_BYTES" ]; then
    printf 'LARGE FILE: %s is %d bytes, limit is %d bytes\n' "$path" "$size" "$LIMIT_BYTES"
    fail=1
  fi
done < <(git ls-files -z --stage)

if [ "$fail" -ne 0 ]; then
  echo "Refused: a file over the limit is in the ${mode#--} set. Keep data out of git (see .gitignore)." >&2
  exit 1
fi
printf 'check-large-files %s: %d file(s) checked, none over %d bytes\n' "$mode" "$checked" "$LIMIT_BYTES"
