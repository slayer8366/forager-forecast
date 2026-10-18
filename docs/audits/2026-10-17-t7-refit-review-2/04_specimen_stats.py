import csv, collections, json
rows = list(csv.DictReader(open("/mnt/work/Zynergy/forecast-data/t7/specimens/specimens_kept.csv")))
n = len(rows); print("kept", n)
yr = [int(r["year"]) if r["year"] else None for r in rows]
print("no year", sum(y is None for y in yr))
dec = collections.Counter((y // 10 * 10) if y else None for y in yr); print("decades", sorted(dec.items(), key=lambda t: (t[0] is None, t[0])))
ds = collections.Counter(r["dataset_key"] for r in rows); print("datasets", len(ds), [(k[:8], v, round(v / n, 3)) for k, v in ds.most_common(6)])
co = collections.Counter((r["lat"], r["lon"]) for r in rows); print("unique coords", len(co), "max at one coordinate", co.most_common(3))
cells = collections.Counter(r["cell_id"] for r in rows); print("unique 250m cells", len(cells), "max per cell", cells.most_common(3))
print("cell_code", collections.Counter(r["cell_code"] for r in rows))
print("interior", collections.Counter(r["interior"] for r in rows))
u = [float(r["uncertainty_m"]) for r in rows]; print("uncert max", max(u), "min", min(u), "<=250", sum(x <= 250 for x in u), ">500", sum(x > 500 for x in u))
print("licences", collections.Counter(r["license"] for r in rows), collections.Counter(r["dataset_licence"] for r in rows))
print("genera", len(set(r["genus"] for r in rows)), collections.Counter(r["genus"] for r in rows).most_common(8))
print("level3", collections.Counter(r["level3"] for r in rows).most_common(8))
# by dataset: year range
by = collections.defaultdict(list)
for r, y in zip(rows, yr): by[r["dataset_key"]].append(y)
for k, v in sorted(by.items(), key=lambda t: -len(t[1]))[:4]:
    vv = [x for x in v if x]; print(k[:8], len(v), "years", min(vv), max(vv), "median", sorted(vv)[len(vv)//2])
