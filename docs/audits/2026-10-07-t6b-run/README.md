# T6b run evidence

`scripts/t6b_run.py` writes this folder at the end of every section and commits it.

## The manifest

- **`manifest.jsonl.gz` is frozen at bf9c315.** It is the manifest as of the section that ended on
  2026-10-18 at 07:00 PDT: 945,913 bytes gzipped, decompressing to 5,495,097 bytes and 13,659 lines,
  sha256 of the decompressed manifest `f37a352b34eefa5ab1bd554752ebdde4d77284b4b5d5b71b5f6788c866b1ebf3`.
  The next section's gzip, at 1,105,301 bytes, was over the repository's 1,048,576-byte limit, and
  the commit was refused. Since dispatch `docs/dispatch/2026-10-19-t6b-progress-save.md` (forecast
  RECORD 2026-09-28-2012), the runner no longer writes the gzip here. The file stays as it was last
  committed, and history isn't rewritten.
- **The live manifest** is on the flash drive, at `<drive>/forecast-data/t6b/manifest.jsonl`.
- **A gzipped copy outside every repository** is at
  `/mnt/work/Zynergy/forecast-data/t6b/manifest.jsonl.gz`. It is replaced each section.
- **`manifest_summary.json`** is what git keeps of the manifest each section:
  - the sha256 of the manifest, its size in bytes and its line count;
  - the line count of each `kind`;
  - the units, counted on the latest line per unit (as `done_units` reads them), by layer and
    status.

  A reader verifies the copy outside the repository, or the drive's manifest, by checking that its
  decompressed sha256 matches the summary. The summary describes the manifest as of the section
  that committed it.

## The rest

- `sections.jsonl`: one line per section, with that section's summary per stage.
- `run.log.txt`: the runner's log, copied from the drive each section.
- `mask.json`, `tiles_trees.json`, `tiles_soil.json`: copied from the drive each section.
- The `*.py.txt` and `*.out.txt` files are one-off probes, kept as they ran.
