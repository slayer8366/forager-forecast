"""T6b study-area mask (D111, D113) and which side a cell is on (D115), on synthetic shapefiles."""

import struct

import numpy as np
import pytest
from pyproj import Transformer

from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.t6b_mask import (
    CEC_LAEA,
    COUNTRY_CAN,
    COUNTRY_MEX,
    COUNTRY_NONE,
    COUNTRY_US48,
    COUNTRY_US_OTHER,
    ECO_ARCTIC,
    ECO_NONE,
    ECO_OTHER,
    SIDE_CA,
    SIDE_US,
    build_mask,
    cells_in_study,
    read_mask,
    read_shapefile,
)

_TO_LAEA = Transformer.from_crs("+proj=longlat +R=6370997 +no_defs", CEC_LAEA, always_xy=True)


def _ring(west, south, east, north, n=40):
    """A lon-lat box as a closed ring in the CEC sphere LAEA, clockwise as shapefiles want."""
    lon = np.concatenate(
        [
            np.full(n, west),
            np.linspace(west, east, n),
            np.full(n, east),
            np.linspace(east, west, n),
        ]
    )
    lat = np.concatenate(
        [
            np.linspace(south, north, n),
            np.full(n, north),
            np.linspace(north, south, n),
            np.full(n, south),
        ]
    )
    x, y = _TO_LAEA.transform(lon, lat)
    ring = np.column_stack([x, y])
    return np.vstack([ring, ring[:1]])


def _write_dbf(path, fields, rows):
    """dBase III with character fields only."""
    rlen = 1 + sum(size for _, size in fields)
    hlen = 32 + 32 * len(fields) + 1
    out = bytearray(struct.pack("<B3BIHH20x", 3, 126, 10, 7, len(rows), hlen, rlen))
    for name, size in fields:
        out += struct.pack("<11sc4xBB14x", name.encode(), b"C", size, 0)
    out += b"\r"
    for row in rows:
        out += b" " + b"".join(str(row[n]).encode().ljust(s) for n, s in fields)
    out += b"\x1a"
    path.write_bytes(bytes(out))


