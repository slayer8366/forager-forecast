"""Q5: re-derive the kept set from the registered download with my own filter, compare to specimens_kept.csv."""
import zipfile, csv, io, re, sys, collections, json
csv.field_size_limit(10**9)
Z = "/mnt/work/Zynergy/forecast-data/t7/specimens/0032050-260928105237408.zip"
z = zipfile.ZipFile(Z)
# dataset key -> title (xml) and title -> rights (rights.txt)
rights = {}
cur = None
for line in z.read("rights.txt").decode("utf-8").splitlines():
    if line.startswith("Dataset: "): cur = line[9:].strip()
    elif line.startswith("Rights as supplied:") and cur is not None: rights[cur] = line.split(":", 1)[1].strip(); cur = None
title = {}
for n in z.namelist():
    m = re.match(r"dataset/([0-9a-f-]{36})\.xml", n)
    if m:
        t = re.search(r"<title[^>]*>(.*?)</title>", z.read(n).decode("utf-8"), re.S)
        title[m.group(1)] = re.sub(r"\s+", " ", t.group(1)).strip() if t else None
def ok_lic(t):
    t = (t or "").lower()
    return ("publicdomain/zero/1.0" in t) or ("licenses/by/4.0" in t) or t in ("cc0_1_0", "cc_by_4_0")
mem = {}
for r in csv.DictReader(open("/mnt/work/Zynergy/forecast-data/t7/v9/membership_list_fungaltraits_export.tsv"), delimiter="\t"):
    mem[r["genus"]] = (r["lifestyle"], r["certainty"])
main = {g for g, (l, c) in mem.items() if l == "ectomycorrhizal" and c == "clear"}
print("ecm clear genera", len(main))
counts = collections.Counter(); kept = {}
with z.open("occurrence.txt") as f:
    rd = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in rd:
        counts["rows"] += 1
        if r["basisOfRecord"] != "PRESERVED_SPECIMEN": counts["not specimen"] += 1; continue
        dl = rights.get(title.get(r["datasetKey"]))
        if not ok_lic(dl): counts["dataset licence"] += 1; continue
        if not ok_lic(r["license"]): counts["record licence"] += 1; continue
        u = r["coordinateUncertaintyInMeters"].strip()
        try: uf = float(u)
        except ValueError: counts["no uncertainty"] += 1; continue
        if uf > 1000: counts["uncertainty > 1000"] += 1; continue
        if r["genus"] not in main: counts["genus not in main run"] += 1; continue
        kept[r["gbifID"]] = (r["genus"], r["year"], r["datasetKey"], r["decimalLatitude"], r["decimalLongitude"])
counts["kept_by_me"] = len(kept)
print(dict(counts))
theirs = {r["gbif_id"]: r for r in csv.DictReader(open("/mnt/work/Zynergy/forecast-data/t7/specimens/specimens_kept.csv"))}
a, b = set(kept), set(theirs)
print("mine", len(a), "theirs", len(b), "only mine", len(a - b), "only theirs", len(b - a))
print("examples only mine", [(i, kept[i][0]) for i in list(a - b)[:5]])
print("examples only theirs", list(b - a)[:5])
# unmatched dataset titles
print("datasets with no rights match:", sum(1 for k, t in title.items() if rights.get(t) is None))
json.dump({"counts": dict(counts), "only_mine": len(a - b), "only_theirs": len(b - a)}, open("10_results.json", "w"))
