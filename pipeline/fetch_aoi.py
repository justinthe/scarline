"""Clip Sentinel-2 bands (COG, Earth Search) and QLD 2022 fire scars to one AOI.

Reflectance = DN * scale + offset. The STAC flag earthsearch:boa_offset_applied says whether the
-0.1 offset (processing baseline 04.00) is already removed from the pixels; both scenes here: True, so offset 0.
The flag is stored in the manifest.
Clip bounds snap to a 20 m grid so 10 m and 20 m bands align exactly.
Outputs go to data/<aoi>/raw/ (git-ignored). Run from the project root:
    python3 pipeline/fetch_aoi.py capeyork   (or gulf)
"""
import json
import math
from pathlib import Path

import sys

import rasterio
import requests
from pyproj import Transformer
from rasterio.windows import from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aoi_config import AOIS

ROOT = Path(__file__).resolve().parent.parent
NAME = sys.argv[1] if len(sys.argv) > 1 else "capeyork"
CFG = AOIS[NAME]
RAW = ROOT / "data" / NAME / "raw"
RAW.mkdir(parents=True, exist_ok=True)

AOI_LONLAT = CFG["aoi_lonlat"]  # west, south, east, north
BUFFER_M = 500
SCAR_PAD_DEG = 0.01  # fire scar query covers the buffered area, not just the AOI
BANDS = ["red", "nir", "swir22", "scl"]


def fetch_items():
    """STAC metadata for the pre and post scenes (scale, offset flag, assets)."""
    out = {}
    for sid, role in [(CFG["pre"], "pre"), (CFG["post"], "post")]:
        r = requests.post("https://earth-search.aws.element84.com/v1/search",
                          json={"collections": ["sentinel-2-l2a"], "ids": [sid], "limit": 1}, timeout=60)
        r.raise_for_status()
        it = r.json()["features"][0]
        p = it["properties"]
        out[sid] = {"role": role, "datetime": p["datetime"], "cloud": p["eo:cloud_cover"], "epsg": p["proj:epsg"],
                    "processing_baseline": p.get("s2:processing_baseline"),
                    "boa_offset_applied": p.get("earthsearch:boa_offset_applied"),
                    "raster_bands": {k: [(b.get("scale"), b.get("offset")) for b in it["assets"][k].get("raster:bands", [])]
                                     for k in ["nir", "swir22"]},
                    "assets": {k: it["assets"][k]["href"] for k in BANDS}}
    return out


items = fetch_items()


def aoi_utm_snapped(epsg):
    t = Transformer.from_crs(4326, epsg, always_xy=True)
    xs, ys = zip(*[t.transform(x, y) for x, y in [(AOI_LONLAT[0], AOI_LONLAT[1]), (AOI_LONLAT[2], AOI_LONLAT[3])]])
    left, bottom = min(xs) - BUFFER_M, min(ys) - BUFFER_M
    right, top = max(xs) + BUFFER_M, max(ys) + BUFFER_M
    # snap outward to a 20 m grid so 10 m and 20 m windows share edges
    return (math.floor(left / 20) * 20, math.floor(bottom / 20) * 20,
            math.ceil(right / 20) * 20, math.ceil(top / 20) * 20)


def clip_band(href, bounds, out_path):
    with rasterio.open(href) as src:
        win = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        if win.col_off < 0 or win.row_off < 0 or win.col_off + win.width > src.width or win.row_off + win.height > src.height:
            raise ValueError(f"AOI not fully inside tile for {href}")
        data = src.read(1, window=win)
        profile = src.profile.copy()
        profile.update(height=data.shape[0], width=data.shape[1],
                       transform=src.window_transform(win), driver="GTiff",
                       compress="deflate", tiled=True)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(data, 1)
    return data.shape


manifest = {"aoi_lonlat": AOI_LONLAT, "scenes": {}, "fire_scars": {}}

for sid, meta in items.items():
    bounds = aoi_utm_snapped(meta["epsg"])
    manifest["scenes"][sid] = {"role": meta["role"], "datetime": meta["datetime"], "cloud_pct_tile": meta["cloud"],
                               "processing_baseline": meta["processing_baseline"], "boa_offset_applied": meta["boa_offset_applied"], "epsg": meta["epsg"],
                               "raster_bands": meta["raster_bands"], "bands": {}}
    for band in BANDS:
        out = RAW / f"{sid}_{band}.tif"
        shape = clip_band(meta["assets"][band], bounds, out)
        manifest["scenes"][sid]["bands"][band] = {"file": out.name, "shape": list(shape), "source": meta["assets"][band]}
        print(sid, band, shape)

# QLD 2022 fire scars (ArcGIS layer 36) over the buffered AOI, paged 500 at a time
west, south, east, north = AOI_LONLAT
URL = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Environment/FireScarMapping/MapServer/36/query"
features, offset, page = [], 0, 500
while True:
    r = requests.get(URL, params={
        "where": "1=1",
        "geometry": f"{west - SCAR_PAD_DEG},{south - SCAR_PAD_DEG},{east + SCAR_PAD_DEG},{north + SCAR_PAD_DEG}",
        "geometryType": "esriGeometryEnvelope", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "outFields": "fire_id,month,year",
        "outSR": 4326, "f": "geojson", "resultOffset": offset, "resultRecordCount": page,
    }, timeout=300)
    r.raise_for_status()
    batch = r.json()["features"]
    features += batch
    if len(batch) < page:
        break
    offset += page
out = RAW / "qld_firescars_2022.geojson"
out.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
manifest["fire_scars"] = {"file": out.name, "features": len(features),
                          "query_bbox_lonlat": [west - SCAR_PAD_DEG, south - SCAR_PAD_DEG, east + SCAR_PAD_DEG, north + SCAR_PAD_DEG],
                          "source": "QLD FireScarMapping MapServer layer 36 (2022)",
                          "licence": "CC BY 4.0", "aoi": NAME}
print("fire scars", len(features))
(RAW / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("wrote", RAW / "manifest.json")
