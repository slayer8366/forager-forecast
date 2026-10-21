#!/usr/bin/env bash
# T8's remaining fit parts, run one at a time after the forecast unit ends, so the chain does not
# depend on a session staying alive (forecast planner's instruction, 2026-10-21). Started as:
#   systemd-run --user --unit=t8-fit-runner -p MemoryMax=256M -p MemorySwapMax=0 \
#       --working-directory=$PWD scripts/t8_fit_runner.sh
# Each part is the dispatch's command (docs/dispatch/2026-10-20-t8-fit.md), with --wait added so
# the runner blocks until that part's unit ends. Stops the chain on any failed check, any non-zero
# exit, or a cap hit. Logs to /mnt/work/scratch/t8-fit/runner.log.
set -u

LOG_DIR=/mnt/work/scratch/t8-fit
LOG=$LOG_DIR/runner.log
COUNT=$HOME/Zynergy/forecast-data/t8/count
OUT=$HOME/Zynergy/forecast-data/t8/fit
WAIT_FOR=t8-fit-t1_1000m-forecast
MIN_KB=2621440 # 2.5 GiB
MEM_POLL=600   # 10 minutes
MEM_TRIES=13   # first check plus 12 waits: 2 hours
PARTS=(
    "t1_1000m alone"
    "t1_1000m challenger"
    "t1_1000m ecoregion"
    "t1_5000m bar"
    "t1_1000m_cc bar"
)

mkdir -p "$LOG_DIR"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >>"$LOG"; }
stop() { log "STOP: $*"; exit 1; }

no_t6b() {
    local units
    units=$(systemctl --user list-units --all 't6b*' --no-legend --no-pager)
    [ -z "$units" ] || stop "a t6b unit exists: $units"
}

mem_ok() {
    local i kb
    for ((i = 1; i <= MEM_TRIES; i++)); do
        kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
        if [ "$kb" -ge "$MIN_KB" ]; then
            log "MemAvailable $kb kB, at least $MIN_KB"
            return 0
        fi
        log "MemAvailable $kb kB, under $MIN_KB (check $i of $MEM_TRIES)"
        [ "$i" -lt "$MEM_TRIES" ] && sleep "$MEM_POLL"
    done
    stop "MemAvailable still under $MIN_KB kB after 2 hours"
}

log "runner started, waiting for $WAIT_FOR to end"
while systemctl --user is-active -q "$WAIT_FOR"; do
    no_t6b
    sleep 60
done
if systemctl --user is-failed -q "$WAIT_FOR"; then
    stop "$WAIT_FOR failed: $(systemctl --user show "$WAIT_FOR" -p Result --value)"
fi
[ -f "$OUT/t1_1000m_forecast.json" ] || stop "$WAIT_FOR ended without t1_1000m_forecast.json"
log "$WAIT_FOR ended, t1_1000m_forecast.json present"

for entry in "${PARTS[@]}"; do
    read -r design part <<<"$entry"
    unit="t8-fit-$design-$part"
    no_t6b
    mem_ok
    log "starting $unit"
    result=$(systemd-run --user --wait --unit="$unit" -p MemoryMax=3G -p MemorySwapMax=0 -p Nice=10 \
        --working-directory="$PWD" .venv/bin/python scripts/t8_fit.py --design "$design" \
        --part "$part" --count "$COUNT" --out "$OUT" 2>&1)
    code=$?
    while IFS= read -r line; do log "  $unit: $line"; done <<<"$result"
    if grep -qi "oom" <<<"$result"; then stop "$unit hit the memory cap"; fi
    [ "$code" -eq 0 ] || stop "$unit exited $code"
    [ -f "$OUT/${design}_${part}.json" ] || stop "$unit wrote no ${design}_${part}.json"
    log "$unit done"
done
log "all parts done"
