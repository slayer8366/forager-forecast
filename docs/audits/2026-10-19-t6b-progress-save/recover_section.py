"""Commit the 2026-10-18 section the refused save lost.

Dispatch 2026-10-19-t6b-progress-save, step 2.

Run once, from the runner's worktree, after the over-size gzip has been set back to HEAD and with
run.log.txt and sections.jsonl still staged from the failed save:

    .venv/bin/python docs/audits/2026-10-19-t6b-progress-save/recover_section.py

It writes the first summary of the drive's manifest and the gzipped copy outside the repository
(the same functions the runner now uses), checks the summary against the drive manifest and the
copy, and commits run.log.txt, sections.jsonl and the summary under the lost section's original
message, through the large-file hook. It appends nothing: sections.jsonl already holds the line.
"""

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from forager_forecast.t6b_run import EVIDENCE_SUMMARY, commit_paths, save_manifest_outside

REPO = Path.cwd()
DRIVE_T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
MANIFEST = DRIVE_T6B / "manifest.jsonl"
COPY_DIR = Path("/mnt/work/Zynergy/forecast-data/t6b")
EVIDENCE = REPO / "docs" / "audits" / "2026-10-07-t6b-run"


def log(msg: str) -> None:
    print(msg, flush=True)


summaries = json.loads((EVIDENCE / "sections.jsonl").read_text().splitlines()[-1])["summaries"]
summary = save_manifest_outside(MANIFEST, COPY_DIR)
drive_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
copy_bytes = gzip.decompress(Path(summary["copy_outside_git"]).read_bytes())
copy_sha = hashlib.sha256(copy_bytes).hexdigest()
log(f"summary sha256 {summary['sha256']}")
log(f"drive manifest  {drive_sha}")
log(f"outside copy    {copy_sha}")
if not summary["sha256"] == drive_sha == copy_sha:
    sys.exit("the summary does not match the drive manifest or its copy: stop")
(EVIDENCE / EVIDENCE_SUMMARY).write_text(json.dumps(summary, indent=1) + "\n")
log(json.dumps(summary, indent=1))
done = sum(s.get("units_done_now", 0) for s in summaries)
msg = (f"T6b run section: {done} tiles; " + "; ".join(
    f"{s.get('layer')}: {s.get('units_ok')} ok, {s.get('units_deferred')} deferred, "
    f"{s.get('units_failed', 0)} failed, "
    f"{s.get('units_remaining')} left, {s.get('stopped')}" for s in summaries)
    + "\n\nCommitted after the refused save of 2026-10-18 22:12 PDT, with the first manifest "
    "summary (dispatch 2026-10-19-t6b-progress-save, step 2)."
    + "\n\nCo-Authored-By: Claude <noreply@anthropic.com>")  # fmt: skip
paths = [EVIDENCE / "run.log.txt", EVIDENCE / "sections.jsonl", EVIDENCE / EVIDENCE_SUMMARY]
ok = commit_paths(REPO, paths, msg, log)
log(subprocess.run(["git", "log", "--stat", "-1"], cwd=REPO, capture_output=True, text=True).stdout)
sys.exit(0 if ok else 1)
