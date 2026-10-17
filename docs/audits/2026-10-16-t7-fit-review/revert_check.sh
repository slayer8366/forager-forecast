#!/usr/bin/env bash
# Q3 revert check of 41f9c79's test, under Forager CLAUDE.md's runner rules:
#  - restore from a copy saved before editing, never from git;
#  - read the run log for import/collection errors before citing any result;
#  - confirm the forward change is present again afterwards.
# The revert: train() passes the raw weights to LightGBM instead of unit_mean_weights(w).
set -u
REPO=/home/zynergy-labs/Zynergy/forager-forecast-t7-fit-review
F=$REPO/src/forager_forecast/t7/model.py
EV=$REPO/docs/audits/2026-10-16-t7-fit-review
TEST=tests/test_t7_model_outputs.py
SAVED=$(mktemp /tmp/model.py.saved.XXXX)
cp "$F" "$SAVED"
before=$(sha256sum "$F" | cut -d' ' -f1)
cd "$REPO"

echo "== forward run (fix in place)"
.venv/bin/python -m pytest -q "$TEST" -p no:cacheprovider > "$EV/revert_forward.log" 2>&1
echo "exit $?"; tail -3 "$EV/revert_forward.log"

echo "== revert"
python3 - "$F" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = "weight=unit_mean_weights(w),"
assert s.count(old) == 1, "revert target not found exactly once"
open(p, "w").write(s.replace(old, "weight=np.asarray(w),"))
PY
git diff --stat -- "$F"
.venv/bin/python -m pytest -q "$TEST" -p no:cacheprovider > "$EV/revert_reverted.log" 2>&1
rc=$?
echo "exit $rc"
if grep -qE "ImportError|SyntaxError|NameError|errors? during collection|ERROR collecting" "$EV/revert_reverted.log"; then
  echo "COMPILE/COLLECTION ERROR in reverted run: results not citable"
fi
grep -E "^(FAILED|PASSED|ERROR)|passed|failed|assert" "$EV/revert_reverted.log" | head -20

echo "== restore from saved copy"
cp "$SAVED" "$F"
after=$(sha256sum "$F" | cut -d' ' -f1)
echo "before $before"; echo "after  $after"
[ "$before" = "$after" ] && echo "restored: identical to the saved copy" || echo "RESTORE MISMATCH"
grep -c "weight=unit_mean_weights(w)," "$F" | sed 's/^/forward change present, count: /'
git status --short -- "$F"
rm -f "$SAVED"
