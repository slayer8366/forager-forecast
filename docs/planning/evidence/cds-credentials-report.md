# Completion report: Copernicus Climate Data Store account and API key

Written 2026-09-19 by Claude (Cowork session), in answer to the dispatch "create the Copernicus
Climate Data Store account and store its API key" (2026-09-18, against forager-forecast main at
ef6c82a, D24). Evidence labels: **observed** means I saw it myself, **owner-reported** means the owner
pasted the output into the chat, **unverified** means nobody checked.

## Outcome

The builders can pull from the store. An account exists, the CC-BY licence is accepted on all four D24
datasets, the key file is in place at mode 600 outside every repository, and one tiny retrieval
succeeded and was deleted.

## For the builder agents (this section is all they need)

- Key file: `~/.cdsapirc`. The `cdsapi` client reads it on its own. Never print, log, copy or commit it.
- Client: `cdsapi>=0.7.7` (observed on the store's API page and on PyPI, where 0.7.7 is the latest).
- Datasets, by catalogue id:
  - `reanalysis-era5-land` (ERA5-Land hourly data from 1950 to present)
  - `reanalysis-era5-single-levels` (ERA5 hourly data on single levels from 1940 to present)
  - `derived-era5-land-daily-statistics` (ERA5-Land post-processed daily statistics from 1950 to present)
  - `derived-era5-single-levels-daily-statistics` (ERA5 post-processed daily statistics on single levels from 1940 to present)
- Licence on all four: CC-BY. Attribution is required in anything that ships. The wording to use is
  under "Citation and attribution" on each dataset page. I did not copy it.
- A request shape known to work for `reanalysis-era5-land`: `variable` (list), `year`, `month`, `day`
  (list), `time` (list), `area` as `[north, west, south, east]`, `data_format: "netcdf"`,
  `download_format: "unarchived"`. The other three datasets have different forms, the daily-statistics
  ones especially. Build each request from that dataset's download form ("Show API request code"),
  not from this one.
- Keep the exact request next to anything pulled, so a pull can be repeated with a different key.
- The store queues requests. The proof took 24 seconds from accepted to successful for 25 KB.

## Evidence

| Item | Value | Label |
|---|---|---|
| Account | ECMWF account for Brandon Wann, `armyofwann@gmail.com` | observed on the store's profile page |
| Username | not shown to me. ECMWF login appears to be by email. | unverified |
| Key file | `-rw------- 1 zynergy-labs zynergy-labs 85 Sep 19 00:32 /home/zynergy-labs/.cdsapirc` | owner-reported |
| Key file shape | 85 bytes equals the two expected lines with a 36-character token | inferred from the size |
| Proof request | `reanalysis-era5-land`, 2m_temperature, 2024-01-01 12:00, box 45.5 to 45.6 N, 122.7 to 122.6 W | observed (script) |
| Proof result | Request ID `7f9dd849-5aad-422e-85b5-e39ede3c668f`, accepted 00:43:30, successful 00:43:54, `PROOF OK ... 25116 bytes downloaded`, `proof file deleted` | owner-reported |
| Negative control | same request with a fake key: `401 Unauthorized ... Authentication failed`, nothing downloaded | observed, three times |
| Terms accepted | "Accepted" shown on all four download forms | observed |
| Token in any chat, log or command | none. The owner pasted it into a no-echo prompt. I never opened the page that displays it. | observed for this session |
| Helper script | `~/Labs/cds-credentials.sh`, no secrets inside, not in a git repo | observed |

## Verify-first findings

- `~/.cdsapirc` is two lines: `url: https://cds.climate.copernicus.eu/api` and `key: <token>`. Observed on
  the store's API page and PyPI. The planning chat's memory was right on all three points.
- Dataset terms must be accepted by hand at the bottom of each download form. Observed. The store records
  acceptance **per licence, not per dataset**: one click on ERA5-Land, and the other three already
  showed "Accepted".
- Licence field, read off each page, word for word: "CC-BY licence" on all four. The field names no
  version. On ERA5-Land I opened the pop-up: it links to `creativecommons.org/licenses/by/4.0/`, the 4.0
  legal code, and `spdx.org/licenses/CC-BY-4.0`. So 4.0 is observed on one dataset and inferred for the
  other three, which show the same label.
- Both daily-statistics datasets exist.

## What sign-up required

- **Observed:** after first login the store demands a profile activation: country, affiliation, thematic
  activities, activity sectors, a contact-consent choice, and acceptance of the data protection
  statement and the store's terms of use. Organisation is optional. A cookie dialog appears on first
  visit. I chose "Deny all".
- **Unverified:** the ECMWF registration form itself (fields, password rules, CAPTCHA). The owner did it
  and has not described it. What the owner entered on the profile form is also not recorded here.

## What differed from the dispatch

1. **Cowork did not register the account or handle the key.** My operating rules prohibit creating
   accounts and handling passwords or tokens in plain text. The owner registered, logged in, and pasted
   the token into a script prompt. No secret passed through any agent.
2. **Password:** chosen by the owner, not generated. Length and reuse unknown. No password manager entry
   was made by me.
3. **I clicked "Accept terms"** once, on ERA5-Land, after the owner wrote "I accept the terms and
   conditions" in the chat. The owner accepted the profile terms themselves.
4. **Client install:** the proof needed `cdsapi`, which was not on the machine. The script installed it
   into a private venv at `~/.cache/forager-forecast/cds-venv`, outside every repository. Builders
   should install `cdsapi` in their own environment and not rely on this one.
5. **Two script faults on the way**, both mine, both fixed and re-tested against a reproduced state: it
   trusted a venv's existence without checking for `cdsapi`, and it printed "proof file deleted" when
   nothing had been downloaded. Neither touched the key or reached the store.

## Correction to something I said in the chat

I told the owner the broken venv was probably caused by a missing `python3-venv` package, and that I
expected the rebuild to fail. It rebuilt on the first try, so that package was present and my
inference was wrong. The cause of the first broken venv is unknown. An interrupted first run is
possible. I have no evidence for it.

## Not checked

- Whether an ECMWF account already existed for the email before registration.
- The other three datasets through the API. Only `reanalysis-era5-land` was retrieved. Terms are
  accepted on all four, so authentication and licence should not block them, but no request to them has
  been tried.
- The content of the downloaded file. It was 25116 bytes and was deleted unopened, as the dispatch asked.
- The store's terms of use text and the CC BY 4.0 text. The owner states they accept them. I did not
  read them on the owner's behalf.
- Whether this account is a test account to be redone later, as the GBIF one is. Asked twice, not answered.
- Whether the browser saved the login. forager-forecast at ef6c82a, D24 and D34: no access.

## If the key ever changes

```
rm ~/.cdsapirc
cd ~/Labs
./cds-credentials.sh store     # paste the new token at the no-echo prompt
./cds-credentials.sh check     # expect PROOF OK
./cds-credentials.sh perms
```
