# T8 fit results: the headline and every no-verdict part

Filed by the forecast planner (Alder Bearing), 2026-10-21. Intent: forecast RECORD 2026-09-28-2036, with -2037 and
-2038. The figures were read from the output JSON in `~/Zynergy/forecast-data/t8/fit/` by script. All 14 output
files are read-only, and `sha256sum -c SHA256SUMS` passes for all 14. The outputs are not committed, because the
repository is public; the headline's figures are also in `headline-bar.md`. Runs are from the runner log
(`/mnt/work/scratch/t8-fit/runner.log`) and from Ash's reports. Every part ran under a 3 GB cap with swap off,
and none came within 2 GB of it.

Skill is Brier skill against the named baseline, with its interval from 1,000 resamples of cells (seed
20260918). Positive skill means the weather model did better.

## Headline: t1_1000m, bar. Verdict: FAIL

52,718 units with 1,138 positive. Code 49862a1; 14:25 to 14:57Z, peak 915 MB.

| | Result | Needs | |
|---|---|---|---|
| C1, against T1's calendar | −0.01108 [−0.01762, −0.00503] | wholly above 0 | fail |
| C2, against no-weather | −0.00138 [−0.00405, +0.00086] | wholly above 0 | fail |
| C3, 199 whole-year swaps | 173 at or above, p = 0.870 | p ≤ 0.05 | fail |
| C4, lichen guard | +0.00215 [+0.00027, +0.00394] | not wholly above 0 | fail |

## Reported beside, no verdict

**2015–2023 line** (32,871 units, 529 positive):
- against the calendar: −0.0127 [−0.0206, −0.0051];
- against no-weather: −0.0060 [−0.0111, −0.0016].

**Forecast timing** (windows end 8 days before the week). It fails C1 to C4:
- C1: −0.01111 [−0.01722, −0.00507];
- C2: −0.00140 [−0.00403, +0.00054];
- C3: p = 0.840;
- C4: +0.00196 [+0.00032, +0.00349].

**Each measure alone** (the no-weather model plus one measure, against no-weather; 199 swaps each):

| | Measure | Skill | Swaps p |
|---|---|---|---|
| W1 | rain, 14 days | −0.00012 [−0.00067, +0.00041] | 0.370 |
| W2 | rain, 56 days | −0.00346 [−0.00597, −0.00151] | 0.975 |
| W3 | soil moisture, 7 days | +0.00041 [−0.00028, +0.00111] | 0.155 |
| W4 | soil temperature, 14 days | +0.00190 [+0.00055, +0.00324] | 0.410 |

Planner's reading of W4, inferred and not checked: it helps against no-weather, but a swapped year helps about
as much (p = 0.41). So what it adds looks like seasonal temperature, not that year's weather.

**The tree challenger** (D133 (6); tuning fixed per fold on true weather, D136). It fails, clearing 1 of 4:
- C1: +0.00236 [−0.00075, +0.00582];
- C2: +0.00131 [−0.00062, +0.00317];
- C3: 29 of 199, p = 0.150. The output carries the label "slightly generous to true weather: each swap keeps the
  fold's tuning chosen on true weather (D136, M-challenger-swaps)";
- C4: −0.00147 [−0.00357, +0.00074], which passes.

**By ecoregion** (leave one CEC level III block out; main against no-weather). Pooled: +0.00129 [−0.00044,
+0.00310]. The informative blocks (≥ 30 positives):

| Block | Units | Positives | Skill |
|---|---|---|---|
| 6.2.5 | 2,923 | 68 | −0.0056 |
| 6.2.7 | 5,599 | 183 | +0.0043 |
| 7.1.7 | 17,454 | 343 | −0.0003 |
| 7.1.8 | 6,571 | 281 | +0.0025 |
| 7.1.9 | 6,603 | 32 | +0.0248 |
| none | 10,254 | 197 | +0.0048 |

There are also 7 thin blocks, kept in the pool. "none" means 10,254 units whose cell centre lies in no
polygon. That is 19% of units; the cause is not yet checked.

**D33 (3), the 5,000 m list** (D137: 34 units, 2 of them positive, in 33 cells outside T6's frame, were
dropped; 56,893 units left). It fails C1 to C4:
- C1: −0.01778 [−0.02606, −0.01089];
- C2: −0.00182 [−0.00476, +0.00048];
- C3: p = 0.880;
- C4: +0.00243 [+0.00069, +0.00424].

**D33 (4), the commercial-safe list** (9,640 units, effort from T6's cc track). It fails C1 to C3 and passes
C4:
- C1: −0.02331 [−0.03627, −0.01280];
- C2: −0.02088 [−0.03419, −0.01132];
- C3: p = 0.940;
- C4: +0.00340 [−0.00355, +0.01045].

## Runs

| Part | Code | Runtime | Peak |
|---|---|---|---|
| bar | 49862a1 | 31 min 53 s | 915 MB |
| forecast | 49862a1 | about 34 min | 862 MB (Ash's watcher; not in the runner log) |
| alone | 88fac57 | 1 h 23 min 50 s | 906 MB |
| challenger | 88fac57 | 56 min 30 s | 862 MB |
| ecoregion | 88fac57 | 1 min 5 s | 902 MB |
| 5,000 m bar | c48be9f (fit code 4554ddc) | 31 min 38 s | 890 MB |
| cc bar | c48be9f | 6 min 5 s | 891 MB |

The first 5,000 m run stopped at 17:54Z with NoEffortValue, and D137 settled it. No refusal for any other
reason, and no cap hit.

## sha256

```
24748a817622fb9b2e29a0507bde7ac9fbbd963945806a3b3def3c6e61b8b034  t1_1000m_alone.json
fd38cc6f9977fc95ebef7a036c13e1f6539d158cd18f8fc6f9a0b47a3bfe8120  t1_1000m_bar.json
f788286209768369595b23c09da16167542114e4c78fba50808f750e5eca064a  t1_1000m_challenger.json
d4911bb2f10e1a95373f0e0a137f8e5a7380e6e998ace786db331e5a6d6daa58  t1_1000m_ecoregion.json
3f473c629b8d69ce569eb98d75e71d2d0200f6fb5143f5b9c77eb118e1c1fb29  t1_1000m_forecast.json
59c00bf42716ce195bfc955edf4ad423809816d3f79403216019214d08d97ea0  t1_1000m_alone.npz
3011a6c3fc5f6486b18d21027be6c2b97ce8090503df4fcf5dc1d20345650805  t1_1000m_bar.npz
fce40513dc0a885e6f40912b3168ee6b690bee9bcd4e43076627ff02e3d3461c  t1_1000m_challenger.npz
64c3fac2cfd5a0e0ce5e9b43fe33013ec7580695adf36ab9d424ed2b2ee9e1b2  t1_1000m_ecoregion.npz
c710b14df394cd6adffe65fa6ff5189d32b9a3564a8e71e0bd28e1373799d779  t1_1000m_forecast.npz
402e19c844493c8dde012fb2b4cd10870feaf6524f64057dca40a75c2d8cd73a  t1_5000m_bar.json
98e7479283c2f31864c3b411e6850eb59027263b678e36ee556de8b3e00e3707  t1_5000m_bar.npz
bd41e68ee3a27e8b1ffcd6124bf95f76dd10f0834b6e8e40669af59790e5b829  t1_1000m_cc_bar.json
019a08033cda5cc21ec3bf91b6a761893d58c78b0c09d96b2b12707833bb2562  t1_1000m_cc_bar.npz
```
