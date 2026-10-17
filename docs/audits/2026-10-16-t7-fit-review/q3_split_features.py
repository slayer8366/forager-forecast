"""Q3 addendum: which inputs the unfixed and rescaled main full c16 models split on, and the
leaf counts per tree. Writes q3_split_features.json."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import common as c

meta = json.loads((c.WORK / "table_meta.json").read_text())
t = c.load_table(features=True)
le = c.effort_by_key("all", t["wkey"])
main = c.Rows(c.V9 / "presences_main.csv", table=t)
x = c.design(main, c.FULL, t["features"], meta["features"], le)
out = {}
for resc in (False, True):
    bst = c.fit(c.config("c16"), c.FULL, x, main.y, main.w, 4, rescale=resc)
    d = bst.dump_model()
    feats = Counter()
    leaves = Counter()
    def walk(n):
        if "split_feature" in n:
            feats[c.FULL[n["split_feature"]]] += 1
            walk(n["left_child"]); walk(n["right_child"])
    for tr in d["tree_info"]:
        walk(tr["tree_structure"]); leaves[tr["num_leaves"]] += 1
    out["rescaled" if resc else "unfixed"] = {"splits_by_feature": dict(feats),
                                              "trees_by_leaf_count": dict(leaves)}
(Path(__file__).parent / "q3_split_features.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
