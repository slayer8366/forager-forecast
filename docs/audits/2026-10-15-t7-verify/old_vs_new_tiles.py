"""T7 verify V4 to V6: do the 24-band PNW tree tiles keep the 11-band tiles' values on the bands
they share? Read only; writes only <out.json>.

For every rebuilt tile of the box (current file under tiles/trees, old file under one of
superseded/20261015T*-trees/tiles/trees), compare each value band and flag band present in the
old file against the same-named band of the new file, over the whole tile: cells whose values
differ (NaN equal to NaN) and the largest absolute difference. The T6b review's checks (ten-cell,
edge, seam) were run on the old files; if the shared bands are identical they carry over.
No record of any fungus is read.
"""

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

T6B = Path("/run/media/zynergy-labs/2ebd084f-5fdd-4730-8cef-96b267723190/forecast-data/t6b")
SUP = sorted(T6B.glob("superseded/20261015T*-trees/tiles/trees"))


def bands(path):
    with rasterio.open(path) as ds:
        return {n: ds.read(i + 1) for i, n in enumerate(ds.descriptions)}


def main(out_path):
    res, summary = {}, {"tiles": 0, "tiles_all_equal": 0, "bands_compared": set()}
    for sup in SUP:
        for old_v in sorted(sup.glob("trees_256_*.tif")):
            key = old_v.name[len("trees_") : -len(".tif")]
            new_v = T6B / "tiles/trees" / old_v.name
            old_f = sup / f"trees_flags_{key}.tif"
            new_f = T6B / "tiles/trees" / f"trees_flags_{key}.tif"
            if not new_v.exists():
                res[key] = {"new_file": False}
                continue
            rec = {"from": str(sup.parent.parent.name)}
            for o, n in ((old_v, new_v), (old_f, new_f)):
                ob, nb = bands(o), bands(n)
                for name, a in ob.items():
                    summary["bands_compared"].add(name)
                    if name not in nb:
                        rec[name] = "missing in new"
                        continue
                    b = nb[name]
                    same = (a == b) | (np.isnan(a) & np.isnan(b)) if a.dtype.kind == "f" else a == b
                    diff = int((~same).sum())
                    if diff:
                        with np.errstate(invalid="ignore"):
                            m = np.nanmax(np.abs(a.astype("float64") - b.astype("float64")))
                        rec[name] = {"cells_differ": diff, "max_abs": float(m)}
            summary["tiles"] += 1
            summary["tiles_all_equal"] += len(rec) == 1
            res[key] = rec
    summary["bands_compared"] = sorted(summary["bands_compared"])
    summary["superseded_dirs"] = [str(s) for s in SUP]
    Path(out_path).write_text(json.dumps({"summary": summary, "tiles": res}, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
