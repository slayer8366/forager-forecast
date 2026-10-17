"""Read-only: lifestyle values in the committed FungalTraits export, and the saprotroph rule's
edge cases (no counts of records are read)."""

from collections import Counter, defaultdict

from forager_forecast.t7 import fungaltraits as ft

t = ft.read_traits_export()
print("rows", len(t))
print(Counter(x.primary for x in t).most_common())
SAP = {"litter_saprotroph", "soil_saprotroph"}
by = defaultdict(list)
for x in t:
    by[x.genus].append(x)
sap = [x for x in t if x.primary in SAP]
mush = [x for x in sap if x.fruitbody in ft.MUSHROOM_FRUITBODIES]
print("sap rows", len(sap), "mushroom-forming", len(mush), "genera", len({x.genus for x in mush}))
print("fruitbody of sap rows", Counter(x.fruitbody for x in sap).most_common())
multi = {g for g in {x.genus for x in sap} if len(by[g]) > 1}
print("sap genera on >1 row:", {g: [(r.primary, r.fruitbody) for r in by[g]] for g in multi})
ecm = [x.genus for x in mush if "ectomycorrhizal" in (x.secondary + x.lifestyle_comment).lower()]
print("mushroom sap genera with ECM in secondary/comment:", ecm)
print(
    "with any secondary:",
    sum(1 for x in mush if x.secondary),
    Counter(x.secondary for x in mush if x.secondary).most_common(12),
)
rows = ft.to_list_rows(t, "x")
cls = {r.genus: (r.lifestyle, r.certainty) for r in rows}
print("their list class:", Counter(cls[x.genus] for x in mush))
print(
    "unspecified_saprotroph mushroom-forming genera:",
    sum(
        1
        for x in t
        if x.primary == "unspecified_saprotroph" and x.fruitbody in ft.MUSHROOM_FRUITBODIES
    ),
)
