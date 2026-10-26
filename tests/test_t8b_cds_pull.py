"""T8b's ERA5-Land pull: the 135 monthly requests, job adoption, the store's size and MD5 check, and
the queue's stops. A fake store stands in for the network."""

import hashlib
import io
import json

import pytest

from forager_forecast.t8b import cds_pull as cp
from forager_forecast.t8b import design

GIB = 1024**3


def test_the_months_run_from_2014_10_to_2025_12():
    m = cp.months()
    assert len(m) == 135 and m[0] == (2014, 10) and m[-1] == (2025, 12)
    assert len(set(m)) == 135
    # B-pull-start, ruled by D160 (4): "pull Daymet and ERA5-Land from 2014-10-01".
    assert design.RULED["B-pull-start"] == "D160 (4)"


def test_a_month_asks_for_the_four_fields_on_t1s_box_as_daily_utc_means():
    r = cp.request_for(2014, 10)
    assert r == {
        "variable": [
            "volumetric_soil_water_layer_2",
            "soil_temperature_level_2",
            "2m_temperature",
            "2m_dewpoint_temperature",
        ],
        "year": "2014",
        "month": "10",
        "day": [f"{d:02d}" for d in range(1, 32)],
        "daily_statistic": "daily_mean",
        "time_zone": "utc+00:00",
        "frequency": "1_hourly",
        "area": [49.5, -125.0, 42.0, -121.0],
    }
    # The four long names are the ones the readers refuse to go without (design.ERA5_LAND_SHORT).
    assert set(r["variable"]) == set(design.ERA5_LAND_SHORT.values())


def test_the_key_is_read_from_cdsapirc(tmp_path):
    rc = tmp_path / ".cdsapirc"
    rc.write_text("url: https://cds.example/api\nkey: abc-123\n")
    assert cp.read_cdsapirc(rc) == ("https://cds.example/api", "abc-123")


def test_the_stops_pause_and_space(tmp_path):
    assert cp.stop_reason(tmp_path, 0, free_bytes=lambda _: 30 * GIB) is None
    assert "free" in cp.stop_reason(tmp_path, 11 * GIB, free_bytes=lambda _: 30 * GIB)
    (tmp_path / "PAUSE").touch()
    assert "PAUSE" in cp.stop_reason(tmp_path, 0, free_bytes=lambda _: 30 * GIB)


@pytest.mark.parametrize(
    ("status", "text", "kind"),
    [
        (401, "Authentication failed", cp.LoginWall),
        (403, "required licences not accepted: licence-to-use-copernicus-products", cp.QueueStop),
        (400, "invalid request", None),
        (202, "", None),
    ],
)
def test_a_refusal_is_classed_as_login_licence_or_neither(status, text, kind):
    got = cp.classify_refusal(status, text)
    assert (got is None) if kind is None else isinstance(got, kind)
    if status == 403:
        assert "licence" in str(got) and not isinstance(got, cp.LoginWall)


def test_requests_compare_after_every_value_is_made_text():
    a = cp.request_for(2015, 1)
    b = json.loads(json.dumps(a))
    b["area"] = ["49.5", "-125.0", "42.0", "-121.0"]
    b["variable"] = list(reversed(b["variable"]))
    assert cp.same_request(a, b)
    assert not cp.same_request(a, cp.request_for(2015, 2))


class Store:
    """A fake store: one account's jobs, their requests, statuses and results."""

    def __init__(
        self, body=b"netcdf" * 1000, md5=None, size=None, statuses=("running", "successful")
    ):
        self.body = body
        self.asset = {
            "href": "https://cds.example/download/x.nc",
            "file:size": len(body) if size is None else size,
            "file:checksum": md5 or hashlib.md5(body).hexdigest(),
        }
        self.jobs_list, self.requests, self.submitted = [], {}, []
        self.statuses = list(statuses)

    def jobs(self):
        return self.jobs_list

    def job_request(self, job):
        return self.requests[job]

    def submit(self, dataset, request):
        job = f"job-{len(self.submitted) + 1}"
        self.submitted.append((dataset, request))
        self.requests[job] = request
        self.jobs_list.append({"jobID": job, "processID": dataset, "status": "accepted"})
        return job

    def status(self, job):
        status = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        for j in self.jobs_list:  # the store's job list shows each job's own state
            if j["jobID"] == job:
                j["status"] = status
        return status

    def results(self, job):
        return {"asset": {"value": dict(self.asset)}}


class Body(io.BytesIO):
    status = 200
    headers = {}


def opener_for(store):
    return lambda href: Body(store.body)


