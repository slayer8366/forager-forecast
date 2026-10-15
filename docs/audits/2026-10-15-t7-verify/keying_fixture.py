"""V11 fixture: master-grid cell centres (ESRI:102008) to longitude and latitude by the mask's
transformer (t6b_mask.cell_lonlat), then cells.cell_for; and cell_for on exact decimal ties."""

from pyproj import Transformer

from forager_forecast.cells import cell_for
from forager_forecast.grid import CELL_SIZE_M, GEOGRAPHIC_CRS, GRID_CRS, GridWindow
from forager_forecast.t6b_mask import cell_lonlat

print({"GRID_CRS": GRID_CRS, "GEOGRAPHIC_CRS": GEOGRAPHIC_CRS, "CELL_SIZE_M": CELL_SIZE_M})
fwd = Transformer.from_crs(GEOGRAPHIC_CRS, GRID_CRS, always_xy=True)
# The master-grid cell holding 45.5 N, 122.5 W, and its neighbours in one 3 x 3 window.
x, y = fwd.transform(-122.5, 45.5)
left = int(x // CELL_SIZE_M) * CELL_SIZE_M - CELL_SIZE_M
top = int(y // CELL_SIZE_M) * CELL_SIZE_M + 2 * CELL_SIZE_M
w = GridWindow(left, top - 3 * CELL_SIZE_M, left + 3 * CELL_SIZE_M, top)
lon, lat = cell_lonlat(w)
for r in range(3):
    for c in range(3):
        cell = cell_for(float(lat[r, c]), float(lon[r, c]))
        print({"row": r, "col": c, "lat": repr(float(lat[r, c])), "lon": repr(float(lon[r, c])),
               "cell": cell.id})  # fmt: skip
for la, lo in ((47.05, -123.05), (45.25, -122.45), (45.2499999, -122.4500001)):
    print({"lat": la, "lon": lo, "cell": cell_for(la, lo).id})
