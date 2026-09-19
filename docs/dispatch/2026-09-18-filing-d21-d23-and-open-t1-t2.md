# Filing dispatch: record rulings D21 to D23, amend T1, then hand back for the merge

## State this was written against

- Written 2026-09-18 by Claude in the planning chat. forager-forecast: main at c66a865, branch
  decisions-d14-d20 at 5e97aa0 holding rows D14 to D20, not merged. Agent-reported. Claude has not read
  the repo. The repo is private (owner, D22).
- This supersedes the earlier hand-off file 2026-09-18-decision-d21-ruling.md, which carried D21 only.
  If that file was already applied, say so under "Verify first" and add only what is missing.
- Established today by the owner: D19 and D20 accepted (D21), the repo is private and the license waits
  until release (D22), the zynergy-site branch stays open as a frozen copy (D23).
- Still open: the license, and whether the tool is commercial.

Scope: a documentation filing on the existing branch, then stop. This does not start T1 or T2.

## Verify first, and report before editing

1. The heads of main and decisions-d14-d20 now. Has any commit since 5e97aa0 touched DECISIONS.md,
   DATA_REGISTER.md or docs/dispatch/2026-09-18-t1-calendar-smoke-test.md? If yes, report and wait.
2. Is D21, or a second T1 amendment, already present from the earlier file?
3. That the newest row on the branch is D20 and that every row has the same number of fields.

## Then do

- Insert the three rows below directly under the DECISIONS.md table header, in the order given
  (D23, D22, D21), unchanged.
- Append "Amendment 2" below to the T1 dispatch, after the first amendment. Append, do not rewrite.
- File this dispatch where the repo's convention puts dispatches, add one audit index row, and say
  where you put it.
- Commit on decisions-d14-d20, push, and report. Do not merge and do not open a pull request unless
  the owner asks.

| D23 | 2026-09-18 | Owner's decision. The planning-pack branch in zynergy-site stays open and unmerged. It is a frozen copy that ends at D13 and is not a source for any agent. The record lives in forager-forecast. | Owner's words: "I'll leave it as it requires an address link nobody has." Nothing in the pack is secret. Claude's caveat, noted and not pressed: the preview address is built from the branch name, so it is guessable by anyone who can see the site repo's branches. | Delete the branch and its Pages preview (tidier, and consistent with a private forecast repo, but it gains little since nothing in the pack is sensitive). | Replaces one clause of D15, withdrawn wording: "the zynergy-site branch is closed without merging". |
| D22 | 2026-09-18 | Owner's statement. The forager-forecast repo is private. The license is not chosen yet and will be decided before release. Until then the repo carries no license file, and no data layer with non-commercial terms is ruled in or out. | Owner's words: "I have yet to figure a license but this is private, so I'll decide later before release. Forager-forecast is private." | Choose a license now (nothing is released, so nothing forces it yet). | Settles the visibility point left open in D17. The commercial-use question in the Spec stays open. |
| D21 | 2026-09-18 | Owner's ruling: yes to both. D19 is accepted: every Open-Meteo archive request pins models=era5_seamless, for training and for serving. Temperature and soil variables come from ERA5-Land at 0.1 degree, precipitation comes from ERA5 at 0.25 degree, and the endpoint default is never used. The T10 item about bridging the newest five days stays open. D20 is accepted: uv with PyPI wheels, no separate GDAL Python bindings, pixi with conda-forge as the recorded fallback, Python pinned at 3.14 with 3.12 as the fallback. T1 and T2 may start once this row is on main. | Owner's words: "Yes to both". | None raised by the owner. D19 and D20 list the alternatives that were considered. | Accepts D19 and D20. D7 is now read through D19. |

### Amendment 2 for the T1 dispatch

> Amendment 2, 2026-09-18. Follows rulings D19 and D21 and changes nothing else. "Verify first" item 2
> is settled for the product question: T0b showed that models=era5_land returns no precipitation, and
> the owner ruled that every request pins models=era5_seamless. Use that model name in every archive
> call and record it in the report. Do not use the endpoint default anywhere, including in tests.
> Rate limits and terms of use are still yours to check and report. Precipitation now arrives on a
> 0.25 degree grid while temperature and soil arrive at 0.1 degree. Keep the 0.1 degree cell as the unit
> and say in the report how many 0.1 degree cells share each rain value. Under D20, confirm the
> gradient-boosting library you choose has a wheel for the pinned Python before writing code, and report
> which library and version you used.

## Do not touch

- Any existing row, including D19 and D20. A ruling is a new row. It never edits the proposal it answers.
- Amendment 1 in the T1 dispatch, and everything else in that file.
- Any code, the Forager repo, the zynergy-site repo, and both Cloudflare accounts.

## Already considered and rejected

- One branch per ruling: three small merges for no gain. The rulings ride on the branch that holds
  the proposals, so main receives both together.
- Marking D19 and D20 as accepted in place: breaks the supersede rule.

## Evidence to return

- The commit hash, and a diff that shows only insertions in DECISIONS.md and an append in the T1 dispatch.
- The field-count check across all rows, and the large-file guard result.
- A Conventions line, and what you did not check.

## Owner only, after this reports

1. Merge decisions-d14-d20 into main.
2. Start T1 with docs/dispatch/2026-09-18-t1-calendar-smoke-test.md, both amendments included. Its
   "Verify first" report comes back before any modelling.
3. T2 may run alongside T1 and share the GBIF pull. Two sessions will both append to the audit index,
   which is the known conflict point, so each appends its row in its own commit and rebases.
4. After each report, a second agent runs the standing review protocol. A dependent task waits for it.
5. T3 can run at any time. The T2 photo hand check needs a person who knows chanterelles.
