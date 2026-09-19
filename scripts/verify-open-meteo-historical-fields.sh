#!/usr/bin/env bash
#
# T0b-era record, kept unchanged under D30 (DECISIONS.md, 2026-09-18). This script is the
# reproducible evidence behind D19: it sends the endpoint default (sections 1 to 3) and
# models=era5_land (section 4) on purpose, which is how the null-precipitation finding was made.
# Under D21 those requests are not made by any data path, feature, test or CI step, so this
# script is never run as a check and is not wired anywhere. Live checks use the separate script
# pinned to models=era5_seamless and the D25 parameters. Only this header was added; the body
# below is as T0b left it.
# Copied, not imported, from the Forager repo: scripts/verify-open-meteo-historical-fields.sh at
# commit 175b050a0a507afb74686285c87fb36f72b9b548 (Forager origin/main, 2026-09-12), per T0b
# (docs/dispatch/2026-09-18-t0b-forecast-repo-bootstrap.md).
#
# What changed from the original: sections 4 and 5 at the end are new. Section 4 requests the four
# variables T1 needs (docs/dispatch/2026-09-18-t1-calendar-smoke-test.md, "Verify first" item 2)
# at one point inside each T1 box, from the ERA5-Land model explicitly (models=era5_land, D7).
# Section 5 was added the same day, after section 4 first ran and found precipitation null under
# era5_land: it requests the same variables under each model setting so the products can be told
# apart. Sections 1 to 3 and the retry loop are the original, unchanged; their comments name
# Forager classes (OpenMeteoHistoricalWeatherProvider, GetSeasonalPatternUseCase) and describe
# that app. Note that sections 1 to 3 send no models= parameter, so they exercise Open-Meteo's
# default best_match product, which section 5 shows is not ERA5-Land.
#
# Verifies against the live Open-Meteo historical archive API that the fields the seasonal
# fruiting-lag visualizer relies on actually exist and actually return data.
#
# Follows scripts/verify-open-meteo-fields.sh's shape, for the archive endpoint instead of the
# forecast one. A prior session concluded this endpoint was blocked by an organization network
# policy and shipped no verification at all. That was a misread of a *rate limit* as a policy
# denial: archive-api.open-meteo.com returns HTTP 429 ("Daily API request limit exceeded") on a
# shared egress IP under load, not a connection failure, and a later attempt with backoff got
# through. This script backs off and retries on 429 rather than concluding the host is
# unreachable — see the retry loop below.
#
# What this checks, and why each one matters:
#
#   1. The request actually returns data for the parameters
#      OpenMeteoHistoricalWeatherProvider sends: latitude, longitude, start_date, end_date,
#      daily=precipitation_sum, timezone=auto. Unlike the forecast endpoint, the archive one
#      takes an explicit date range rather than past_days/forecast_days.
#
#   2. The response shape matches what HistoricalPrecipitationResponseDto expects:
#      utc_offset_seconds, daily.time, daily.precipitation_sum.
#
#   3. A single request can span years, not just days — GetSeasonalPatternUseCase fetches one
#      request per search covering the full range from the earliest sighting (padded backward by
#      FruitingPatternAssumptions.FRUITING_LAG_DAYS.last) through the latest, which for a species
#      with sightings spread across many years can be a multi-year window. If the API silently
#      truncated a long span, the provider would need to chunk requests — a capability it does
#      not have and does not silently pretend to.
#
# What this script could NOT establish, the last time it was run (2026-08-17): whether the most
# recent few days before "today" are populated or come back null — every attempt to check that
# specific case hit the same daily rate limit before a request got through. This is not assumed
# either way: OpenMeteoHistoricalWeatherProvider treats a missing/null precipitation value on any
# day the same way OpenMeteoWeatherProvider already does for the forecast endpoint — the day is
# dropped from the series rather than defaulted to zero, so an unpopulated recent day degrades to
# "not counted" rather than reading as "confirmed dry."
set -euo pipefail

API="https://archive-api.open-meteo.com/v1/archive"
DAILY="precipitation_sum"

# Rate-limit backoff. The observed failure mode is HTTP 429 with
# {"error":true,"reason":"Daily API request limit exceeded..."} — a shared-IP throttle, not a
# policy block (curl exits 0 with a normal HTTP response either way). A curl-level failure
# (timeout, DNS, refused) is a different, genuine unreachability signal and is not retried the
# same way; it is reported once and treated as a real failure.
MAX_ATTEMPTS=6
BACKOFF_SECONDS=8

fail=0

