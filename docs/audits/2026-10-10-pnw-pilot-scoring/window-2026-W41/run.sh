#!/bin/bash
# Scoring-window pull for 2026-W41 (2026-07-01 to 2026-10-04) by the builder's --scoring routes.
cd ~/Zynergy/forager-forecast-pnw-scoring || exit 9
D=~/Zynergy/forecast-data-pnw-pilot
uv run --with cdsapi==0.7.7 python scripts/pnw_cds_precip_hourly.py --out $D/cds pull --scoring > $D/scoring/pull-2026-W41/rain.log 2>&1 &
R=$!
uv run --with cdsapi==0.7.7 python scripts/pnw_cds_hourly_pull.py --out $D/cds --scoring --workers 4 > $D/scoring/pull-2026-W41/land.log 2>&1
L=$?
wait $R; RC=$?
echo "$(date -u +%FT%TZ) land_exit=$L rain_exit=$RC" >> $D/scoring/pull-2026-W41/done.log
