"""Canopy cover per genus from an FIA tree list: the US side of T5's genus fraction (D87).

The formula and its sources are in docs/audits/2026-10-06-t5-verify-report.md, section 2:

- Largest crown width (ft) of a stand-grown tree, LCW = b0 + b1 D + b2 D^2, with D the d.b.h. in
  inches: Bechtold, W.A. 2004. Largest-crown-width prediction models for 53 species in the western
  United States. West. J. Appl. For. 19(4):245-251, Equation 3, coefficients from Table 3. Fitted on
  trees of 5.0 in d.b.h. and larger, so smaller trees carry no crown here.
- Crown area is a circle of that width, and plot cover follows Crookston, N.L. and Stage, A.R. 1999,
  RMRS-GTR-24: without overlap C' = 100 * sum(p_i a_i) / 43560 (their equation 1), with overlap
  C = 100 * (1 - exp(-0.01 C')) (their equation 2).
- A genus's cover is C times its share of sum(p_i a_i). Splitting the overlap-corrected cover pro
  rata is inferred from equation 2's random-placement assumption, not stated by the authors; it
  makes the genus covers sum to C, as SCANFI v2's species crown closures sum to its total.

A species not in Table 3 takes a surrogate, by a rule fixed before any value was seen: the
same-genus Table 3 species with the most observations in Bechtold's Table 1 (woodland species
excluded, since their D is root-collar diameter), else the class default with the most
observations (Douglas-fir for conifers, quaking aspen for broadleaf trees). Every surrogate use is
counted, and the surrogate widths can be scaled to measure how much the rule matters.
"""

import math
from collections.abc import Iterable
from dataclasses import dataclass, field

MIN_DBH_IN = 5.0
SQUARE_FEET_PER_ACRE = 43560.0

# FIA species code: (b0, b1, b2), Bechtold 2004 Table 3. A dash in the table is b2 = 0.
BECHTOLD_2004_EQ3: dict[int, tuple[float, float, float]] = {
    # Softwood species
    11: (7.3037, 0.5909, 0.0),  # Pacific silver fir
    15: (4.4965, 0.9238, -0.0120),  # white fir
    17: (5.7545, 1.1196, -0.0147),  # grand fir
    18: (6.0730, 0.3756, 0.0),  # corkbark fir
    19: (3.9629, 0.6469, 0.0),  # subalpine fir
    20: (4.7623, 0.5222, 0.0),  # California red fir
    21: (4.0524, 0.6423, 0.0),  # Shasta red fir
    22: (6.3260, 0.6588, 0.0),  # noble fir
    41: (2.3625, 0.9974, 0.0),  # Port-Orford cedar
    62: (-2.1213, 1.7308, -0.0243),  # California juniper (w)
    64: (-0.0037, 1.3526, -0.0165),  # western juniper (w)
    65: (2.4349, 0.9000, -0.0177),  # Utah juniper (w)
    66: (2.1431, 1.3447, -0.0228),  # Rocky Mountain juniper (w)
    69: (5.7367, 0.4932, 0.0),  # oneseed juniper (w)
    73: (4.5176, 0.7931, 0.0),  # western larch
    81: (4.1207, 0.9773, -0.0107),  # incense cedar
    93: (5.1218, 0.5547, 0.0),  # Engelmann spruce
    98: (8.8087, 0.7825, 0.0),  # Sitka spruce
    101: (2.6531, 0.8015, 0.0),  # whitebark pine
    102: (7.4251, 0.8991, 0.0),  # Rocky Mountain bristlecone pine
    106: (-1.2638, 1.9922, -0.0410),  # common pinyon (w)
    108: (-1.1994, 1.5154, -0.0232),  # lodgepole pine
    113: (4.0181, 0.8528, 0.0),  # limber pine
    116: (4.2675, 0.7714, 0.0),  # Jeffrey pine
    117: (4.8657, 0.7890, 0.0),  # sugar pine
    119: (4.2840, 0.6949, 0.0),  # western white pine
    122: (2.3089, 1.1388, -0.0089),  # ponderosa pine
    127: (4.3699, 1.2524, 0.0),  # grey pine
    133: (2.5093, 0.8503, 0.0),  # singleleaf pinyon (w)
    202: (5.7753, 1.0639, -0.0109),  # Douglas-fir
    211: (12.0128, 0.4576, 0.0),  # redwood
    242: (8.1993, 1.1134, -0.0165),  # western redcedar
    263: (5.0036, 1.1808, -0.0107),  # western hemlock
    264: (3.2343, 0.6927, 0.0),  # mountain hemlock
    # Hardwood species
    312: (10.0915, 1.1139, 0.0),  # bigleaf maple
    321: (10.5451, 0.9493, 0.0),  # Rocky Mountain maple (w)
    322: (4.0040, 1.0604, 0.0),  # bigtooth maple (w)
    351: (4.7027, 1.3537, 0.0),  # red alder
    352: (9.7927, 0.9006, 0.0),  # white alder
    361: (5.7785, 0.9832, 0.0),  # Pacific madrone
    475: (3.5082, 0.8770, 0.0),  # curlleaf mountain-mahogany (w)
    631: (6.7864, 0.8443, 0.0),  # tanoak
    746: (2.5515, 1.2029, 0.0),  # quaking aspen
    749: (2.8848, 1.5866, 0.0),  # narrowleaf cottonwood
    801: (0.5740, 1.8475, 0.0),  # coast live oak
    805: (6.1397, 1.0109, 0.0),  # canyon live oak
    807: (3.9281, 1.5550, 0.0),  # blue oak
    814: (3.0334, 0.9834, 0.0),  # Gambel oak (w)
    815: (-1.3160, 2.9311, -0.0866),  # Oregon white oak
    818: (7.0284, 1.0470, 0.0),  # California black oak
    821: (2.9954, 1.9137, 0.0),  # valley oak
    839: (5.1005, 1.6359, 0.0),  # interior live oak
    981: (7.3204, 1.4420, 0.0),  # California laurel
}

