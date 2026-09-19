# T0 completion report: the planning pack landed on the site branch

**Date:** 2026-09-18
**Type:** completion report for docs/dispatch/2026-09-18-t0-repo-bootstrap.md, given to the owner in
chat that day and filed here by T0b (docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md).
**Base:** zynergy-site main at 0688e4d. Work on branch claude/forager-forecast-planning-pack:
b707cbe, 851b96d, c8e8ce3.
**Superseded in part by:** T0b, for the .gitignore and layout items. What landed stands.

---

## The short version

The owner asked for the pack to go into the zynergy-site repository so it would serve under
zynergy-labs.com/Forager/. The site repo was not checked out on the machine, so it was cloned to
~/Zynergy/zynergy-site and given the same git identity as the Forager checkout. The pack went in
unchanged, on a branch, and was verified on the Cloudflare Pages preview build. Nothing was merged
to main. The owner then chose a dedicated repo (D15), so the site branch was never merged and is
to be closed once T0b reports the pack safe in the new repo.

## Verify first, as answered

1. **Does the repo exist?** Yes: slayer8366/zynergy-site, default branch main, head 0688e4d, a
   static Cloudflare Pages site with two Pages Functions (README.md:1-4 of that repo).
2. **Existing convention for docs, decisions or dispatches?** None in zynergy-site: one directory
   per URL path holding an index.html, and a README that inventories every file. The neighbouring
   Forager repo has docs/audits/ with an index README, docs/qc/dispatches/, docs/adr/ and
   docs/plans/. The pack's internal layout was kept as exported, because the owner placed it in a
   repo where no docs convention exists to conflict with.
3. **Tooling.** None: no package manager files, no CI workflow, no linter, no licence, no
   .gitignore. A Cloudflare Pages check-run appears on each commit.
4. **"Python is the working language for T1 to T9."** The site repo points elsewhere: JavaScript
   Pages Functions on a static site. It cannot host GBIF pulls and model fitting. Stopped for the
   owner on where that code lives. Answered later by D15: a dedicated repo.

## What landed

| Commit | Change |
|---|---|
| b707cbe | The pack, content unchanged, at Forager/mushroom-forecast/ |
| 851b96d | Site README pointer, plus the pack's own session-log row and T0 status |
| c8e8ce3 | Site README note that Pages paths are case-sensitive |

All 17 files were checked byte-for-byte against the zip with diff -r and per-file sha256 before
committing. The sub-directory was named mushroom-forecast by subject rather than the zip's
planning-pack, so later reports for the same project would have a home.

## Verified on the preview build

- Each .md returned status 200, content type text/markdown, body identical to the committed file
  by sha256. Headless Firefox displayed it as plain text. Chrome behaviour was not checked.
- The atlas page served intact at the extensionless URL; Pages redirects the .html form to it
  with a 308. Its Google Fonts stylesheet is blocked by the site's Content-Security-Policy
  (functions/_middleware.js:22-24 in that repo), so it renders in fallback fonts. Inferred from
  the header text, not observed in a browser.
- Paths are case-sensitive: the lowercase form returned the holding page with status 200, the
  capitalised form returned the file. The site README already reserves lowercase /forager for a
  future app page, so the two differ only by case. Recorded in c8e8ce3.
- The bare directory URL showed the holding page, because no index exists there.

## Not done from T0, and why

- No .gitignore and no project layout proposal: the site repo cannot host the model work, so
  both belonged to whichever repo would. Taken up by T0b.
- The session-log row and T0 status were added only to the repo copy of the pack. The planning
  doc on claude.ai is named as the planning home, so the same row belongs there.
- No pull request was opened.

## Not checked

Chrome's handling of text/markdown. The atlas under a real browser with the CSP applied. Whether
the Pages project deploys production only from main (inferred from the check-run on main's head
and the README's description).
