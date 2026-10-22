#!/usr/bin/env bash
# Scratch revert runner: one edit per throwaway worktree at HEAD (CLAUDE.md runner rules), for the
# count's T1-units identity check and the fit's T1 land-route check.
set -u
MAIN=$HOME/.cache/forager-wt/t8-build
PY=$MAIN/.venv/bin/python
OUT=/mnt/work/scratch/t8-build/revert
run() {  # id, file, sed edit, module to import, pytest args
  local ID=$1 REL=$2 EDIT=$3 MOD=$4; shift 4
  local WT=$OUT/wt-$ID F
  rm -rf "$WT"; git -C "$MAIN" worktree prune
  git -C "$MAIN" worktree add -q --detach "$WT" HEAD
  F=$WT/$REL
  cp "$F" "$OUT/$ID.saved"
  sed -i "$EDIT" "$F"
  echo "== $ID: lines changed: $(diff "$OUT/$ID.saved" "$F" | grep -c '^>')"
  (cd "$WT" && PYTHONPATH=$WT/src systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 \
     nice -n 10 "$PY" -c "import $MOD as m; print('imported', m.__file__)" > "$OUT/import-$ID.log" 2>&1)
  (cd "$WT" && PYTHONPATH=$WT/src systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 \
     nice -n 10 "$PY" -m pytest -q -p no:cacheprovider "$@" > "$OUT/pytest-$ID.log" 2>&1)
  cat "$OUT/import-$ID.log"
  if ! grep -q "imported $WT/src" "$OUT/import-$ID.log"; then echo "REFUSE $ID: wrong module imported"
  elif grep -E -q "SyntaxError|ImportError|ModuleNotFoundError|error(s)? during collection|ERROR collecting" "$OUT/pytest-$ID.log"; then
    echo "REFUSE $ID: did not import or collect; results not cited"
  else grep -E "^E   .*(Error|DID NOT RAISE)|^FAILED|passed|failed" "$OUT/pytest-$ID.log" | head -8; fi
  cp "$OUT/$ID.saved" "$F"; cmp -s "$OUT/$ID.saved" "$F" && echo "restored $ID from saved copy"
  git -C "$MAIN" worktree remove --force "$WT"
}
run count-identity src/forager_forecast/t8/count.py \
  's/^    tu.check_same_units(t1, recounted, extra, expected_total)$/    pass/' \
  forager_forecast.t8.count tests/test_t8_count.py
run fit-land-route src/forager_forecast/t8/fit.py \
  's/^    if not np.array_equal(kinds, t1.land_point):$/    if False:/' \
  forager_forecast.t8.fit tests/test_t8_fit.py -k "land_point or prepare_lines"
git -C "$MAIN" status -s
grep -c "tu.check_same_units(t1, recounted, extra, expected_total)" $MAIN/src/forager_forecast/t8/count.py | sed 's/^/forward count identity present: /'
grep -c "if not np.array_equal(kinds, t1.land_point):" $MAIN/src/forager_forecast/t8/fit.py | sed 's/^/forward land-route check present: /'
