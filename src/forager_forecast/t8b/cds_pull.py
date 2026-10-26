"""T8b's ERA5-Land pull from the Climate Data Store, by the daily-statistics route.

Dispatch 2026-10-26-pulls, Part B item 3; D159 (2); B-pull-start, ruled by D160 (4): from
2014-10-01.

One request per month, because the daily-statistics form takes ``month`` as one value (as
scripts/pnw_cds_pull.py found): 2014-10 to 2025-12, 135 months, four variables, T1's box. Each
delivery is checked against the ``file:size`` and ``file:checksum`` (MD5) the store states for its
job's result (as docs/planning/DATA_REGISTER.md's 2026-W42 row did), and a mismatch stops the queue.
The store is reached with the key in ``~/.cdsapirc``, as the earlier pulls were.
"""

import hashlib
import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

FORECAST_DATA = Path("/run/media/zynergy-labs/forager-storage/forecast-data")
OUT = FORECAST_DATA / "t8b" / "era5land"
DATASET = "derived-era5-land-daily-statistics"
VARIABLES = [
    "volumetric_soil_water_layer_2",
    "soil_temperature_level_2",
    "2m_temperature",
    "2m_dewpoint_temperature",
]
AREA = [49.5, -125.0, 42.0, -121.0]
MIN_FREE = 20 * 1024**3


class QueueStop(RuntimeError):
    """The queue must stop; the message is the reason it logs."""


class ChecksumMismatch(QueueStop):
    pass


class LoginWall(QueueStop):
    pass


class JobFailed(RuntimeError):
    pass


LICENCE_WORDS = ("licence", "license", "terms")
ACCOUNT = (
    "the CDS test account (D43): the ECMWF login recorded at "
    "docs/planning/evidence/cds-credentials-report.md:37; key read from ~/.cdsapirc, not recorded"
)
DISPATCH = "docs/dispatch/2026-10-26-pulls.md, Part B item 3"
_CHUNK = 8 << 20


def months() -> list[tuple[int, int]]:
    return [(2014, m) for m in range(10, 13)] + [
        (y, m) for y in range(2015, 2026) for m in range(1, 13)
    ]


def request_for(year: int, month: int) -> dict:
    return {
        "variable": list(VARIABLES),
        "year": str(year),
        "month": f"{month:02d}",
        "day": [f"{d:02d}" for d in range(1, 32)],
        "daily_statistic": "daily_mean",
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": list(AREA),
    }


def read_cdsapirc(path: Path) -> tuple[str, str]:
    fields = {}
    for line in Path(path).read_text().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields["url"], fields["key"]


def stop_reason(root: Path, need_bytes: int = 0, free_bytes=None) -> str | None:
    root = Path(root)
    if (root / "PAUSE").exists():
        return f"PAUSE file at {root / 'PAUSE'}"
    free = (free_bytes or (lambda r: shutil.disk_usage(r).free))(root)
    if free - need_bytes < MIN_FREE:
        return (f"{free} bytes free with {need_bytes} still to arrive would leave less than "
                f"{MIN_FREE} bytes free")  # fmt: skip
    return None


def classify_refusal(status: int, text: str) -> QueueStop | None:
    """A refusal that needs the owner: a login wall, or a licence or terms not accepted. The queue
    never accepts terms itself."""
    low = (text or "").lower()
    if status in (401, 403) or (400 <= status < 500 and any(w in low for w in LICENCE_WORDS)):
        if any(w in low for w in LICENCE_WORDS):
            return QueueStop(f"the store refused for a licence or terms reason (HTTP {status}): "
                             f"{text[:300]}; the owner must act")  # fmt: skip
        return LoginWall(f"the store refused the key (HTTP {status}): {text[:300]}")
    return None


def _text(x) -> str:
    """One value as text, numbers by their float value, so 49.5 and "49.5" compare equal."""
    try:
        return str(float(x))
    except TypeError, ValueError:
        return str(x)


def _norm(request: dict) -> str:
    out = {}
    for k, v in request.items():
        out[k] = sorted(_text(x) for x in v) if isinstance(v, list | tuple) else _text(v)
    return json.dumps(out, sort_keys=True)


def same_request(a: dict, b: dict) -> bool:
    return _norm(a) == _norm(b)


def submit_or_adopt(api, request: dict) -> tuple[str, bool]:
    """The job id for ``request``: an accepted, running or successful job of this account with the
    same request if there is one (adopted), else a new submission."""
    for job in api.jobs():
        if job.get("processID") != DATASET:
            continue
        if job.get("status") not in ("accepted", "running", "successful"):
            continue
        if same_request(api.job_request(job["jobID"]), request):
            return job["jobID"], True
    return api.submit(DATASET, request), False


def wait_for_asset(api, job: str, sleep, poll=(10, 120)) -> dict:
    wait = poll[0]
    while True:
        status = api.status(job)
        if status == "successful":
            return dict(api.results(job)["asset"]["value"])
        if status not in ("accepted", "running"):
            raise JobFailed(f"job {job}: {status}")
        sleep(wait)
        wait = min(wait * 1.5, poll[1])


