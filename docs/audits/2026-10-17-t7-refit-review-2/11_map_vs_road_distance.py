import json, numpy as np
from scipy.stats import spearmanr
NEW = "/mnt/work/Zynergy/forecast-data/t7/refit/"; OLD = "/mnt/work/Zynergy/forecast-data/t7/fit/"
tab = np.load(NEW + "table.npz"); meta = json.load(open(NEW + "table_meta.json"))
road = tab["access"][:, meta["access_bands"].index("dist_road_m")].astype(np.float64)
cid_old = np.load(OLD + "table.npz")["cell_id"]; assert np.array_equal(cid_old, tab["cell_id"]), "cell lists differ"
out = {}
for name, d in (("new", NEW), ("old", OLD)):
    s = np.load(d + "scores_all.npy").astype(np.float64); ins = np.load(d + "inside_all.npy")
    r = spearmanr(s[ins], road[ins]).statistic
    top = ins & (s >= np.quantile(s[ins], 0.9))
    out[name] = dict(shaded=int(ins.sum()), spearman_score_vs_road_distance=float(r), top_decile_median_road_m=float(np.median(road[top])),
                     all_shaded_median_road_m=float(np.median(road[ins])), top_decile_share_over_1km=float((road[top] > 1000).mean()),
                     bottom_decile_median_road_m=float(np.median(road[ins & (s <= np.quantile(s[ins], 0.1))])))
    print(name, out[name])
json.dump(out, open("11_results.json", "w"), indent=1)
