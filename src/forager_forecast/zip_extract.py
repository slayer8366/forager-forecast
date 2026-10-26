"""Extracting the T6b sources' zips to where the runner reads them (dispatch 2026-10-26-pulls,
Part A steps 2 and 3, which had no code path: docs/audits/2026-10-25-t6b-rebuild-check/report.md).

The zips' member paths were never recorded, so nothing here assumes them. Each function reads the
zip's own listing, finds the members it needs by a rule that refuses anything but exactly one match,
records the listing, and checks every member against the CRC-32 the zip carries.
"""

import hashlib
import zipfile
import zlib
from pathlib import Path, PurePosixPath

from forager_forecast.pulls_queue import QueueStop

_CHUNK = 8 << 20


class ExtractError(RuntimeError):
    pass


def zip_listing(zip_path: Path) -> list[dict]:
    with zipfile.ZipFile(zip_path) as z:
        return [
            {
                "name": i.filename,
                "file_size": i.file_size,
                "compress_size": i.compress_size,
                "crc32": f"{i.CRC:08x}",
            }  # fmt: skip
            for i in z.infolist()
            if not i.is_dir()
        ]


def _parts(name: str) -> tuple[str, ...]:
    p = PurePosixPath(name)
    if p.is_absolute() or "\\" in name or ".." in p.parts or not p.parts:
        raise ExtractError(f"{name!r}: a member path that would escape the folder it goes into")
    return p.parts


def root_for_target(names: list[str], target: Path) -> tuple[str, Path]:
    """The one member whose whole path is the end of ``target``'s path, and the folder that the
    zip must be extracted into so that member lands at ``target``."""
    target = Path(target)
    t = target.parts
    hits = [n for n in names if len(PurePosixPath(n).parts) < len(t)
            and PurePosixPath(n).parts == t[-len(PurePosixPath(n).parts):]]  # fmt: skip
    if len(hits) != 1:
        raise ExtractError(f"{target}: {len(hits)} members end with the target's path ({hits[:5]})")
    return hits[0], Path(*t[: -len(PurePosixPath(hits[0]).parts)])


def _extract_one(z: zipfile.ZipFile, info: zipfile.ZipInfo, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    h = hashlib.sha256()
    written = 0
    try:
        with z.open(info) as src, partial.open("wb") as out:
            while block := src.read(_CHUNK):  # zipfile checks the CRC-32 at the member's end
                h.update(block)
                out.write(block)
                written += len(block)
    except (zipfile.BadZipFile, zlib.error, EOFError) as err:
        partial.unlink(missing_ok=True)
        raise ExtractError(f"{info.filename}: damaged in the zip ({err})") from err
    if written != info.file_size:
        partial.unlink(missing_ok=True)
        raise ExtractError(f"{info.filename}: {written} bytes, the zip says {info.file_size}")
    partial.rename(dest)
    return {"member": info.filename, "path": str(dest), "bytes": written,
            "crc32": f"{info.CRC:08x}", "crc32_ok": True, "sha256": h.hexdigest()}  # fmt: skip


def _check_stop(should_stop, need: int) -> None:
    reason = should_stop(need)
    if reason is not None:
        raise QueueStop(reason)


def extract_beside_target(zip_path: Path, target: Path, should_stop=lambda _n: None) -> dict:
    """Every file in the zip, under the folder that puts its ``target`` member at ``target``."""
    listing = zip_listing(zip_path)
    for m in listing:
        _parts(m["name"])
    member, root = root_for_target([m["name"] for m in listing], target)
    files = []
    with zipfile.ZipFile(zip_path) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        for n, info in enumerate(infos):
            _check_stop(should_stop, sum(i.file_size for i in infos[n:]))
            files.append(_extract_one(z, info, root.joinpath(*_parts(info.filename))))
    return {"zip": Path(zip_path).name, "target": str(target), "target_member": member,
            "root": str(root), "listing": listing, "files": files}  # fmt: skip


def extract_named(zip_path: Path, names: list[str], dest_dir: Path,
                  should_stop=lambda _n: None) -> dict:  # fmt: skip
    """Each member whose file name is one of ``names`` (exactly one each), flat in ``dest_dir``."""
    listing = zip_listing(zip_path)
    picks = {}
    for name in names:
        hits = [m["name"] for m in listing if PurePosixPath(m["name"]).name == name]
        if len(hits) != 1:
            raise ExtractError(f"{name}: {len(hits)} members have this file name ({hits[:5]})")
        _parts(hits[0])
        picks[name] = hits[0]
    files = []
    with zipfile.ZipFile(zip_path) as z:
        for n, name in enumerate(names):
            _check_stop(should_stop, sum(z.getinfo(picks[x]).file_size for x in names[n:]))
            files.append(_extract_one(z, z.getinfo(picks[name]), Path(dest_dir) / name))
    return {"zip": Path(zip_path).name, "dest_dir": str(dest_dir), "picked": picks,
            "listing": listing, "files": files}  # fmt: skip
