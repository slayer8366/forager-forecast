#!/usr/bin/env bash
# Copied, not imported, from the Forager repo: scripts/verify-inaturalist-access.sh at commit
# 175b050a0a507afb74686285c87fb36f72b9b548 (Forager origin/main, 2026-09-12), per T0b
# (docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md). The body below this header is the
# original, unchanged; its comments describe the Forager app, which is where it came from.
# Verifies network access to the iNaturalist website and public REST API
# (used by the Forager app for species identification/lookup).
set -euo pipefail

check() {
  local url="$1"
  local code
  # Reporting reachability is this script's whole job, so one unreachable host
  # must not abort the remaining checks via `set -e`. The failure is recorded and
  # printed, not swallowed: curl's own diagnostic still goes to stderr (-S) and
  # its exit code is shown in the report line.
  code=$(curl -sS -o /dev/null -w "%{http_code}" "$url") || code="unreachable (curl exit $?)"
  printf "%-55s -> HTTP %s\n" "$url" "$code"
}

check "https://www.inaturalist.org/"
check "https://api.inaturalist.org/v1/taxa?q=morel&per_page=1"
check "https://api.inaturalist.org/v1/observations?per_page=1"
