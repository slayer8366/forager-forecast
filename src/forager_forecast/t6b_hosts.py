"""T6b's own host-tree genus list, kept apart from T5's (Forager RECORD -1033 item 6).

The owner, on T7's M7 (Forager RECORD -1029): "M7 let's add them now, it's not a huge task now,
but it will be later." On the planner's six recommendations (RECORD -1033, provisional until
review): "All recommended". The go to build (RECORD -1037): "1 to 3 yes". Proposed genera and
their tree-table counts: docs/audits/2026-10-15-t6b-host-genera-verify-report.md, section 2, on
branch t6b-host-genera-verify; mycorrhizal statuses there are from memory, not yet checked
against a published genus list.

- T5's bands stay first and in T5's order, so the plot table's existing columns keep their
  meaning (the dispatch's stop condition); the new genera and the total follow.
- Genus strings are the TreeMap 2023 tree table's own. Tanoak is "Lithocarpus" there (9,999 rows,
  none under "Notholithocarpus", counted 2026-10-15), so its band is ``Lithocarpus``. Tanoak and
  chinquapin are two bands, not one Fagaceae band: each band keeps one meaning, a genus.
- Tier B genera are outside T5's class lists, so D116 classes them by FIA code (all broadleaf)
  and, as written, never counts them as hosts. Making them host bands needs D116 amended:
  proposed as D127, for the owner's review.
- ``ecm_hosts`` is the ectomycorrhizal-host total: the summed cover of its member genera as a
  share of canopy, like any genus band. Membership is listed explicitly so the owner can change
  it without touching the genus bands. Proposed: every genus band. Canada cannot supply it
  (SCANFI's classes mix hosts with non-hosts), so it is flagged not available there (D85).
- Crown widths: genera with no Bechtold 2004 Table 3 species of their own take quaking aspen's,
  as D89 (2) already provides (RECORD -1033 item 4).
"""

import hashlib

from forager_forecast.crown_cover import BANDS as T5_BANDS
from forager_forecast.crown_cover import HOST_GENERA as T5_HOST_GENERA

# Tier A: the Pacific Northwest pilot's hosts. Tier B: continental.
TIER_A_GENERA = ("Larix", "Betula", "Populus", "Alnus", "Lithocarpus", "Chrysolepis", "Arbutus")
TIER_B_GENERA = ("Fagus", "Carya", "Tilia", "Ostrya", "Carpinus")
T6B_HOST_GENERA = (*T5_HOST_GENERA, *TIER_A_GENERA, *TIER_B_GENERA)

ECM_HOSTS = "ecm_hosts"
# Proposed for the owner's review (report section 5): all eighteen genus bands.
ECM_HOST_MEMBERS = T6B_HOST_GENERA
HOST_TOTALS = {ECM_HOSTS: ECM_HOST_MEMBERS}

T6B_BANDS = (*T5_BANDS, *TIER_A_GENERA, *TIER_B_GENERA, ECM_HOSTS)


def band_layout(bands: tuple[str, ...], totals: dict[str, tuple[str, ...]]) -> str:
    """A short name for a band layout: the band names in order and each total's members."""
    text = ",".join(bands) + "|" + ";".join(f"{k}={','.join(v)}" for k, v in totals.items())
    return "t6b-bands-" + hashlib.sha256(text.encode()).hexdigest()[:12]


# Written into every tree tile's tags, its manifest line and the plot table. A tree unit counts
# as done only when its line names this layout (verify report finding F1), and the plot table
# is rebuilt when it differs (F2).
BAND_LAYOUT = band_layout(T6B_BANDS, HOST_TOTALS)
