"""T7 part B: the road and trail sources for the access layer, and how each download is checked.

Dispatch 2026-10-17-T7B (Forager RECORD -1163, go in -1168). Sources, one file each:

- the USGS National Transportation Dataset, state file geodatabases for the eight states the PNW
  box touches (OR, WA, ID, MT, CA, NV, UT, WY; the last three added by the planner's go, -1168);
- the Forest Service's National Forest System roads (``Trans_RoadCore_FS``) and trails
  (``Trans_Trail_NFS_Publish``);
- the Bureau of Land Management's public managed trails (hub export, file geodatabase);
- the Forest Service's administrative forest boundaries, for the trails-not-published mask.

Checks (the planner's call in -1168): an NTD file is checked against its S3 ETag, which for these
objects is a multipart MD5 of 8 MiB parts (``"<md5 of the part md5s>-<parts>"``); every other file
against its served length. Every file's sha256 is recorded either way. Nothing here is a
publisher-stated checksum: the TNM catalogue's own ``sizeInBytes`` is about 4.6% larger than the
bytes served for every NTD file (verify report), so it cannot be used.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

ACCESS_ROOT = Path("/mnt/work/Zynergy/forecast-data/access")
RAW_DIR = ACCESS_ROOT / "raw"
PART_SIZE = 8 * 1024 * 1024

NTD_STATES = ("Oregon", "Washington", "Idaho", "Montana", "California", "Nevada", "Utah", "Wyoming")
NTD_URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Tran/GDB/TRAN_{state}_State_GDB.zip"
FS_ROADS_URL = "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/Trans_RoadCore_FS.gdb.zip"
FS_TRAILS_URL = (
    "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/Trans_Trail_NFS_Publish.gdb.zip"
)
# The mask for the forests whose trail records carry no lines (the owner's ruling 1, -1168).
FS_FORESTS_URL = (
    "https://data.fs.usda.gov/geodata/edw/edw_resources/fc/BdyAdm_LSRS_AdministrativeForest.gdb.zip"
)
BLM_TRAILS_URL = (
    "https://gbp-blm-egis.hub.arcgis.com/api/download/v1/items/"
    "974363b4f22244d49350753f8fb5af32/filegdb?layers=2"
)

# The map's credit line for the access layer (dispatch item 5): the USGS acknowledged as its
# metadata asks ("Acknowledgment of the U.S. Geological Survey would be appreciated"), the Forest
# Service's products under CC BY 4.0, BLM's trails public domain (DATA_REGISTER, D148). The same
# text is written into the layer's own ``attribution`` tag. Nothing is published by writing it.
ACCESS_ATTRIBUTION = (
    "Roads and trails: USGS National Transportation Dataset (acknowledgment of the U.S. "
    "Geological Survey); National Forest System Roads, National Forest System Trails and "
    "Administrative Forest Boundaries, USDA Forest Service, CC BY 4.0; BLM National GTLF Public "
    "Managed Trails, Bureau of Land Management, public domain."
)

CHECK_ETAG = "s3 multipart etag"
CHECK_LENGTH = "served length"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    check: str


def sources() -> tuple[Source, ...]:
    out = [Source(f"ntd_{s.lower()}", NTD_URL.format(state=s), CHECK_ETAG) for s in NTD_STATES]
    out += [
        Source("fs_roads", FS_ROADS_URL, CHECK_LENGTH),
        Source("fs_trails", FS_TRAILS_URL, CHECK_LENGTH),
        Source("blm_trails", BLM_TRAILS_URL, CHECK_LENGTH),
        Source("fs_admin_forests", FS_FORESTS_URL, CHECK_LENGTH),
    ]
    return tuple(out)


def multipart_etag(path: Path, part_size: int = PART_SIZE) -> str:
    """The S3 ETag of a multipart upload of ``path`` in parts of ``part_size`` bytes.

    One part gives ``md5-1``, as S3 does for a multipart upload of one part (a single-request
    upload's ETag is the plain MD5 instead, which ``etag_matches`` also accepts)."""
    digests = []
    with open(path, "rb") as f:
        while chunk := f.read(part_size):
            digests.append(hashlib.md5(chunk).digest())
    return f"{hashlib.md5(b''.join(digests)).hexdigest()}-{len(digests)}"


def plain_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def etag_matches(path: Path, etag: str) -> bool:
    etag = etag.strip().strip('"')
    if "-" in etag:
        parts = int(etag.rsplit("-", 1)[1])
        return multipart_etag(path) == etag and parts >= 1
    return plain_md5(path) == etag


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()