# Fetches $1, retrying on the rate-limit response body. Writes the response body to stdout on
# success. On exhausted retries or a curl-level failure, writes an {"error":true} sentinel so
# callers can detect it the same way scripts/verify-open-meteo-fields.sh does, and prints what
# was actually observed rather than silently giving up.
fetch_with_backoff() {
  local url="$1" attempt body
  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    if body=$(curl -sS --max-time 45 "$url" 2>/dev/null); then
      if printf '%s' "$body" | grep -q '"error":true'; then
        printf '  attempt %d/%d: rate-limited (%s), backing off %ds\n' \
          "$attempt" "$MAX_ATTEMPTS" "$(printf '%s' "$body" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("reason","?"))' 2>/dev/null || echo '?')" \
          "$BACKOFF_SECONDS" >&2
        sleep "$BACKOFF_SECONDS"
        continue
      fi
      printf '%s' "$body"
      return 0
    fi
    printf '  attempt %d/%d: curl failed (network/timeout, not a rate limit)\n' "$attempt" "$MAX_ATTEMPTS" >&2
    sleep "$BACKOFF_SECONDS"
  done
  echo '{"error":true,"reason":"exhausted retries"}'
  return 1
}

# --- 1 & 2. field names and response shape, at one location ---------------------------------
printf '%s\n' "--- request shape and response fields (10-day window) ---"
short_url="$API?latitude=45.5&longitude=-122.6&start_date=2024-01-01&end_date=2024-01-10&daily=$DAILY&timezone=auto"
short_body=$(fetch_with_backoff "$short_url") || fail=1
printf '%s' "$short_body" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if d.get("error"):
    print("  FAILED: could not reach the archive API:", d.get("reason"))
    sys.exit(1)

problems = []
for field in ("utc_offset_seconds", "timezone", "daily"):
    if field not in d:
        problems.append("top-level %s missing" % field)
daily = d.get("daily", {})
for field in ("time", "precipitation_sum"):
    if field not in daily:
        problems.append("daily.%s missing" % field)

print("  utc_offset_seconds=%s timezone=%s" % (d.get("utc_offset_seconds"), d.get("timezone")))
time = daily.get("time", [])
precip = daily.get("precipitation_sum", [])
print("  daily window: %d days, %s -> %s" % (len(time), time[0] if time else "?", time[-1] if time else "?"))
print("  precipitation_sum: %d entries, %d non-null" % (len(precip), sum(1 for v in precip if v is not None)))
if len(time) != 10 or len(precip) != 10:
    problems.append("expected 10 days for a 10-day start_date/end_date span, got %d/%d" % (len(time), len(precip)))

if problems:
    print("  FAILED: " + "; ".join(problems))
    sys.exit(1)
print("  OK")
' || fail=1

# --- 3. a multi-year span in one request -----------------------------------------------------
printf '\n%s\n' "--- a single request spanning several years (2016-01-01 to 2024-12-31, 3288 days) ---"
long_url="$API?latitude=45.5&longitude=-122.6&start_date=2016-01-01&end_date=2024-12-31&daily=$DAILY&timezone=auto"
long_body=$(fetch_with_backoff "$long_url") || fail=1
printf '%s' "$long_body" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if d.get("error"):
    print("  FAILED: could not reach the archive API:", d.get("reason"))
    sys.exit(1)

daily = d.get("daily", {})
time = daily.get("time", [])
precip = daily.get("precipitation_sum", [])
expected_days = 3288  # 2016-01-01 .. 2024-12-31 inclusive, across three leap years
non_null = sum(1 for v in precip if v is not None)
print("  %d days returned (expected %d), %s -> %s" % (len(time), expected_days, time[0] if time else "?", time[-1] if time else "?"))
print("  %d/%d non-null" % (non_null, len(precip)))

problems = []
if len(time) != expected_days:
    problems.append("expected %d days, got %d — the endpoint may cap or paginate a long span" % (expected_days, len(time)))
if non_null != len(precip):
    problems.append("some days in a fully-historical span came back null")
if problems:
    print("  FAILED: " + "; ".join(problems))
    sys.exit(1)
print("  OK: one request served the full multi-year span with no truncation and no gaps")
' || fail=1

printf '\n'
if [ "$fail" -eq 0 ]; then
  echo "All Open-Meteo historical-archive field checks passed."
else
  echo "One or more Open-Meteo historical-archive field checks failed or could not complete (see above)."
fi