# Observations per species, Bechtold 2004 Table 1; used only to choose a surrogate.
BECHTOLD_2004_N: dict[int, int] = {
    11: 218, 15: 855, 17: 610, 18: 68, 19: 1262, 20: 160, 21: 63, 22: 50, 41: 78, 62: 28,
    64: 302, 65: 402, 66: 144, 69: 98, 73: 183, 81: 220, 93: 1205, 98: 53, 101: 97, 102: 26,
    106: 278, 108: 2761, 113: 164, 116: 108, 117: 118, 119: 84, 122: 1413, 127: 37, 133: 323,
    202: 4088, 211: 55, 242: 439, 263: 1008, 264: 209, 312: 106, 321: 70, 322: 48, 351: 409,
    352: 37, 361: 164, 475: 227, 631: 534, 746: 1383, 749: 44, 801: 87, 805: 440, 807: 184,
    814: 248, 815: 126, 818: 239, 821: 29, 839: 79, 981: 28,
}  # fmt: skip

# Woodland species, marked (w) in the paper: D is diameter at root collar, not d.b.h.
WOODLAND = frozenset({62, 64, 65, 66, 69, 106, 133, 321, 322, 475, 814})

# Genus of each Table 3 species (the paper gives common names; genera as in the FIA tree table).
TABLE_3_GENUS: dict[int, str] = {
    **dict.fromkeys((11, 15, 17, 18, 19, 20, 21, 22), "Abies"),
    41: "Chamaecyparis",
    **dict.fromkeys((62, 64, 65, 66, 69), "Juniperus"),
    73: "Larix",
    81: "Calocedrus",
    93: "Picea",
    98: "Picea",
    **dict.fromkeys((101, 102, 106, 108, 113, 116, 117, 119, 122, 127, 133), "Pinus"),
    202: "Pseudotsuga",
    211: "Sequoia",
    242: "Thuja",
    263: "Tsuga",
    264: "Tsuga",
    **dict.fromkeys((312, 321, 322), "Acer"),
    351: "Alnus",
    352: "Alnus",
    361: "Arbutus",
    475: "Cercocarpus",
    631: "Lithocarpus",
    746: "Populus",
    749: "Populus",
    **dict.fromkeys((801, 805, 807, 814, 815, 818, 821, 839), "Quercus"),
    981: "Umbellularia",
}

