#!/usr/bin/env bash
# Review 2, question 3: my own revert check of 41f9c79's test, under CLAUDE.md's runner rules:
# the reverted file is restored from a copy saved before editing (never from git); the reverted
# build is checked for import errors before its result is read; the forward change is confirmed
# present afterwards. Output goes beside this script.
set -u
cd "$(dirname "$0")/../../.." || exit 1
F=src/forager_forecast/t7/model.py
T="tests/test_t7_model_outputs.py::test_a_fit_does_not_depend_on_the_scale_of_the_weights"
E=docs/audits/2026-10-16-t7-fit-review-2
PY=.venv/bin/python
SAVED=/tmp/review2_model_py.saved
cp "$F" "$SAVED" || exit 1
sha_before=$(sha256sum "$F" | cut -c1-16)
{
  echo "revert check run $(date -u +%FT%TZ) at $(git rev-parse --short HEAD)"
  echo "saved copy sha256 (16) $sha_before"
  echo "--- forward state: the test on the committed code"
  $PY -m pytest -q "$T" 2>&1 | tail -3
  echo "--- revert: train() passes the weights through unscaled"
  $PY - <<'PYEOF'
from pathlib import Path
p = Path("src/forager_forecast/t7/model.py")
s = p.read_text()
old = "weight=unit_mean_weights(w),"
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, "weight=np.asarray(w),"))
print("reverted one line")
PYEOF
  git diff --stat -- "$F"
  echo "--- reverted build compiles and imports?"
  if PYTHONPATH=src $PY -c "import forager_forecast.t7.model as m; print('import ok; train uses unit_mean_weights:', 'unit_mean_weights(w)' in open('$F').read())"; then
    echo "--- the test on the reverted code (expected: FAIL at the first assertion)"
    $PY -m pytest -q "$T" 2>&1 | grep -E "assert|Error|passed|failed|^E " | head -20
  else
    echo "REVERTED BUILD DOES NOT IMPORT: result not read"
  fi
  echo "--- restore from the saved copy, not from git"
  cp "$SAVED" "$F"
  sha_after=$(sha256sum "$F" | cut -c1-16)
  echo "restored sha256 (16) $sha_after (same as saved: $([ "$sha_before" = "$sha_after" ] && echo yes || echo NO))"
  echo "forward change present: $(grep -c 'weight=unit_mean_weights(w),' "$F") line(s); git diff empty: $(git diff --quiet -- "$F" && echo yes || echo NO)"
  echo "--- the test again on the restored code"
  $PY -m pytest -q "$T" 2>&1 | tail -2
} 2>&1 | tee "$E/revert_check.txt"
