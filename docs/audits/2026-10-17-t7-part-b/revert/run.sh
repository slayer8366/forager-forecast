#!/usr/bin/env bash
# One revert per scratch branch, in a separate worktree. Usage: run.sh NAME FILE PYTHON_EDIT TESTFILE
set -u
NAME=$1; FILE=$2; EDIT=$3; TEST=$4
REPO=~/Zynergy/forager-forecast-t7-part-b
WT=/tmp/hz-revert/wt-$NAME
PY=$REPO/.venv/bin/python
git -C $REPO worktree add -q -b revert-$NAME $WT HEAD || exit 2
cd $WT
cp "$FILE" /tmp/hz-revert/$NAME.saved
$PY -I -c "
import sys; p=sys.argv[1]; old,new=sys.argv[2].split('|||')
s=open(p).read(); n=s.count(old)
assert n==1, f'edit anchor found {n} times'
open(p,'w').write(s.replace(old,new))" "$FILE" "$EDIT" || { echo "EDIT FAILED"; exit 3; }
echo "--- diff"; git diff --stat; git diff | grep -E '^[-+][^-+]'
echo "--- run"
PYTHONPATH=$WT/src:$WT/tests $PY -m pytest -q -p no:cacheprovider "$TEST" --junitxml=/tmp/hz-revert/$NAME.xml > /tmp/hz-revert/$NAME.log 2>&1
echo "pytest exit $?"
echo "--- compile/collection errors in log:"; grep -E "ERROR collecting|SyntaxError|ImportError|ModuleNotFoundError|NameError" /tmp/hz-revert/$NAME.log || echo none
echo "--- module path used:"; PYTHONPATH=$WT/src $PY -c "import forager_forecast.t7.access as a; print(a.__file__)"
echo "--- failures:"; grep -E "^FAILED|^ERROR" /tmp/hz-revert/$NAME.log
grep -o 'tests="[0-9]*" \|failures="[0-9]*"\|errors="[0-9]*"' /tmp/hz-revert/$NAME.xml | head -3 | tr '\n' ' '; echo
cp /tmp/hz-revert/$NAME.saved "$FILE"; cmp "$FILE" /tmp/hz-revert/$NAME.saved && echo "restored from saved copy"
git diff --quiet && echo "scratch tree clean after restore"
cd /; git -C $REPO worktree remove --force $WT; git -C $REPO branch -D revert-$NAME -q
