import math

import pytest
from pyproj import Transformer
from rasterio.crs import CRS
from rasterio.warp import transform as gdal_transform

from forager_forecast.grid import (
    CELL_SIZE_M,
    GRID_CRS,
    GridCell,
    GridWindow,
    cell_at,
    cell_for_lonlat,
    cell_from_id,
    snap_bounds,
    window_for_bounds,
)


def test_a_known_point_lands_in_a_known_cell_with_a_known_id():
    # Seattle, 47.6062 N 122.3321 W. ESRI:102008 x, y observed in the verify report:
    # (-1843096.297, 1156036.185). floor(x / 250) = -7373, floor(y / 250) = 4624.
    cell = cell_for_lonlat(-122.3321, 47.6062)
    assert cell == GridCell(col=-7373, row=4624)
    assert cell.id == ((4624 + 32768) << 16) | (-7373 + 32768)
    assert cell.id == 2_450_547_507  # (37392 << 16) | 25395


def test_the_lattice_origin_is_the_projection_false_origin():
    assert cell_at(0.0, 0.0) == GridCell(0, 0)
    assert cell_at(-0.001, -0.001) == GridCell(-1, -1)
    assert GridCell(0, 0).bounds == (0, 0, 250, 250)
    assert cell_for_lonlat(-96.0, 40.0) == GridCell(0, 0)


@pytest.mark.parametrize(
    ("x", "y", "expected"),
    [
        (500.0, 750.0, GridCell(2, 3)),  # on both edges: east and north, toward +infinity (D63)
        (499.999, 749.999, GridCell(1, 2)),
        (-250.0, -500.0, GridCell(-1, -2)),
        (-250.001, -500.001, GridCell(-2, -3)),
    ],
)
def test_points_on_edges_go_east_and_north(x, y, expected):
    assert cell_at(x, y) == expected


@pytest.mark.parametrize(
    ("col", "row"),
    [(0, 0), (-1, -1), (-7373, 4624), (-32768, -32768), (32767, 32767), (12345, -2)],
)
def test_cell_id_round_trips(col, row):
    cell = GridCell(col, row)
    assert 0 <= cell.id < 2**32
    assert cell_from_id(cell.id) == cell


def test_ids_are_distinct_over_a_block():
    ids = {GridCell(c, r).id for c in range(-40, 40) for r in range(-40, 40)}
    assert len(ids) == 80 * 80


def test_cells_outside_the_id_range_raise_instead_of_wrapping():
    with pytest.raises(ValueError):
        GridCell(32768, 0)
    with pytest.raises(ValueError):
        cell_at(-8_192_000.001, 0.0)
    with pytest.raises(ValueError):
        cell_from_id(2**32)
    with pytest.raises(ValueError):
        cell_at(math.nan, 0.0)


def test_north_american_extremes_have_ids():
    for lon, lat in [(-178.3, 28.4), (172.9, 52.9), (-77.2, 7.2), (-70.0, 83.1), (-12.0, 81.0)]:
        cell = cell_for_lonlat(lon, lat)
        assert cell_from_id(cell.id) == cell


def test_snap_bounds_widens_outward_to_the_lattice():
    assert snap_bounds(-1001.0, 10.0, 260.0, 499.0) == (-1250, 0, 500, 500)
    assert snap_bounds(-1000.0, 0.0, 250.0, 500.0) == (-1000, 0, 250, 500)
    with pytest.raises(ValueError):
        snap_bounds(1.0, 0.0, 1.0, 5.0)


def test_a_window_maps_raster_pixels_to_cells_with_rows_north_to_south():
    window = window_for_bounds(-1001.0, 10.0, 260.0, 499.0)
    assert (window.width, window.height) == (7, 2)
    assert window.cell_of_pixel(0, 0) == GridCell(col=-5, row=1)
    assert window.cell_of_pixel(1, 6) == GridCell(col=1, row=0)
    for r in range(window.height):
        for c in range(window.width):
            assert window.pixel_of_cell(window.cell_of_pixel(r, c)) == (r, c)
    with pytest.raises(IndexError):
        window.pixel_of_cell(GridCell(col=2, row=0))
    with pytest.raises(ValueError):
        GridWindow(1, 0, 250, 250)


def test_the_datum_step_is_pinned_and_gdal_agrees_with_it():
    # The grid reads WGS84 longitude and latitude as NAD83 (a null shift). GDAL, going from
    # SoilGrids' Homolosine on WGS84, must land within a millimetre of the same point, or the
    # native raster and the grid would disagree about where a cell is.
    homolosine = "+proj=igh +datum=WGS84 +no_defs"
    to_igh = Transformer.from_crs("EPSG:4326", homolosine, always_xy=True)
    to_grid_wgs84 = Transformer.from_crs("EPSG:4326", GRID_CRS, always_xy=True)
    for lon, lat in [(-122.3321, 47.6062), (-124.374, 47.604), (-121.736, 46.786)]:
        hx, hy = to_igh.transform(lon, lat)
        gx, gy = gdal_transform(CRS.from_string(homolosine), CRS.from_string(GRID_CRS), [hx], [hy])
        cell = cell_for_lonlat(lon, lat)
        from forager_forecast.grid import lonlat_transformer

        px, py = lonlat_transformer().transform(lon, lat)
        assert abs(gx[0] - px) < 1e-3 and abs(gy[0] - py) < 1e-3
        wx, wy = to_grid_wgs84.transform(lon, lat)
        assert abs(wx - px) < 1e-3 and abs(wy - py) < 1e-3
        assert cell == cell_at(gx[0], gy[0])
    assert CELL_SIZE_M == 250


def test_lonlat_to_grid_leaves_proj_no_datum_operation_to_choose():
    # Added by the T4 reviewer (D18), docs/audits/2026-10-06-t4-review.md. The test above passes
    # with the pin reverted, because at its three points PROJ picks the null shift either way.
    # What the pin guarantees is that no PROJ setup has a choice: from EPSG:4326, PROJ 9.8.1 lists
    # three usable NAD83 to WGS 84 operations (up to 2.6 m apart at Seattle) and 47 more that
    # need grids. From the pinned CRS there is one operation, the projection itself.
    from pyproj.transformer import TransformerGroup

    from forager_forecast.grid import lonlat_transformer

    transformer = lonlat_transformer()
    group = TransformerGroup(transformer.source_crs, transformer.target_crs, always_xy=True)
    assert len(group.transformers) == 1
    assert group.unavailable_operations == []


def test_the_pinned_null_shift_holds_where_offline_proj_would_shift():
    # Added by the T4 reviewer (D18). Offline, PROJ 9.8.1 going from EPSG:4326 applies a datum
    # shift of 0.7 to 1 m in Hawaii and the Aleutians (not in the T4 rectangle), so the pin is
    # observable without network grids. The pinned path must be the bare projection: no shift.
    from pyproj import Proj

    from forager_forecast.grid import lonlat_transformer

    albers = Proj(GRID_CRS)  # a projection alone, no CRS-to-CRS operation, so no datum step
    for lon, lat in [(-157.8583, 21.3069), (-176.64, 51.88), (-160.41986644407345, 18.5)]:
        bare_x, bare_y = albers(lon, lat)
        x, y = lonlat_transformer().transform(lon, lat)
        assert abs(x - bare_x) < 1e-3 and abs(y - bare_y) < 1e-3
        assert cell_for_lonlat(lon, lat) == cell_at(bare_x, bare_y)
