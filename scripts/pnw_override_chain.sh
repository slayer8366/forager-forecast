#!/bin/bash
# Gate-override dispatch step 2 (Forager RECORD -854, -855): hedge, then main, then extras, one
# CPU job at a time, all under one 5G memory cap with no swap. Stops at the first failure.
# Run as: systemd-run --user --scope -q -p MemoryMax=5G -p MemorySwapMax=0 bash <this> > override_chain.log 2>&1
# (first run 2026-10-11 15:27Z from a copy in the data folder; this committed copy adds the ERR trap).
set -euo pipefail
# A failing step writes a FAILED line with its exit code before the chain stops (added after the
# 16:54:23Z extras stop left no line in the log).
trap 'rc=$?; echo "$(date -u +%FT%TZ) FAILED: step exited $rc at line $LINENO; the chain stopped"' ERR
cd ~/Zynergy/forager-forecast-pnw-pilot
echo "$(date -u +%FT%TZ) chain start at $(git rev-parse --short HEAD)"
echo "$(date -u +%FT%TZ) hedge"; scripts/pnw_hedge_run.sh --override "Forager RECORD -854"; echo "$(date -u +%FT%TZ) hedge exit $?"
echo "$(date -u +%FT%TZ) main";  scripts/pnw_t1_run_all.sh main --override "Forager RECORD -854"; echo "$(date -u +%FT%TZ) main exit $?"
echo "$(date -u +%FT%TZ) extras"; scripts/pnw_t1_run_all.sh extras; echo "$(date -u +%FT%TZ) extras exit $?"
echo "$(date -u +%FT%TZ) chain finished"