# --- 4. the four T1 variables at one point inside each T1 box (added by T0b) ----------------
# T1 needs, from the ERA5-Land archive: daily mean temperature, daily precipitation, soil
# temperature 0 to 7 cm and soil moisture 0 to 7 cm. Soil variables are hourly-only on Open-Meteo
# (the same holds on the forecast endpoint, see Forager's scripts/verify-open-meteo-fields.sh), so
# the daily pair goes in daily= and the soil pair in hourly=. models=era5_land pins the product
# D7 fixed, rather than Open-Meteo's default blend. Boxes, from the T1 dispatch:
#   Pacific Northwest 42.0 to 49.5 N, 125.0 to 121.0 W  ->  point 47.0 N, 123.0 W
#   East              38.0 to 46.0 N,  84.0 to  70.0 W  ->  point 42.0 N,  77.0 W
# Finding, 2026-09-18: under models=era5_land, temperature and both soil variables are fully
# populated, and daily and hourly precipitation are null at every step, in both boxes, in a
# September and a January window. This section therefore fails on precipitation until the
# owner decides the product (D7). Section 5 shows where precipitation is served.
T1_DAILY="temperature_2m_mean,precipitation_sum"
T1_HOURLY="soil_temperature_0_to_7cm,soil_moisture_0_to_7cm"
for point in "pnw 47.0 -123.0" "east 42.0 -77.0"; do
  set -- $point
  name="$1"; lat="$2"; lon="$3"
  printf '\n%s\n' "--- T1 variables, $name box point ($lat, $lon), ERA5-Land, 2024-09-01 to 2024-09-10 ---"
  t1_url="$API?latitude=$lat&longitude=$lon&start_date=2024-09-01&end_date=2024-09-10&daily=$T1_DAILY&hourly=$T1_HOURLY&models=era5_land&timezone=auto"
  t1_body=$(fetch_with_backoff "$t1_url") || fail=1
  printf '%s' "$t1_body" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if d.get("error"):
    print("  FAILED: could not reach the archive API:", d.get("reason"))
    sys.exit(1)
problems = []
def report(block, field, expected_n):
    vals = d.get(block, {}).get(field)
    unit = d.get(block + "_units", {}).get(field, "?")
    if vals is None:
        problems.append("%s.%s missing from the response" % (block, field))
        print("  %s.%s: MISSING" % (block, field))
        return
    nn = [v for v in vals if v is not None]
    lo = min(nn) if nn else "?"
    hi = max(nn) if nn else "?"
    print("  %s.%s: %d values, %d non-null, unit %s, range %s to %s" % (block, field, len(vals), len(nn), unit, lo, hi))
    if len(vals) != expected_n:
        problems.append("%s.%s: expected %d values, got %d" % (block, field, expected_n, len(vals)))
    if len(nn) != len(vals):
        problems.append("%s.%s: %d null value(s)" % (block, field, len(vals) - len(nn)))
print("  grid elevation=%s m, timezone=%s, utc_offset_seconds=%s" % (d.get("elevation"), d.get("timezone"), d.get("utc_offset_seconds")))
for f in ("temperature_2m_mean", "precipitation_sum"):
    report("daily", f, 10)
for f in ("soil_temperature_0_to_7cm", "soil_moisture_0_to_7cm"):
    report("hourly", f, 240)
if problems:
    print("  FAILED: " + "; ".join(problems))
    sys.exit(1)
print("  OK: all four T1 variables present and fully populated at this point")
' || fail=1
done

# --- 5. the T1 variables by model, so the products can be told apart (added by T0b) ---------
# Same request as section 4, PNW point only, under each model setting the archive API offers for
# this region. Prints non-null counts and the period sum per variable. What T0b observed:
#   era5_land      temperature and soil served; precipitation absent, every value null
#   era5           everything served, on ERA5's coarser grid, so different values
#   era5_seamless  temperature and soil identical to era5_land, precipitation identical to era5
#   best_match     a third set of values, Open-Meteo's default when models= is omitted
# So "ERA5-Land" on this API means models=era5_seamless once precipitation is needed, with the
# precipitation then coming from ERA5. This section reports and does not pass or fail: which
# product T1 trains on is the owner's decision (D7, "thresholds belong to their product").
printf '\n%s\n' "--- T1 variables by model, PNW point (47.0, -123.0), 2024-09-01 to 2024-09-10 ---"
for model in era5_land era5 era5_seamless best_match; do
  m_url="$API?latitude=47.0&longitude=-123.0&start_date=2024-09-01&end_date=2024-09-10&daily=$T1_DAILY&hourly=$T1_HOURLY&models=$model&timezone=auto"
  m_body=$(fetch_with_backoff "$m_url") || true
  printf '%s' "$m_body" | python3 -c '
import json, sys
model = sys.argv[1]
d = json.load(sys.stdin)
if d.get("error"):
    print("  %-14s could not fetch: %s" % (model, d.get("reason")))
    sys.exit()
parts = []
for block in ("daily", "hourly"):
    for k, v in d.get(block, {}).items():
        if k == "time":
            continue
        nn = [x for x in v if x is not None]
        parts.append("%s %d/%d sum=%s" % (k, len(nn), len(v), round(sum(nn), 1) if nn else "-"))
print("  %-14s %s" % (model, "; ".join(parts)))
' "$model"
  sleep 1
done

printf '\n'
if [ "$fail" -eq 0 ]; then
  echo "All Open-Meteo historical-archive checks passed, including the four T1 variables in both boxes."
else
  echo "One or more Open-Meteo historical-archive checks failed or could not complete (see above)."
fi
exit "$fail"
