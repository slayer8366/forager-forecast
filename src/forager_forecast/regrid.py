"""Exact area-weighted regrid of a native raster onto the master grid.

Why not GDAL's ``average``: on the real geometry it is not the area-weighted mean. Around 47 N a
250 m master cell lands in SoilGrids' Homolosine as a quad about 285 m by 219 m, rotated about 13
degrees, and GDAL approximates that footprint. On synthetic noise its result differed from exact
area weights by up to 0.50 pH (mean 0.09); it agreed to 1e-6 only when the two grids differed by a
pure shift. The probe scripts are in docs/audits/2026-10-06-t4-verify/ and the finding in the T4
completion report. The planner accepted exact area weights on 2026-10-06.

How: each master cell's four corners go through ``to_native`` (a pinned pyproj transform for real
data), giving a quad in native pixel coordinates. The quad is clipped against every native pixel it
can touch (Sutherland-Hodgman against the unit square, vectorised in numpy), and the overlap areas
weight the pixel values. Edges are straight between corners: over 250 m the projection's curvature
is far below the precision of the data. No-data pixels (NaN) carry no weight; the share of the
cell's area that is valid is returned beside the value, so a cell averaged from a sliver is visible
as one. No geometry library is used, so no dependency was added.
"""

from collections.abc import Callable

import numpy as np
from rasterio.transform import Affine

from forager_forecast.grid import CELL_SIZE_M, GridWindow