CONIFER_GENERA = frozenset({
    "Abies", "Callitropsis", "Calocedrus", "Chamaecyparis", "Cupressus", "Hesperocyparis",
    "Juniperus", "Larix", "Picea", "Pinus", "Pseudotsuga", "Sequoia", "Sequoiadendron", "Taxus",
    "Thuja", "Torreya", "Tsuga", "Xanthocyparis",
})  # fmt: skip
BROADLEAF_GENERA = frozenset({
    "Acer", "Aesculus", "Alnus", "Arbutus", "Betula", "Castanopsis", "Cercocarpus", "Chrysolepis",
    "Cornus", "Corylus", "Crataegus", "Eucalyptus", "Fraxinus", "Ilex", "Juglans", "Lithocarpus",
    "Malus", "Notholithocarpus", "Platanus", "Populus", "Prunus", "Pyrus", "Quercus", "Rhamnus",
    "Robinia", "Salix", "Sorbus", "Ulmus", "Umbellularia",
})  # fmt: skip
CONIFER_DEFAULT = 202  # Douglas-fir, n = 4088
BROADLEAF_DEFAULT = 746  # quaking aspen, n = 1383

HOST_GENERA = ("Pseudotsuga", "Tsuga", "Picea", "Abies", "Pinus", "Quercus")
BANDS = (*HOST_GENERA, "conifer", "broadleaf")


class UnknownGenus(ValueError):
    """A genus in neither class list: refused, since its class cannot be guessed."""


def is_conifer(genus: str) -> bool:
    if genus in CONIFER_GENERA:
        return True
    if genus in BROADLEAF_GENERA:
        return False
    raise UnknownGenus(f"genus {genus!r} is in neither the conifer nor the broadleaf list")


def surrogate_for(spcd: int, genus: str) -> int:
    """The Table 3 species whose coefficients ``spcd`` uses (itself when it is in the table)."""
    if spcd in BECHTOLD_2004_EQ3:
        return spcd
    conifer = is_conifer(genus)
    mates = [s for s, g in TABLE_3_GENUS.items() if g == genus and s not in WOODLAND]
    if mates:
        return max(mates, key=lambda s: BECHTOLD_2004_N[s])
    return CONIFER_DEFAULT if conifer else BROADLEAF_DEFAULT


def crown_width_for(spcd: int, genus: str, dbh_in: float) -> tuple[float, int]:
    """(largest crown width in ft, the Table 3 species whose coefficients were used)."""
    used = surrogate_for(spcd, genus)
    b0, b1, b2 = BECHTOLD_2004_EQ3[used]
    return b0 + b1 * dbh_in + b2 * dbh_in * dbh_in, used


@dataclass(frozen=True)
class Tree:
    spcd: int
    genus: str
    dbh_in: float
    tpa: float
    live: bool


@dataclass
class PlotCover:
    """Percent canopy cover with overlap (Crookston and Stage eq. 2), split by band."""

    total: float
    by_band: dict[str, float]
    surrogate_trees: int = 0
    surrogate_species: dict[int, int] = field(default_factory=dict)


def plot_cover(trees: Iterable[Tree], surrogate_width_scale: float = 1.0) -> PlotCover:
    crown = dict.fromkeys(BANDS, 0.0)
    total_pa = 0.0
    surrogate_trees = 0
    surrogate_species: dict[int, int] = {}
    for t in trees:
        if not t.live or not (t.dbh_in >= MIN_DBH_IN) or not (t.tpa > 0):
            continue
        width, used = crown_width_for(t.spcd, t.genus, t.dbh_in)
        if used != t.spcd:
            surrogate_trees += 1
            surrogate_species[t.spcd] = used
            width *= surrogate_width_scale
        if width <= 0:
            continue
        pa = t.tpa * math.pi * (width / 2.0) ** 2
        total_pa += pa
        if t.genus in crown:
            crown[t.genus] += pa
        crown["conifer" if is_conifer(t.genus) else "broadleaf"] += pa
    c_prime = 100.0 * total_pa / SQUARE_FEET_PER_ACRE
    total = 100.0 * (1.0 - math.exp(-0.01 * c_prime))
    if total_pa > 0:
        by_band = {band: total * crown[band] / total_pa for band in BANDS}
    else:
        by_band = dict.fromkeys(BANDS, 0.0)
    return PlotCover(total, by_band, surrogate_trees, surrogate_species)
