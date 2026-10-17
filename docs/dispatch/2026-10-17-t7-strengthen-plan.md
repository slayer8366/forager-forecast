# Plan: strengthening T7 before it is shown (for the owner's decisions; no build)

Written by the planner (Rowan Waymark), 2026-10-17, at the owner's word: "Go ahead and write that plan". It follows the owner's ruling "Hold; strengthen first" (Forager RECORD -1146).

**Read against** (each fetched and read while writing):
- forager-forecast t7-build `b5c3d26` (the fit report) and main `b9127e5`;
- the two independent reviews: t7-fit-review `2a10348` (Sorrel Tally on Opus) and t7-fit-review-2 `20da09c` (Sorrel Tally on Fable);
- DECISIONS.md on t7-build, where the newest row is D144, so the next free is **D145**.

**Status: a plan.** Nothing here is authorised to build. Every numbered decision is the owner's, each with a recommendation.

## 1. Where T7 stands, and why it is held

The full model met the P10 bar (D140) by small margins. Both reviews reproduced every figure exactly. Their findings (Forager RECORD -1144, -1145), each from the review reports:
- **Effort carries almost all of the signal.** Effort alone scores 0.877; every habitat input together adds 0.004.
- **It isn't shown to hold across ecoregions.** Intervals clustered by block include zero.
- **The pass over B rests on choosing the three added bands on the same held-out blocks.** The base model, with no such choice, is not above B: +0.0008 (−0.0009, +0.0026).
- **Within one weather cell, where effort is constant,** the full model ranks the reported cell first 55 times in 100 (0.548), against effort-only's 0.494. Those pairs carry only 0.027% of the AUC's weight (review 2).
- **The map is nearly uncorrelated with effort** (−0.007). It ranks the little-searched interior mountains highest, and 46% of shaded cells lie outside T6's effort frame (both reviews).
- **The comparison group, a wood-rot genus (*Laetiporus*), gains more from the same inputs** (+0.023 over A). So the gain isn't shown to be about mycorrhizal hosts.

Both reviews' advice on what would most strengthen it:
- **Review 1:** "A test that does not ride on reporting effort. That means presences from the unsearched interior, or independent plot or survey data, scored against the map. Short of that, a contrast against the wood-rot comparison group, which would isolate the host-specific part."
- **Review 2:** "A within-cell test built into the bar … or a finer effort layer such as distance to roads and trails so the between-cell confounding is broken, together with a second comparison group chosen to share the forests but not the hosts".

## 2. The goal

Show, or fail to show, that the map carries a **habitat signal beyond where people search**, and that the signal is **specific to trees that host mycorrhizal fungi**, before anything is shown or published. A clear "no" is an acceptable outcome. The point is to know which.

## 3. The work, in four parts

**A. The reviews' fixes** (small, documents and reporting). These are needed whatever else is decided.
- A correcting line for the "26 level III blocks": it is 25, in the V9 report, the fit report and Forager RECORD -1126.
- The weighting fix's reach stated correctly: unfixed, no habitat model exists at all.
- Base minus B, and the within-cell AUC, printed beside every pooled AUC.
- A decision row for applying D144's 30-presence rule to the presences entering the fit (44 genera alone, not V9's 47).

**B. A finer effort layer, to break the between-cell confounding.** T6 measures effort per 0.1° weather cell. A cell-level proxy for access, such as distance to the nearest road or trail at 250 m, would let the model separate "easy to reach and searched" from "good forest" within each cell.
- *Unverified:* which source to use. Public-domain US federal road and trail layers would keep the forecast's CC BY-NC data licence clean. A share-alike source would not. The licence is checked at source before any download.

**C. A second comparison group that shares the forests but not the hosts.** Mushroom-forming genera whose primary lifestyle in FungalTraits is litter or soil saprotroph (forest-floor decomposers, not tree partners). They are chosen by that rule alone, fixed before any count is read, and a minimum count is set first.
- The **host-specific signal** is then the mycorrhizal group's gain minus this group's gain, on the same design.
- *Unverified:* how many such genera have enough records in the box. That is known only after counting, which is a point of no return (decision 4).

**D. A test that doesn't rely on reports at all.** Independent presences from the interior, such as federal fungal survey records or plot studies, scored against the map.
- *Unverified:* whether any such data exist openly for the PNW interior, and under what licence.
- **First step:** a read-only search that lists candidate sources, their coverage and licences, and downloads nothing.

## 4. The new bar, fixed before any new result is read

P10 asked only "above both comparisons, interval above zero". The reviews show that can pass on effort and band selection alone. A stricter bar is set before the re-fit, so it can't be tuned to the answer. The proposed bar, **P10b**, passes only if all four hold:
1. The full model is above B, with the **block-clustered** interval above zero (not only the weather-cell one).
2. The **within-cell** AUC is above effort-only's, with its interval above zero.
3. The **host-specific contrast** (part C) is above zero, with its interval above zero.
4. If part D finds data, the map ranks independent presences above background, with the interval above zero.

The exact form of each, and how many must pass, is the owner's to set (decision 2).

## 5. Order, cost and the points of no return

1. **Part A** (an hour or two of a coder; documents only).
2. **The read-only searches** for parts B and D (a reviewer-style session; no downloads).
3. **The owner rules on decisions 1 to 6,** with the search results in hand.
4. **Build parts B and C,** tests first, on a branch from t7-build, with Hazel Cairnwright as coder. Counting the new comparison group's presences is **-1030's first point of no return** again (decision 4).
5. **The re-fit,** about 14 hours as last time, likely more with the added layer (an estimate). Starting it is the second point of no return.
6. **Two independent reviews by Sorrel Tally,** on models other than the coder's (Forager -1134), compared by the planner.
7. **Publishing,** if anything, is a separate yes: the third point of no return.

The continental T6b run carries on beside this. The re-fit and T6b share the laptop as last time (6 of 8 cores), and Gradle doesn't run on it.

## 6. Decisions for the owner

1. **Do part A now?** *Recommended: yes.* It corrects the record whatever else happens.
2. **The new bar.** Adopt P10b's four conditions (the fourth only if data exist), or a subset. *Recommended: conditions 1 to 3 required; 4 required if part D finds usable data.*
3. **Run the two read-only searches** (the effort-layer source and its licence; independent interior presence data)? *Recommended: yes, as one session, nothing downloaded.*
4. **The second comparison group:** litter and soil saprotroph genera by FungalTraits' primary lifestyle, mushroom-forming, with a minimum of 30 presences per genus, pooled, fixed now. Counting them is a point of no return. *Recommended: adopt the rule now; count only after decisions 2 and 3.*
5. **If parts B to D can't be done** (no usable road or trail layer, no interior data): stop T7 for the PNW and move to T8, or re-fit with what can be done. *Recommended: decide after the searches report.*
6. **What the map would be called if it ever passes.** *Recommended: decide at publishing, from the evidence then.* For now, neither review supports "mycorrhizal habitat".

## 7. What this plan doesn't settle

- The cost and coverage of parts B and D (unknown until searched).
- Whether the S2 and S3 items from the earlier T6b review interact with a finer effort layer (not checked).
- Whether a stricter bar can be met at all.