def _write_shapefile(stem, records, fields, rows):
    """Polygon shapefile (type 5); each record is a list of closed rings (N, 2)."""
    contents = []
    for rings in records:
        pts = np.vstack(rings)
        parts = np.cumsum([0] + [len(r) for r in rings[:-1]])
        body = struct.pack(
            "<i4d2i", 5, pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max(),
            len(rings), len(pts),
        )  # fmt: skip
        body += struct.pack(f"<{len(parts)}i", *parts) + pts.astype("<f8").tobytes()
        contents.append(body)
    allpts = np.vstack([np.vstack(r) for r in records])
    bbox = (allpts[:, 0].min(), allpts[:, 1].min(), allpts[:, 0].max(), allpts[:, 1].max())
    shp = bytearray()
    shx = bytearray()
    offset = 50
    for i, body in enumerate(contents, start=1):
        shp += struct.pack(">2i", i, len(body) // 2) + body
        shx += struct.pack(">2i", offset, len(body) // 2)
        offset += 4 + len(body) // 2
    for path, payload in ((f"{stem}.shp", shp), (f"{stem}.shx", shx)):
        header = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, (100 + len(payload)) // 2)
        header += struct.pack("<2i4d4d", 1000, 5, *bbox, 0, 0, 0, 0)
        with open(path, "wb") as f:
            f.write(header + payload)
    _write_dbf(stem.with_suffix(".dbf"), fields, rows)
    stem.with_suffix(".prj").write_text("LAEA sphere 6370997, lat 45, lon -100")


@pytest.fixture
def sources(tmp_path):
    political = tmp_path / "political"
    # The coarse line: the "Canada" polygon reaches down to 48.97 N between 118 and 116 W, as a
    # 1:10M line might, so a cell just south of 49 N in the band must still be US (D115).
    states = [
        ("US-WA", "USA", [_ring(-121.0, 47.0, -116.0, 49.0)]),
        ("CA-BC", "CAN", [_ring(-121.0, 49.0, -116.0, 52.0), _ring(-118.0, 48.97, -116.0, 49.0)]),
        # East of the band, the polygon alone decides: Canada south of 49 N here.
        ("CA-ON", "CAN", [_ring(-90.0, 47.0, -86.0, 50.0)]),
        # Alaska, with a lake (hole) and an island in it (a third ring), even-odd.
        (
            "US-AK",
            "USA",
            [
                _ring(-150.0, 60.0, -146.0, 62.0),
                _ring(-149.0, 60.5, -147.0, 61.5),
                _ring(-148.3, 60.8, -147.7, 61.2),
            ],
        ),
        ("MX-CHH", "MEX", [_ring(-108.0, 28.0, -104.0, 31.0)]),
    ]
    _write_shapefile(
        political,
        [r for _, _, r in states],
        [("COUNTRY", 20), ("STATEABB", 20)],
        [{"COUNTRY": c, "STATEABB": s} for s, c, _ in states],
    )
    eco = tmp_path / "eco"
    # Non-Arctic regions cover every state except a coastal sliver of Washington, 47.0 to 47.3 N,
    # which lies in no ecoregion polygon, as the CEC coastlines leave some cells (D117).
    _write_shapefile(
        eco,
        [
            [_ring(-121.0, 51.0, -116.0, 52.0)],
            [_ring(-121.0, 49.0, -116.0, 51.0)],
            [_ring(-121.0, 47.3, -116.0, 49.0)],
            [_ring(-90.0, 47.0, -86.0, 50.0)],
            [_ring(-150.0, 60.0, -146.0, 62.0)],
            [_ring(-108.0, 28.0, -104.0, 31.0)],
        ],
        [("LEVEL1", 5), ("NameL1_En", 40)],
        [
            {"LEVEL1": "2", "NameL1_En": "Tundra"},
            {"LEVEL1": "5", "NameL1_En": "Northern Forests"},
            {"LEVEL1": "7", "NameL1_En": "Marine West Coast Forests"},
            {"LEVEL1": "5", "NameL1_En": "Northern Forests"},
            {"LEVEL1": "6", "NameL1_En": "Northwestern Forested Mountains"},
            {"LEVEL1": "10", "NameL1_En": "North American Deserts"},
        ],
    )
    return political.with_suffix(".shp"), eco.with_suffix(".shp")


def _cell_lonlat(window):
    xs = window.left + (np.arange(window.width) + 0.5) * CELL_SIZE_M
    ys = window.top - (np.arange(window.height) + 0.5) * CELL_SIZE_M
    gx, gy = np.meshgrid(xs, ys)
    return Transformer.from_crs(GRID_CRS, GEOGRAPHIC_CRS, always_xy=True).transform(gx, gy)


def _window(lon0, lat0, lon1, lat1):
    t = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)
    xs, ys = t.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    s = 250
    return GridWindow(
        int(np.floor(min(xs) / s) * s), int(np.floor(min(ys) / s) * s),
        int(np.ceil(max(xs) / s) * s), int(np.ceil(max(ys) / s) * s),
    )  # fmt: skip


def test_a_shapefile_reads_back_its_rings(sources):
    political, _ = sources
    records = read_shapefile(political)
    assert [len(r) for r in records] == [1, 2, 1, 3, 1]
    assert all(np.allclose(ring[0], ring[-1]) for rings in records for ring in rings)


def test_countries_and_the_arctic_are_burned_by_cell_centre(sources, tmp_path):
    political, eco = sources
    window = _window(-121.0, 47.0, -116.0, 52.0)
    path = tmp_path / "mask.tif"
    build_mask(political, eco, window, path, block=64)
    country, arctic = read_mask(path, window)
    lon, lat = _cell_lonlat(window)
    inner = (lon > -120.95) & (lon < -116.05)
    us = inner & (lat > 47.02) & (lat < 48.96)
    ca = inner & (lat > 49.02) & (lat < 51.98)
    assert (country[us] == COUNTRY_US48).all()
    assert (country[ca] == COUNTRY_CAN).all()
    tundra = inner & (lat > 51.02) & (lat < 51.98)
    assert (arctic[tundra] == ECO_ARCTIC).all()
    assert (arctic[inner & (lat > 49.02) & (lat < 50.98)] == ECO_OTHER).all()
    assert (arctic[inner & (lat > 47.02) & (lat < 47.28)] == ECO_NONE).all()
    # The coarse "Canada" sliver south of 49 N between 118 and 116 W is burned as Canada.
    sliver = (lon > -117.9) & (lon < -116.1) & (lat > 48.975) & (lat < 48.995)
    assert sliver.any() and (country[sliver] == COUNTRY_CAN).all()


def test_the_band_keeps_t5s_49_n_rule_and_the_polygon_decides_elsewhere(sources, tmp_path):
    political, eco = sources
    window = _window(-121.0, 47.0, -116.0, 52.0)
    path = tmp_path / "mask.tif"
    build_mask(political, eco, window, path, block=64)
    country, arctic = read_mask(path, window)
    study, side = cells_in_study(window, country, arctic)
    lon, lat = _cell_lonlat(window)
    sliver = (lon > -117.9) & (lon < -116.1) & (lat > 48.975) & (lat < 48.995)
    assert (side[sliver] == SIDE_US).all()  # T5's rule, not the coarse polygon
    north = (lon > -120.9) & (lon < -116.1) & (lat > 49.005) & (lat < 50.98)
    assert (side[north] == SIDE_CA).all() and study[north].all()
    tundra = (lon > -120.9) & (lon < -116.1) & (lat > 51.02) & (lat < 51.98)
    assert not study[tundra].any()  # D111

    east = _window(-90.0, 47.0, -86.0, 50.0)
    path2 = tmp_path / "mask_east.tif"
    build_mask(political, eco, east, path2, block=64)
    c2, a2 = read_mask(path2, east)
    s2, side2 = cells_in_study(east, c2, a2)
    lon2, lat2 = _cell_lonlat(east)
    south_of_49 = (lon2 > -89.9) & (lon2 < -86.1) & (lat2 > 47.05) & (lat2 < 48.9)
    assert (side2[south_of_49] == SIDE_CA).all() and s2[south_of_49].all()


def test_alaska_mexico_and_a_lake_are_out_and_an_island_in_the_lake_is_back_in(sources, tmp_path):
    political, eco = sources
    window = _window(-150.0, 60.0, -146.0, 62.0)
    path = tmp_path / "mask_ak.tif"
    build_mask(political, eco, window, path, block=64)
    country, arctic = read_mask(path, window)
    lon, lat = _cell_lonlat(window)
    land = (lon > -149.9) & (lon < -149.1) & (lat > 60.1) & (lat < 61.9)
    lake = (lon > -148.9) & (lon < -148.4) & (lat > 60.6) & (lat < 61.4)
    island = (lon > -148.2) & (lon < -147.8) & (lat > 60.9) & (lat < 61.1)
    assert (country[land] == COUNTRY_US_OTHER).all()
    assert (country[lake] == COUNTRY_NONE).all()
    assert (country[island] == COUNTRY_US_OTHER).all()
    study, _ = cells_in_study(window, country, arctic)
    assert not study.any()  # D113: Alaska masked

    mx = _window(-108.0, 28.0, -104.0, 31.0)
    path_mx = tmp_path / "mask_mx.tif"
    build_mask(political, eco, mx, path_mx, block=64)
    cm, am = read_mask(path_mx, mx)
    lon, lat = _cell_lonlat(mx)
    inside = (lon > -107.9) & (lon < -104.1) & (lat > 28.1) & (lat < 30.9)
    assert (cm[inside] == COUNTRY_MEX).all()
    assert not cells_in_study(mx, cm, am)[0].any()


def test_blocks_give_the_same_mask_as_one_pass(sources, tmp_path):
    political, eco = sources
    window = _window(-121.0, 47.0, -116.0, 52.0)
    build_mask(political, eco, window, tmp_path / "a.tif", block=37)
    build_mask(political, eco, window, tmp_path / "b.tif", block=4096)
    a = read_mask(tmp_path / "a.tif", window)
    b = read_mask(tmp_path / "b.tif", window)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_a_cell_in_no_ecoregion_polygon_is_out_of_the_study_area(sources, tmp_path):
    political, eco = sources
    window = _window(-121.0, 47.0, -116.0, 49.0)
    path = tmp_path / "mask.tif"
    build_mask(political, eco, window, path, block=64)
    study, _ = cells_in_study(window, *read_mask(path, window))
    lon, lat = _cell_lonlat(window)
    inner = (lon > -120.95) & (lon < -116.05)
    sliver = inner & (lat > 47.02) & (lat < 47.28)
    land = inner & (lat > 47.32) & (lat < 48.9)
    assert sliver.any() and not study[sliver].any()  # D117
    assert study[land].all()
