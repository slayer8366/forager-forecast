#!/usr/bin/env bash
# The pulls queue (dispatch 2026-10-26-pulls): one download at a time, in this order, each part
# stopping the queue when it stops itself. Started once, detached, by:
#   systemd-run --user --unit=forecast-pulls -p MemoryMax=2G -p MemorySwapMax=0 -p Nice=10 \
#     bash ~/.cache/forager-wt/t8b-build/scripts/pulls_queue.sh
# Part A runs from the t6b-rebuild worktree with its venv, Part B from this one with its venv; both
# venvs are on the drive (forecast-data/pulls-env). Daymet (Part B item 2) is not in the queue: a GET
# needs an Earthdata Login (checked 2026-10-26T12:40:57Z), so the dispatch says stop and report.
# The log is forecast-data/pulls/queue.log; PAUSE is forecast-data/PAUSE.
set -u
FD=/run/media/zynergy-labs/forager-storage/forecast-data
ENVS=$FD/pulls-env
A=$HOME/.cache/forager-wt/t6b-rebuild
B=$HOME/.cache/forager-wt/t8b-build
LOG=$FD/pulls/queue.log
mkdir -p "$FD/pulls"
say() { echo "$(date -u +%FT%TZ) [queue] $*" | tee -a "$LOG"; }
say "start: A at $(git -C "$A" rev-parse --short HEAD), B at $(git -C "$B" rev-parse --short HEAD)"
cd "$A" && "$ENVS/venv-t6b/bin/python" -I scripts/t6b_pulls.py; code=$?
say "Part A exit $code"
if [ "$code" -ne 0 ]; then say "queue stopped after Part A"; exit "$code"; fi
cd "$B" && "$ENVS/venv-t8b/bin/python" -I scripts/t8b_era5land_pull.py; code=$?
say "Part B (ERA5-Land) exit $code"
say "queue end: exit $code"
exit "$code"
