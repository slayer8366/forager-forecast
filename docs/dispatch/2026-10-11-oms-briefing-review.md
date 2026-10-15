# Dispatch: an independent read of the OMS briefing before the owner reads it

Written by the planner (Rowan Waymark), 2026-10-11, on the owner's "Yes please check it". The briefing is docs/briefings/2026-10-12-oms-briefing.md on pnw-pilot-plans at 9526ea4 (verify that). The owner takes it into a meeting on Monday 2026-10-12 with a mycologist. You did not write it. Read it as a demanding outsider would.

Writing rule for everything you write: describe other products, services and device makers generically or by what they do.

## Check

1. **Accuracy.** Trace every figure and claim to its cited source, and re-derive what you can cheaply:
   - review pass 2: pnw-pilot-t1-review 79b8b17;
   - the builder's report: pnw-pilot-t1 f73b800;
   - ~/Zynergy/forecast-data-pnw-pilot/fits/*_comparison.json;
   - Forager RECORD.md on records-after-173 (worktree ~/.cache/forager-wt/records).
   Flag any figure quoted outside its scope: a figure about one sample cited about another, a superseded number, a "never" or an "all" not checked against its sample (CLAUDE.md, "A derived figure carried across a boundary").
2. **Consistency.** Find any two passages that disagree, and any stale line left from before 2026-10-11.
3. **Usefulness in the room.** Can the owner find the headline result, what to say, and what not to say in under a minute? What's too long, repeated, or jargon a mycologist wouldn't follow? Is the honest result stated plainly, neither spun nor buried?
4. **Wording rules:** "sighting chance", never fruiting probability (D12); no forbidden terms (D58); products described generically.

## Output

Don't edit the briefing. Return a report as your final message, findings ranked most important first. For each: the line, what's wrong, the evidence (file and line), and a proposed fix in plain words. Say what you checked and what you couldn't. Commit the report as docs/audits/2026-10-11-oms-briefing-review.md on pnw-pilot-plans and push.