ToNative = Callable[[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]

# A convex quad clipped by four half-planes keeps at most 4 + 4 vertices.
_MAX_VERTICES = 8


def _clip_half_plane(
    verts: np.ndarray, count: np.ndarray, axis: int, value: float, keep_above: bool
) -> tuple[np.ndarray, np.ndarray]:
    """Clip convex polygons (N, M, 2), each with ``count`` real vertices, by one half-plane."""
    n, m, _ = verts.shape
    k = np.arange(m)[None, :]
    real = k < count[:, None]
    prev_idx = np.where(k == 0, np.maximum(count[:, None] - 1, 0), k - 1)
    prev = np.take_along_axis(verts, prev_idx[..., None].repeat(2, axis=2), axis=1)
    cur = verts
    sign = 1.0 if keep_above else -1.0
    cur_in = sign * (cur[..., axis] - value) >= 0
    prev_in = sign * (prev[..., axis] - value) >= 0
    crossing = real & (cur_in != prev_in)
    denom = cur[..., axis] - prev[..., axis]
    t = np.where(crossing, (value - prev[..., axis]) / np.where(crossing, denom, 1.0), 0.0)
    inter = prev + t[..., None] * (cur - prev)
    inter[..., axis] = np.where(crossing, value, inter[..., axis])

    out = np.empty((n, 2 * m, 2))
    out[:, 0::2] = inter
    out[:, 1::2] = cur
    present = np.empty((n, 2 * m), dtype=bool)
    present[:, 0::2] = crossing
    present[:, 1::2] = real & cur_in
    new_count = present.sum(axis=1)
    if new_count.max(initial=0) > _MAX_VERTICES:
        raise AssertionError("a clipped quad cannot have more than eight vertices")
    order = np.argsort(~present, axis=1, kind="stable")[:, :_MAX_VERTICES]
    compact = np.take_along_axis(out, order[..., None].repeat(2, axis=2), axis=1)
    return compact, new_count


def polygon_square_overlap(polys: np.ndarray) -> np.ndarray:
    """Area of each convex polygon (N, M, 2), vertices in order, inside the unit square."""
    polys = np.asarray(polys, dtype="float64")
    n, m, _ = polys.shape
    verts = np.zeros((n, _MAX_VERTICES, 2))
    verts[:, :m] = polys
    count = np.full(n, m)
    unit_square = ((0, 0.0, True), (0, 1.0, False), (1, 0.0, True), (1, 1.0, False))
    for axis, value, keep_above in unit_square:
        verts, count = _clip_half_plane(verts, count, axis, value, keep_above)
    k = np.arange(_MAX_VERTICES)[None, :]
    real = k < count[:, None]
    next_idx = np.where(k + 1 >= count[:, None], 0, k + 1)
    nxt = np.take_along_axis(verts, next_idx[..., None].repeat(2, axis=2), axis=1)
    cross = verts[..., 0] * nxt[..., 1] - nxt[..., 0] * verts[..., 1]
    return np.abs(0.5 * np.where(real, cross, 0.0).sum(axis=1))


def area_weighted_regrid(
    native: np.ndarray,
    native_transform: Affine,
    to_native: ToNative,
    window: GridWindow,
    chunk_rows: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    """Regrid bands (B, H, W) onto ``window``. Returns (values, valid_fraction), each (B, h, w).

    ``native`` holds NaN for no data. ``to_native`` maps ESRI:102008 x, y arrays to the native
    CRS. A cell with no valid overlap is NaN with fraction 0. A cell that reaches past the native
    raster raises: a gap there would be the fetch's fault, not the soil's.
    """
    a = _north_up(native_transform)

    def pixel_position(nx, ny):
        return (nx - a.c) / a.a, (ny - a.f) / a.e

    return _regrid(native, pixel_position, to_native, window, chunk_rows)


def area_weighted_regrid_from_origin(
    native: np.ndarray,
    source_transform: Affine,
    col_off: int,
    row_off: int,
    to_native: ToNative,
    window: GridWindow,
    chunk_rows: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    """As ``area_weighted_regrid``, for a subset starting at (``col_off``, ``row_off``) of a source.

    T6b (D115 item 5). Positions are computed against the whole source raster's transform, then the
    integer offset is taken off, which is exact. So a cell's arithmetic does not depend on where a
    tile's subset starts, and the same cell comes out bit-identical from any tile. The
    window-relative form above differs in the last bits between subsets (T6b verify report,
    section 3, edge_origin_probe).
    """
    a = _north_up(source_transform)

    def pixel_position(nx, ny):
        return (nx - a.c) / a.a - col_off, (ny - a.f) / a.e - row_off

    return _regrid(native, pixel_position, to_native, window, chunk_rows)


def _north_up(a: Affine) -> Affine:
    if a.b != 0 or a.d != 0 or a.a <= 0 or a.e >= 0:
        raise ValueError("native raster must be north-up with no rotation")
    return a


def _regrid(native, pixel_position, to_native, window, chunk_rows):
    native = np.asarray(native, dtype="float64")
    if native.ndim != 3:
        raise ValueError("native must be (bands, rows, cols)")
    bands, nrows, ncols = native.shape
    finite = np.isfinite(native)
    values = np.full((bands, window.height, window.width), np.nan)
    fraction = np.zeros((bands, window.height, window.width))

    xs = window.left + CELL_SIZE_M * np.arange(window.width + 1, dtype="float64")
    for r0 in range(0, window.height, chunk_rows):
        r1 = min(r0 + chunk_rows, window.height)
        ys = window.top - CELL_SIZE_M * np.arange(r0, r1 + 1, dtype="float64")
        gx, gy = np.meshgrid(xs, ys)
        nx, ny = to_native(gx.ravel(), gy.ravel())
        u, v = pixel_position(np.asarray(nx), np.asarray(ny))
        u = u.reshape(gx.shape)
        v = v.reshape(gx.shape)
        quad = np.stack(
            [
                np.stack([u[:-1, :-1], v[:-1, :-1]], axis=-1),
                np.stack([u[:-1, 1:], v[:-1, 1:]], axis=-1),
                np.stack([u[1:, 1:], v[1:, 1:]], axis=-1),
                np.stack([u[1:, :-1], v[1:, :-1]], axis=-1),
            ],
            axis=2,
        ).reshape(-1, 4, 2)
        col0 = np.floor(quad[..., 0].min(axis=1)).astype(np.int64)
        row0 = np.floor(quad[..., 1].min(axis=1)).astype(np.int64)
        span_c = int((np.floor(quad[..., 0].max(axis=1)) - col0).max()) + 1
        span_r = int((np.floor(quad[..., 1].max(axis=1)) - row0).max()) + 1

        total = np.zeros(len(quad))
        w_valid = np.zeros((bands, len(quad)))
        w_sum = np.zeros((bands, len(quad)))
        for dr in range(span_r):
            for dc in range(span_c):
                pc = col0 + dc
                pr = row0 + dr
                local = quad - np.stack([pc, pr], axis=-1)[:, None, :].astype("float64")
                overlap = polygon_square_overlap(local)
                touched = overlap > 0
                inside = (pc >= 0) & (pc < ncols) & (pr >= 0) & (pr < nrows)
                if (touched & ~inside).any():
                    raise ValueError("the native raster does not cover every master cell")
                cc = np.clip(pc, 0, ncols - 1)
                rr = np.clip(pr, 0, nrows - 1)
                total += overlap
                for b in range(bands):
                    ok = finite[b, rr, cc] & touched
                    w = np.where(ok, overlap, 0.0)
                    w_valid[b] += w
                    w_sum[b] += np.where(ok, w * native[b, rr, cc], 0.0)
        shape = (r1 - r0, window.width)
        for b in range(bands):
            with np.errstate(invalid="ignore", divide="ignore"):
                val = np.where(w_valid[b] > 0, w_sum[b] / w_valid[b], np.nan)
            values[b, r0:r1] = val.reshape(shape)
            fraction[b, r0:r1] = (w_valid[b] / total).reshape(shape)
    return values, fraction
