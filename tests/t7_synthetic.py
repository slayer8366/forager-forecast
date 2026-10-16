"""Synthetic fixtures shared by the T7 tests. No real record, list or layer is read here."""

import zipfile
from xml.sax.saxutils import escape

import numpy as np
import rasterio
from rasterio.transform import from_origin

from forager_forecast.grid import CELL_SIZE_M, GRID_CRS


def write_xlsx(path, sheets: dict[str, list[list[str]]]) -> None:
    """A minimal workbook: shared strings for text, inline numbers for numeric-looking cells."""
    strings: list[str] = []
    index: dict[str, int] = {}

    def col(i):
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    sheet_xml = {}
    for name, rows in sheets.items():
        out = []
        for r, row in enumerate(rows, start=1):
            cells = []
            for c, value in enumerate(row):
                if value == "":
                    continue
                ref = f"{col(c)}{r}"
                if value.replace(".", "", 1).isdigit():
                    cells.append(f'<c r="{ref}"><v>{value}</v></c>')
                else:
                    if value not in index:
                        index[value] = len(strings)
                        strings.append(value)
                    cells.append(f'<c r="{ref}" t="s"><v>{index[value]}</v></c>')
            out.append(f'<row r="{r}">{"".join(cells)}</row>')
        sheet_xml[name] = (
            '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.'
            'openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            + "".join(out)
            + "</sheetData></worksheet>"
        )
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rns = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    sheets_el = "".join(
        f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, n in enumerate(sheet_xml, start=1)
    )
    rels = "".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        for i, _ in enumerate(sheet_xml, start=1)
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "xl/workbook.xml", f"<workbook {ns} {rns}><sheets>{sheets_el}</sheets></workbook>"
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + rels
            + "</Relationships>",
        )
        z.writestr(
            "xl/sharedStrings.xml",
            f"<sst {ns}>" + "".join(f"<si><t>{escape(s)}</t></si>" for s in strings) + "</sst>",
        )
        for i, xml in enumerate(sheet_xml.values(), start=1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", xml)


def write_raster(path, window, bands: dict, dtype="float32", tags=None, nodata=None):
    profile = {
        "driver": "GTiff", "width": window.width, "height": window.height, "count": len(bands),
        "dtype": dtype, "crs": GRID_CRS, "nodata": nodata,
        "transform": from_origin(window.left, window.top, CELL_SIZE_M, CELL_SIZE_M),
    }  # fmt: skip
    with rasterio.open(path, "w", **profile) as dst:
        for k, (name, data) in enumerate(bands.items(), start=1):
            dst.write(np.asarray(data).astype(dtype), k)
            dst.set_band_description(k, name)
        if tags:
            dst.update_tags(**tags)
