"""Adopting a job the store already holds, so a restarted pull never submits the same request twice.

The store caps queued requests per user (observed 2026-10-10: "Number queued requests for this
dataset is temporarily limited"), so a duplicate costs a slot and a queue position. Before
submitting, `fetch` looks for a job of this account with the same dataset and the same request
(compared after normalising every value to text) that is accepted, running or successful, and
downloads that job's result instead. Every adoption is reported by the caller.
"""

import json


def _norm(request: dict) -> str:
    out = {}
    for k, v in request.items():
        if isinstance(v, list | tuple):
            out[k] = sorted(str(float(x)) if isinstance(x, float) else str(x) for x in v)
        else:
            out[k] = str(v)
    return json.dumps(out, sort_keys=True)


def existing_job(client, dataset: str, request: dict) -> str | None:
    headers = {"PRIVATE-TOKEN": client.key}
    r = client.session.get(f"{client.url}/retrieve/v1/jobs?limit=100", headers=headers, timeout=60)
    r.raise_for_status()
    want = _norm(request)
    for job in r.json().get("jobs", []):
        if job.get("processID") != dataset:
            continue
        if job.get("status") not in ("accepted", "running", "successful"):
            continue
        d = client.session.get(
            f"{client.url}/retrieve/v1/jobs/{job['jobID']}?request=true",
            headers=headers,
            timeout=60,
        )
        d.raise_for_status()
        ids = d.json().get("metadata", {}).get("request", {}).get("ids", {})
        if _norm(ids) == want:
            return job["jobID"]
    return None


def fetch(client, dataset: str, request: dict, target: str) -> str | None:
    """Download the request's result to target. Returns the adopted job id, or None if a new job
    was submitted."""
    job = existing_job(client, dataset, request)
    if job:
        client.client.get_remote(job).download(target)
        return job
    client.retrieve(dataset, request).download(target)
    return None
