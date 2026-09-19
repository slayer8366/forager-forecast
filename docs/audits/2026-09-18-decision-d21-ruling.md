# Ruling row D21, plus a second T1 amendment

Written 2026-09-18 by Claude against forager-forecast branch decisions-d14-d20 at 5e97aa0 (agent-reported,
not read by Claude). Apply on that same branch so main receives the proposals and the ruling together.

1. Insert the row below directly under the DECISIONS.md table header, above D20, unchanged.
2. Append the amendment below to docs/dispatch/2026-09-18-t1-calendar-smoke-test.md, after the first
   amendment. Append, do not rewrite.
3. File this document in docs/audits/ as received and add one index row.
4. Report the commit. Merging to main is the owner's call. T1 and T2 start only after that merge.

| D21 | 2026-09-18 | Owner's ruling: yes to both. D19 is accepted: every Open-Meteo archive request pins models=era5_seamless, for training and for serving. Temperature and soil variables come from ERA5-Land at 0.1 degree, precipitation comes from ERA5 at 0.25 degree, and the endpoint default is never used. The T10 item about bridging the newest five days stays open. D20 is accepted: uv with PyPI wheels, no separate GDAL Python bindings, pixi with conda-forge as the recorded fallback, Python pinned at 3.14 with 3.12 as the fallback. T1 and T2 may start once this row is on main. | Owner's words: "Yes to both". | None raised by the owner. D19 and D20 list the alternatives that were considered. | Accepts D19 and D20. D7 is now read through D19. |

### Amendment text for the T1 dispatch

> Amendment 2, 2026-09-18. Follows rulings D19 and D21 and changes nothing else. "Verify first" item 2
> is settled for the product question: T0b showed that models=era5_land returns no precipitation, and
> the owner ruled that every request pins models=era5_seamless. Use that model name in every archive
> call and record it in the report. Do not use the endpoint default anywhere, including in tests.
> Rate limits and terms of use are still yours to check and report. Precipitation now arrives on a
> 0.25 degree grid while temperature and soil arrive at 0.1 degree. Keep the 0.1 degree cell as the unit
> and say in the report how many 0.1 degree cells share each rain value. Under D20, confirm the
> gradient-boosting library you choose has a wheel for the pinned Python before writing code, and report
> which library and version you used.
