#!/bin/bash
# The 2019-2025 model (owner, Forager RECORD -837: "2019–2025 model if all-years misses
# (Recommended)"). It goes live only if the all-years model is not fitted, checked and scored by
# Monday 2026-10-12 about 15:00 UTC, and it must pass the same gates first. One CPU job at a time.
# Order:
#   1. build the weather file from what has arrived;
#   2. equivalence --available: D24 daily (reported) and the hourly land-route check (gate) on
#      every sample span whose data are in; a land-route fail stops here;
#   3. held-out evaluation on 2019-2025 only, calendar and full, and their comparison, all
#      labelled PARTIAL (not the T1 result, whose headline comes only from the all-years run);
#   4. the scoring model on 2019-2025 (--final-only --years), labelled
#      "fitted on 2019-2025 only; T1's all-years result pending", with copernicus_sources.
set -euo pipefail
cd "$(dirname "$0")/.."
D=/home/zynergy-labs/Zynergy/forecast-data-pnw-pilot
H=$D/hedge
W=$H/weather.npz
YEARS=2019,2020,2021,2022,2023,2024,2025
mkdir -p "$H/fits" "$H/equivalence"

# Every time-series point against the gridded months; failing points are left out (2026-10-11).
uv run python scripts/pnw_ts_check.py "$D" > "$D/ts_check.log" || echo "ts check: some points failed; see $D/ts_check.json" >&2
uv run python scripts/pnw_ts_assemble.py "$D" > "$D/ts_assemble.log"
uv run python scripts/pnw_cds_precip_hourly.py --out "$D/cds" aggregate > "$D/rain_aggregate.log"
uv run python scripts/pnw_weather.py "$D/cds" "$W" > "$H/weather_build.log"
# Review S9: the gate needs every non-sea 2019-2025 sample span, not however many have arrived.
if ! uv run python scripts/pnw_equivalence.py "$D/records" "$W" "$D/cds" "$H/equivalence" \
    --available --require-years 2019-2025 > "$H/equivalence.log" 2>&1; then
  grep GATE "$H/equivalence.log" >&2 || true
  echo "gate failed; see $H/equivalence.log" >&2
  exit 3
fi
grep GATE "$H/equivalence.log"
for model in calendar full; do
  uv run python scripts/pnw_t1_fit.py --records "$D/records" --list t1_1000m --design primary \
    --model "$model" --weather "$W" --years "$YEARS" --out "$H/fits" --threads 4 \
    > "$H/fits/primary_t1_1000m_$model.log" 2>&1
  tail -1 "$H/fits/primary_t1_1000m_$model.log"
done
uv run python scripts/pnw_t1_compare.py "$H/fits" primary_t1_1000m > "$H/fits/comparison.log"
tail -30 "$H/fits/comparison.log"
uv run python scripts/pnw_t1_fit.py --records "$D/records" --list t1_1000m --design primary \
  --model full --weather "$W" --years "$YEARS" --out "$H/fits" --threads 4 --final-only \
  > "$H/fits/final_full.log" 2>&1
tail -1 "$H/fits/final_full.log"
