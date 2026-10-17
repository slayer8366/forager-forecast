#!/usr/bin/env bash
# One revert check, under CLAUDE.md's runner rules. Args: id file forward_line reverted_line tests...
# Runs in its own scratch worktree on its own scratch branch; restores from a saved copy, never git.
set -u
id=$1; file=$2; fwd=$3; rev=$4; shift 4; tests=("$@")
wt=/tmp/t7c-revert-wt-$id
base=$(git -C ~/Zynergy/forager-forecast-t7-part-a rev-parse HEAD)
git -C ~/Zynergy/forager-forecast-t7-part-a worktree add -q -b scratch-t7c-revert-$id "$wt" "$base" || exit 2
cd "$wt"
save=/tmp/t7c-revert-tools/$id.saved
cp "$file" "$save"; before=$(sha256sum < "$save")
n=$(grep -cF -- "$fwd" "$file"); [ "$n" = 1 ] || { echo "[$id] forward line found $n times, not 1: STOP"; exit 3; }
python3 - "$file" "$fwd" "$rev" <<'PY'
import sys; p,f,r=sys.argv[1:]; s=open(p).read(); open(p,'w').write(s.replace(f,r,1))
PY
echo "[$id] diff --stat: $(git diff --stat | tail -1)"
xml=/tmp/t7c-revert-tools/$id.xml; log=/tmp/t7c-revert-tools/$id.log; rm -f "$xml" "$log"
uv sync -q --frozen >/dev/null 2>&1
echo "[$id] package imported from: $(uv run --frozen python -c "import forager_forecast;print(forager_forecast.__file__)")"
uv run --frozen pytest -q -p no:cacheprovider --junitxml="$xml" "${tests[@]}" > "$log" 2>&1
if grep -qE "SyntaxError|ImportError|ModuleNotFoundError|NameError|errors? during collection|INTERNALERROR" "$log" || [ ! -s "$xml" ]; then
  echo "[$id] BUILD/COLLECTION ERROR in the reverted run, results NOT cited"; grep -E "Error" "$log" | head -5
else
  python3 - "$xml" "$id" <<'PY'
import sys, xml.etree.ElementTree as E
r=E.parse(sys.argv[1]).getroot(); s=r if r.tag=='testsuite' else r[0]
print(f"[{sys.argv[2]}] tests {s.get('tests')} failures {s.get('failures')} errors {s.get('errors')}")
for tc in s.iter('testcase'):
    for f in list(tc.findall('failure'))+list(tc.findall('error')):
        msg=(f.get('message') or '').splitlines()[0][:160]
        print(f"[{sys.argv[2]}]   FAIL {tc.get('name')}: {msg}")
PY
fi
cp "$save" "$file"; after=$(sha256sum < "$file")
[ "$before" = "$after" ] && echo "[$id] restored from saved copy, sha256 equal" || echo "[$id] RESTORE MISMATCH"
echo "[$id] forward line present: $(grep -cF -- "$fwd" "$file"); git diff empty: $([ -z "$(git diff)" ] && echo yes || echo no)"
cd /tmp; git -C ~/Zynergy/forager-forecast-t7-part-a worktree remove "$wt" && git -C ~/Zynergy/forager-forecast-t7-part-a branch -q -D scratch-t7c-revert-$id