def _hash_file(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with open(path, "rb") as f:
        while block := f.read(_CHUNK):
            h.update(block)
    return h.hexdigest()


def download_checked(opener, href: str, dest: Path, size: int, md5: str, should_stop) -> dict:
    dest = Path(dest)
    part = dest.with_name(dest.name + ".part")
    part.unlink(missing_ok=True)
    h5, h256, written = hashlib.md5(), hashlib.sha256(), 0
    try:
        response = opener(href)
        with response, part.open("wb") as out:
            while chunk := response.read(_CHUNK):
                h5.update(chunk)
                h256.update(chunk)
                out.write(chunk)
                written += len(chunk)
                reason = should_stop(max(size - written, 0))
                if reason:
                    raise QueueStop(f"{dest.name}: stopped at {written} bytes: {reason}")
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    if written != size or h5.hexdigest() != md5:
        part.rename(dest.with_name(dest.name + ".mismatch"))
        raise ChecksumMismatch(f"{dest.name}: {written} bytes, MD5 {h5.hexdigest()}; the store "
                               f"states {size} bytes, MD5 {md5}")  # fmt: skip
    part.rename(dest)
    return {"bytes": written, "md5": h5.hexdigest(), "sha256": h256.hexdigest()}


def pull_month(api, opener, year: int, month: int, out: Path, root: Path, log, sleep,
               free_bytes=None, attempts: int = 3) -> dict | None:  # fmt: skip
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"era5land-{year}-{month:02d}"
    nc, rec_path = out / f"{name}.nc", out / f"{name}.request.json"
    (out / f"{name}.nc.part").unlink(missing_ok=True)
    if nc.is_file() and rec_path.is_file():
        rec = json.loads(rec_path.read_text())
        if _hash_file(nc, "md5") == rec.get("store_file_checksum"):
            log(f"{name}: already here, MD5 matches the store's; skipped")
            return None
    reason = stop_reason(root, 0, free_bytes)
    if reason:
        raise QueueStop(f"before {name}: {reason}")
    request = request_for(year, month)
    errors = []
    for n in range(1, attempts + 1):
        requested_at = datetime.now(UTC).isoformat(timespec="seconds")
        t0 = time.monotonic()
        try:
            job, adopted = submit_or_adopt(api, request)
            log(f"{name}: job {job} ({'adopted' if adopted else 'submitted'}), attempt {n}")
            asset = wait_for_asset(api, job, sleep)
            size, md5 = int(asset["file:size"]), str(asset["file:checksum"])
            reason = stop_reason(root, size, free_bytes)
            if reason:
                raise QueueStop(f"before downloading {name}: {reason}")
            got = download_checked(opener, asset["href"], nc, size, md5,
                                   lambda still: stop_reason(root, still, free_bytes))  # fmt: skip
        except QueueStop:
            raise
        except (JobFailed, OSError) as err:
            errors.append(repr(err))
            log(f"{name}: attempt {n} failed: {err!r}")
            if n < attempts:
                sleep(60 * n)
            continue
        record = {
            "dataset": DATASET,
            "request": request,
            "requested_at_utc": requested_at,
            "seconds": round(time.monotonic() - t0, 1),
            "job": job,
            "adopted": adopted,
            "href": asset["href"],
            "store_file_size": size,
            "store_file_checksum": md5,
            "bytes": got["bytes"],
            "md5": got["md5"],
            "sha256": got["sha256"],
            "checksum_match": True,
            "account": ACCOUNT,
            "client": "forager_forecast.t8b.cds_pull (urllib, the store's retrieve API)",
            "attempts": n,
            "dispatch": DISPATCH,
            "rulings": ["D159 (2)", "D160 (4) B-pull-start"],
        }
        rec_path.write_text(json.dumps(record, indent=2) + "\n")
        log(f"{name}: verified, {got['bytes']} B, MD5 {md5} as the store states")
        return record
    raise QueueStop(f"{name}: no verified delivery after {attempts} attempts: {errors[-1]}")


class HttpApi:
    """The store's retrieve API over urllib, with the key from ~/.cdsapirc."""

    def __init__(self, url: str, key: str, timeout: int = 120) -> None:
        self.url, self.key, self.timeout = url.rstrip("/"), key, timeout

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        import urllib.error
        import urllib.request

        data = json.dumps(body).encode() if body is not None else None
        headers = {"PRIVATE-TOKEN": self.key, "User-Agent": "forager-forecast-pulls"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{self.url}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as err:
            text = err.read().decode("utf-8", "replace")
            stop = classify_refusal(err.code, text)
            if stop is not None:
                raise stop from err
            raise OSError(f"HTTP {err.code} for {method} {path}: {text[:300]}") from err

    def jobs(self) -> list[dict]:
        return self._call("GET", "/retrieve/v1/jobs?limit=100").get("jobs", [])

    def job_request(self, job: str) -> dict:
        reply = self._call("GET", f"/retrieve/v1/jobs/{job}?request=true")
        return reply.get("metadata", {}).get("request", {}).get("ids", {})

    def submit(self, dataset: str, request: dict) -> str:
        reply = self._call("POST", f"/retrieve/v1/processes/{dataset}/execution",
                           {"inputs": request})  # fmt: skip
        return reply["jobID"]

    def status(self, job: str) -> str:
        return self._call("GET", f"/retrieve/v1/jobs/{job}")["status"]

    def results(self, job: str) -> dict:
        return self._call("GET", f"/retrieve/v1/jobs/{job}/results")


def http_opener(href: str):
    import urllib.request

    req = urllib.request.Request(href, headers={"User-Agent": "forager-forecast-pulls"})
    return urllib.request.urlopen(req, timeout=300)
