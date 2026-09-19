"""The fixed choices of T1, transcribed from the dispatch.

Source: docs/dispatch/2026-09-18-t1-calendar-smoke-test.md ("Boxes, for T1 only", "Then build",
"Do not touch"). These are not parameters. The dispatch forbids changing the boxes, the window
list, the year range, the filters or the tuning budget once any test result has been seen, so
they live in one place, with no way to override them from a call site.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    """A latitude and longitude box, edges inclusive, in decimal degrees."""

    name: str
    south: float
    north: float
    west: float
    east: float

    def contains(self, latitude: float, longitude: float) -> bool:
        return self.south <= latitude <= self.north and self.west <= longitude <= self.east

    def wkt_polygon(self) -> str:
        """The box as a counter-clockwise WKT polygon, the winding GBIF's API requires."""
        return (
            f"POLYGON(({self.west} {self.south},{self.east} {self.south},"
            f"{self.east} {self.north},{self.west} {self.north},{self.west} {self.south}))"
        )


# "Pacific Northwest: 42.0 to 49.5 N, 125.0 to 121.0 W" and "East: 38.0 to 46.0 N, 84.0 to 70.0 W".
BOXES: tuple[Box, ...] = (
    Box(name="pnw", south=42.0, north=49.5, west=-125.0, east=-121.0),
    Box(name="east", south=38.0, north=46.0, west=-84.0, east=-70.0),
)

# "2015 to 2025", both ends included.
FIRST_YEAR = 2015
LAST_YEAR = 2025

# "Rolling windows of 3, 7, 14, 21, 28, 42, 56 and 90 days".
WINDOW_DAYS: tuple[int, ...] = (3, 7, 14, 21, 28, 42, 56, 90)

# "drop records with coordinate uncertainty above 1,000 m or missing".
MAX_COORDINATE_UNCERTAINTY_M = 1000.0

# "Presences against 12 random-date pseudo-absences per record" (secondary design, D13).
RANDOM_DATE_PSEUDO_ABSENCES_PER_RECORD = 12

# GBIF backbone keys, resolved on 2026-09-18 with
# https://api.gbif.org/v1/species/match?name=Cantharellus&rank=GENUS&kingdom=Fungi
# (usageKey 9623860, ACCEPTED, family Hydnaceae; a strict match without the kingdom returns
# NONE because the name is a homonym) and .../species/match?name=Fungi (usageKey 5).
FUNGI_KINGDOM_KEY = 5
CANTHARELLUS_GENUS_KEY = 9623860


def box_of(latitude: float, longitude: float) -> Box | None:
    """The T1 box a point falls in, or None. The two boxes do not overlap."""
    for box in BOXES:
        if box.contains(latitude, longitude):
            return box
    return None
