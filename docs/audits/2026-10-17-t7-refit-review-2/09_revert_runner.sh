#!/bin/bash
# Revert check per CLAUDE.md runner rules: save a copy first (never git), compile-check the mutated file
# and refuse to cite results if it does not compile, restore from the copy, verify the restore by sha256.
set -u
PY=../../../.venv/bin/python
cp rv2lib.py /mnt/work/Zynergy/rv2-scratch/rv2lib.py.saved
H0=$(sha256sum rv2lib.py | cut -d' ' -f1)
# the one-line mutation: the same-cell branch counts a presence "above" a background point when it scores BELOW it
sed -i 's/S = (ps\[:, None\] > qs\[None, :\]) + 0.5/S = (ps[:, None] < qs[None, :]) + 0.5/' rv2lib.py
if cmp -s rv2lib.py /mnt/work/Zynergy/rv2-scratch/rv2lib.py.saved; then echo "MUTATION DID NOT APPLY"; exit 2; fi
diff /mnt/work/Zynergy/rv2-scratch/rv2lib.py.saved rv2lib.py
if ! $PY -m py_compile rv2lib.py 2>/tmp/compile_err.txt; then echo "COMPILE ERROR - results not citable"; cat /tmp/compile_err.txt; cp /mnt/work/Zynergy/rv2-scratch/rv2lib.py.saved rv2lib.py; exit 3; fi
echo "--- mutated run ---"
$PY 09_positive_control_and_revert.py 2>&1 | grep -v Warn | tail -12
cp /mnt/work/Zynergy/rv2-scratch/rv2lib.py.saved rv2lib.py
H1=$(sha256sum rv2lib.py | cut -d' ' -f1)
[ "$H0" = "$H1" ] && echo "RESTORED: sha256 identical ($H1)" || echo "RESTORE MISMATCH"
echo "--- forward run after restore ---"
$PY 09_positive_control_and_revert.py 2>&1 | grep -v Warn | tail -3