def test_a_job_already_held_by_the_store_is_adopted_not_resubmitted():
    s = Store()
    r = cp.request_for(2016, 3)
    s.jobs_list.append({"jobID": "old", "processID": cp.DATASET, "status": "running"})
    s.requests["old"] = json.loads(json.dumps(r))
    assert cp.submit_or_adopt(s, r) == ("old", True)
    assert s.submitted == []
    s.jobs_list[0]["status"] = "failed"
    assert cp.submit_or_adopt(s, r) == ("job-1", False)


def test_a_failed_job_raises_and_a_successful_one_gives_its_asset():
    s = Store(statuses=("accepted", "running", "successful"))
    slept = []
    asset = cp.wait_for_asset(s, "j", sleep=slept.append, poll=(1, 4))
    assert asset["file:checksum"] == hashlib.md5(s.body).hexdigest()
    assert slept and max(slept) <= 4
    with pytest.raises(cp.JobFailed, match="failed"):
        cp.wait_for_asset(Store(statuses=("failed",)), "j", sleep=lambda s: None)


def test_a_month_is_downloaded_checked_and_recorded(tmp_path):
    s = Store()
    rec = cp.pull_month(s, opener_for(s), 2014, 10, tmp_path, tmp_path, log=lambda m: None,
                        sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip
    nc = tmp_path / "era5land-2014-10.nc"
    assert nc.read_bytes() == s.body
    on_disk = json.loads((tmp_path / "era5land-2014-10.request.json").read_text())
    assert on_disk == rec
    assert rec["store_file_checksum"] == rec["md5"] == hashlib.md5(s.body).hexdigest()
    assert rec["store_file_size"] == rec["bytes"] == len(s.body)
    assert rec["sha256"] == hashlib.sha256(s.body).hexdigest()
    assert rec["request"] == cp.request_for(2014, 10) and rec["dataset"] == cp.DATASET
    assert rec["job"] == "job-1" and rec["adopted"] is False
    # Run again: the file's MD5 matches its record, so nothing is asked of the store.
    s2 = Store()
    assert cp.pull_month(s2, opener_for(s2), 2014, 10, tmp_path, tmp_path, log=lambda m: None,
                         sleep=lambda x: None, free_bytes=lambda _: 100 * GIB) is None  # fmt: skip
    assert s2.submitted == []


def test_an_md5_off_the_stores_stops_the_queue_and_sets_the_file_aside(tmp_path):
    s = Store(md5="0" * 32)
    with pytest.raises(cp.ChecksumMismatch, match="MD5"):
        cp.pull_month(s, opener_for(s), 2015, 1, tmp_path, tmp_path, log=lambda m: None,
                      sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip
    assert not (tmp_path / "era5land-2015-01.nc").exists()
    assert (tmp_path / "era5land-2015-01.nc.mismatch").exists()
    assert not (tmp_path / "era5land-2015-01.request.json").exists()


def test_a_size_off_the_stores_stops_the_queue(tmp_path):
    s = Store(size=5)
    with pytest.raises(cp.ChecksumMismatch, match="bytes"):
        cp.pull_month(s, opener_for(s), 2015, 1, tmp_path, tmp_path, log=lambda m: None,
                      sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip


def test_a_stale_partial_or_unrecorded_file_is_fetched_again(tmp_path):
    s = Store()
    (tmp_path / "era5land-2015-01.nc").write_bytes(b"old")
    (tmp_path / "era5land-2015-01.nc.part").write_bytes(b"half")
    cp.pull_month(s, opener_for(s), 2015, 1, tmp_path, tmp_path, log=lambda m: None,
                  sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip
    assert (tmp_path / "era5land-2015-01.nc").read_bytes() == s.body
    assert not (tmp_path / "era5land-2015-01.nc.part").exists()


def test_a_failed_job_is_retried_then_stops(tmp_path):
    s = Store(statuses=("failed",))
    with pytest.raises(cp.QueueStop, match="3 attempts"):
        cp.pull_month(s, opener_for(s), 2015, 1, tmp_path, tmp_path, log=lambda m: None,
                      sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip
    assert len(s.submitted) == 3


def test_a_pause_stops_before_any_request(tmp_path):
    (tmp_path / "PAUSE").touch()
    s = Store()
    with pytest.raises(cp.QueueStop, match="PAUSE"):
        cp.pull_month(s, opener_for(s), 2015, 1, tmp_path, tmp_path, log=lambda m: None,
                      sleep=lambda x: None, free_bytes=lambda _: 100 * GIB)  # fmt: skip
    assert s.submitted == []
