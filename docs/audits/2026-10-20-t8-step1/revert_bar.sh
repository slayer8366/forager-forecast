#!/usr/bin/env bash
# Scratch revert runner for T8's bar, C1 to C4: one edit per throwaway worktree at HEAD.
# Under CLAUDE.md's runner rules: save a copy before editing, check the edit is exactly one line,
# read the import/collection log before results, restore from the saved copy (never git).
set -u
MAIN=$HOME/.cache/forager-wt/t8-build
PY=$MAIN/.venv/bin/python
OUT=/mnt/work/scratch/t8-build/revert
declare -A EDIT=(
  [C1]='s/^            c1\["low"\] > 0.0,$/            True,/'
  [C2]='s/^            c2\["low"\] > 0.0,$/            True,/'
  [C3]='s/^            c3\["p"\] <= C3_ALPHA,$/            True,/'
  [C4]='s/^            not c4\["low"\] > 0.0,$/            True,/'
)
for C in C1 C2 C3 C4; do
  WT=$OUT/wt-$C
  rm -rf "$WT"; git -C "$MAIN" worktree prune
  git -C "$MAIN" worktree add -q --detach "$WT" HEAD
  F=$WT/src/forager_forecast/t8/bar.py
  cp "$F" "$OUT/bar.py.saved-$C"
  sed -i "${EDIT[$C]}" "$F"
  CHANGED=$(diff "$OUT/bar.py.saved-$C" "$F" | grep -c '^>')
  echo "== $C: lines changed by the edit: $CHANGED"
  if [ "$CHANGED" != 1 ]; then echo "REFUSE $C: edit did not change exactly one line"; continue; fi
  (cd "$WT" && PYTHONPATH=$WT/src systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 \
     nice -n 10 "$PY" -c "import forager_forecast.t8.bar as b; print('imported', b.__file__)" \
     > "$OUT/import-$C.log" 2>&1)
  (cd "$WT" && PYTHONPATH=$WT/src systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 \
     nice -n 10 "$PY" -m pytest -q -p no:cacheprovider tests/test_t8_bar.py -rf > "$OUT/pytest-$C.log" 2>&1)
  cat "$OUT/import-$C.log"
  if ! grep -q "imported $WT/src/forager_forecast/t8/bar.py" "$OUT/import-$C.log"; then
    echo "REFUSE $C: the reverted bar.py was not the one imported"
  elif grep -E -q "SyntaxError|ImportError|ModuleNotFoundError|error(s)? during collection|ERROR collecting" "$OUT/pytest-$C.log"; then
    echo "REFUSE $C: the reverted build did not import or collect; results not cited"
  else
    grep -E "^FAILED|passed|failed" "$OUT/pytest-$C.log"
  fi
  cp "$OUT/bar.py.saved-$C" "$F"
  cmp -s "$OUT/bar.py.saved-$C" "$F" && echo "restored $C from saved copy"
  git -C "$MAIN" worktree remove --force "$WT"
done
git -C "$MAIN" status -s
grep -c -E 'c1\["low"\] > 0.0,|c2\["low"\] > 0.0,|c3\["p"\] <= C3_ALPHA,|not c4\["low"\] > 0.0,' "$MAIN/src/forager_forecast/t8/bar.py" | sed 's/^/forward conditions present in t8-build bar.py: /'
