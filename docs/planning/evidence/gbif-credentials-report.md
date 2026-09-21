# Completion report: GBIF account and credentials for the builder agents

Written 2026-09-18 by Claude (Cowork session), in answer to the dispatch "create the GBIF account
and store its credentials for the builder agents". Evidence labels: **observed** means I saw the
output myself, **owner-reported** means the owner pasted it into the chat, **unverified** means nobody
checked.

## Outcome

T1 and T2 are unblocked on credentials. A GBIF account exists, its credentials are stored outside
every repository, and an authenticated API request returned 200.

## For the builder agents (this section is all they need)

- Credentials file: `~/.config/forager-forecast/gbif.env`
- Variables: `GBIF_USER`, `GBIF_PWD`, `GBIF_EMAIL`. pygbif reads exactly these names (observed, pygbif docs).
- Load it by sourcing it in a shell (`set -a; . ~/.config/forager-forecast/gbif.env; set +a`) or with
  a dotenv parser. Do not split lines on `=` by hand, because the value may be quoted.
- Never print, log, copy or commit the contents. Reports name the path only.
- **This is a test account.** The business will use a new account later, and every download will be
  redone under it, not moved. So for each download:
  - keep the exact query (predicate JSON or pygbif arguments) next to the DOI, so the redo is the
    same request with different credentials;
  - mark the DOI as provisional, from the test account. After the redo, add the new DOI as a
    superseding entry and leave the old one in place;
  - do not pin exact record counts in tests. GBIF's index changes, so the redo may differ slightly.

## Evidence

| Item | Value | Label |
|---|---|---|
| Username | `b.wann` | owner-reported, from the check output |
| Email | not stated in the chat. It is in the file. | unverified by me |
| Login check | `GET https://api.gbif.org/v1/user/login as b.wann -> HTTP 200` | owner-reported |
| Negative control | same request with a made-up user returned HTTP 401 | observed |
| Folder | `drwx------ zynergy-labs` `/home/zynergy-labs/.config/forager-forecast` | owner-reported |
| File | `-rw------- zynergy-labs` 70 bytes `gbif.env` | owner-reported |
| Password in any chat, log or command | none. The owner typed it into GBIF's form and into a no-echo prompt. | observed for this session |
| Helper script | `~/Labs/gbif-credentials.sh`, no secrets inside, not in a git repo | observed |

## What differed from the dispatch

1. **Cowork did not create the account.** My operating rules prohibit creating accounts and handling
   passwords, and the owner's request does not override that. The owner registered. I supplied a
   script the owner ran, so no password passed through any agent. This is stronger than the
   dispatch's "treat it as low-value" fallback.
2. **Username is `b.wann`, not an organisation name.** Owner's decision: the owner is the
   organisation, and this is a test account. Closed.
3. **Password is under 24 characters** (inferred from the 70-byte file size) and was chosen by the
   owner, not generated. Accepted for a throwaway test account. The business account should use
   `./gbif-credentials.sh setup`, which generates 32 random characters.
4. **No password manager entry.** I did not check whether one is set up on the machine.

## What GBIF's sign-up required

- **Observed:** gbif.org put a Cloudflare "Verifying you are human" page in front of the built-in
  browser, and it did not clear. I did not try to get past it.
- **Unverified:** the registration form's fields, password rules, CAPTCHA and terms checkbox. I never
  saw the form, and the owner has not described it.

## Not checked

- Whether the owner read and accepted GBIF's terms and data user agreement. Assumed from registering.
- Whether an account already existed for the email before registration.
- Whether the password was saved in a browser's saved logins.
- Whether a download request succeeds. The dispatch forbade requesting one. A 200 on login shows the
  account authenticates. T1's first download is the first real evidence for downloads.
- Whether GBIF can transfer a download or DOI between accounts. Moot, since downloads will be redone.
- The forager-forecast repo at f96d557. I had no access to it.

## Moving to the business account later

```
rm ~/.config/forager-forecast/gbif.env
cd ~/Labs
./gbif-credentials.sh setup <business username> <business email>
./gbif-credentials.sh copy     # paste into GBIF's sign-up form, then clear the clipboard
./gbif-credentials.sh check    # expect HTTP 200 after the verification link is clicked
./gbif-credentials.sh perms
```

Nothing in the repo or the worktrees changes on that day.
