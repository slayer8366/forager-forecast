#!/bin/bash
# T1 on the PNW box, all years, one CPU job at a time (planner, 2026-10-10).
# Usage: scripts/pnw_t1_run_all.sh [main|extras]
#   main:   build the weather file, then primary calendar + full, comparison, then the
#           random-date (secondary) design, calendar + full, comparison.
#   extras: D33 (3) the 5,000 m list and D33 (4) the CC0/CC BY list, primary design.
# Every fit refuses to start with uncommitted tracked files (review S2) and refuses a run over
# all years with any weather missing (review B3).
set -euo pipefail
cd "$(dirname "$0")/.."
D=/home/zynergy-labs/Zynergy/forecast-data-pnw-pilot
W=$D/weather/t1_pnw.npz
F=$D/fits
mkdir -p "$D/weather" "$F"
step=${1:-main}

fit() { # design list model
  uv run python scripts/pnw_t1_fit.py --records "$D/records" --list "$2" --design "$1" \
    --model "$3" --weather "$W" --out "$F" --threads 4 > "$F/$1_$2_$3.log" 2>&1
  tail -1 "$F/$1_$2_$3.log"
}

if [ "$step" = main ]; then
  uv run python scripts/pnw_weather.py "$D/cds" "$W" > "$D/weather/build.log"
  cp "$W.summary.json" "$D/weather/t1_pnw.summary.json"
  for design in primary secondary; do
    fit "$design" t1_1000m calendar
    fit "$design" t1_1000m full
    uv run python scripts/pnw_t1_compare.py "$F" "${design}_t1_1000m" > "$F/${design}_t1_1000m_comparison.log"
    tail -20 "$F/${design}_t1_1000m_comparison.log"
  done
else
  for list in t1_5000m t1_1000m_cc; do
    fit primary "$list" calendar
    fit primary "$list" full
    uv run python scripts/pnw_t1_compare.py "$F" "primary_$list" > "$F/primary_${list}_comparison.log"
    tail -20 "$F/primary_${list}_comparison.log"
  done
fi
