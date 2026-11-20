"""Build web assets for the Scarline portfolio page from the Cape York outputs.

Writes docs/data/: copies of the baseline and block results, and the 2D map set from build_map():
map_pre.jpg, map_post.jpg (SWIR2-NIR-red false colour, stretched), map_k.png, inspect.bin, scars.json,
map_meta.json, plus home_change.png for the home page. Run from the project root:
    python3 pipeline/build_web.py
"""
import json
import os
import shutil
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
import geopandas as gpd
import pyproj
import shapely
from rasterio.features import rasterize
from shapely.geometry import MultiPolygon, Polygon, box, mapping
from shapely.ops import transform as shp_transform, unary_union

from aoi_config import AOIS
from baseline import VALID_SCL, band_scale_offset, read_on_grid  # importing runs only module-level setup (capeyork default)

os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
ROOT = Path(__file__).resolve().parent.parent
AOI = ROOT / "data" / "capeyork"
RAW, PROC = AOI / "raw", AOI / "processed"
OUT = ROOT / "docs" / "data"
OUT.mkdir(parents=True, exist_ok=True)
PRE = "S2A_54LXL_20220713_0_L2A"
POST = "S2B_54LXL_20221026_0_L2A"

manifest = json.loads((RAW / "manifest.json").read_text())


def scale_for(sid):
    sc = manifest["scenes"][sid]["raster_bands"]["nir"][0][0]
    return sc


def read(sid, band, shape):
    with rasterio.open(RAW / f"{sid}_{band}.tif") as s:
        a = s.read(1, out_shape=shape, resampling=Resampling.bilinear).astype(np.float32)
    return a


def stretch(a, valid):
    lo, hi = np.percentile(a[valid], [2, 98])
    return np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)


def composite(sid, shape, valid):
    s = scale_for(sid)  # reflectance = DN * scale (offset is 0: boa_offset_applied)
    swir = read(sid, "swir22", shape) * s
    nir = read(sid, "nir", shape) * s
    red = read(sid, "red", shape) * s
    rgb = np.dstack([stretch(swir, valid), stretch(nir, valid), stretch(red, valid)])
    rgb = rgb * 0.9 + 0.02
    rgb[~valid] = 0.04  # cloud and shadow rendered dark, not as bright artefacts
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


MAP_W = 1024
THRESH = np.round(np.arange(0.05, 0.851, 0.01), 2)  # 81 slider values, same as #thr
SPLIT_COL = None  # set in build_map: W0 // 2 (baseline.py: west = cols < width // 2)
TRUTH_M, AMB_M = set(AOIS["capeyork"]["truth_months"]), set(AOIS["capeyork"]["ambiguous_months"])


def _rng(m):
    m = sorted(m)
    return f"{m[0]}-{m[-1]}" if m == list(range(m[0], m[-1] + 1)) else ", ".join(map(str, m))

SCAR_MIN_M2 = 10_000  # 1 ha


def _clean(poly):
    """Drop holes under 1 ha."""
    return Polygon(poly.exterior, [r for r in poly.interiors if Polygon(r).area >= SCAR_MIN_M2])


def build_scars(ref_crs, bounds):
    gdf = gpd.read_file(RAW / "qld_firescars_2022.geojson")
    gdf = gdf[gdf["month"].isin(sorted(TRUTH_M | AMB_M))].to_crs(ref_crs)
    clip = box(*bounds)
    to_ll = pyproj.Transformer.from_crs(ref_crs, 4326, always_xy=True).transform
    feats = []
    for cls, months in [("truth", TRUTH_M), ("ambiguous", AMB_M)]:
        g = unary_union([x for x in gdf[gdf["month"].isin(months)].geometry if x is not None]).intersection(clip)
        parts = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area >= SCAR_MIN_M2]
        g = unary_union([_clean(p) for p in parts]).simplify(50, preserve_topology=True)
        g = shp_transform(to_ll, g)
        g = shapely.transform(g, lambda c: np.round(c, 4))
        feats.append({"type": "Feature", "properties": {"cls": cls}, "geometry": mapping(g)})
    (OUT / "scars.json").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))


def build_home_change(k, x0, y0, cell):
    """home_change.png: map_post.jpg in grey + orange tint where dNBR > 0.21 + white Aug-Oct scar outlines. Same size as map_post.jpg."""
    post = Image.open(OUT / "map_post.jpg").convert("RGB")
    a = np.asarray(post).astype(np.float32)
    assert a.shape[:2] == k.shape, (a.shape, k.shape)
    burnt = k > int(np.flatnonzero(THRESH == 0.21)[0])  # k = number of THRESH values dNBR exceeds
    a = np.repeat((a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None], 3, axis=2) * 0.8  # grey base so the tint reads
    a[burnt] = a[burnt] * 0.4 + np.array([224, 96, 28], np.float32) * 0.6
    img = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(img)
    R = 6378137.0
    def px(lon, lat):  # same formula as L.CRS.EPSG3857 / map_meta grid
        x = R * np.radians(lon)
        y = R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        return ((x - x0) / cell, (y0 - y) / cell)
    truth = next(f for f in json.loads((OUT / "scars.json").read_text())["features"] if f["properties"]["cls"] == "truth")
    g = shapely.geometry.shape(truth["geometry"])
    for poly in getattr(g, "geoms", [g]):
        for ring in [poly.exterior, *poly.interiors]:
            d.line([px(*c) for c in ring.coords], fill=(255, 255, 255), width=2)
    assert img.size == post.size, (img.size, post.size)
    img.save(OUT / "home_change.png", optimize=True)


def build_map(dnbr, scored):
    """2D map assets on a square-cell EPSG:3857 grid, W=1024. See docs/specialists.html (#map) for the reader."""
    global SPLIT_COL
    H0, W0 = dnbr.shape
    SPLIT_COL = W0 // 2
    assert SPLIT_COL == 2503, SPLIT_COL  # capeyork
    with rasterio.open(RAW / f"{PRE}_nir.tif") as ref:
        prof = {"height": ref.height, "width": ref.width, "transform": ref.transform, "crs": ref.crs}
        bounds = ref.bounds
    x0, y1, x1, y0 = transform_bounds(prof["crs"], 3857, *bounds, densify_pts=21)  # y0 = north edge, y1 = south edge
    cell = (x1 - x0) / MAP_W
    H = int(np.ceil((y0 - y1) / cell))
    # cell centres -> UTM -> source row/col (floor)
    cx = x0 + (np.arange(MAP_W) + 0.5) * cell
    cy = y0 - (np.arange(H) + 0.5) * cell
    X, Y = np.meshgrid(cx, cy)
    E, N = pyproj.Transformer.from_crs(3857, prof["crs"], always_xy=True).transform(X, Y)
    t = prof["transform"]
    col = np.floor((E - t.c) / t.a).astype(np.int64)
    row = np.floor((t.f - N) / -t.e).astype(np.int64)
    outside = (row < 0) | (row >= H0) | (col < 0) | (col >= W0)
    r = np.clip(row, 0, H0 - 1)
    c = np.clip(col, 0, W0 - 1)

    # DN on the 10 m grid (red, NIR native 10 m; SWIR2 and SCL native 20 m, nearest-resampled by baseline.read_on_grid)
    def dn(sid, band):
        return read_on_grid(RAW / f"{sid}_{band}.tif", prof, Resampling.nearest)
    sc = {sid: band_scale_offset(sid) for sid in (PRE, POST)}
    assert all(sc[s][b] == (0.0001, 0.0) for s in sc for b in ("red", "nir", "swir22")), "scale/offset changed: update meta"
    bands, scl_ok = {}, {}
    for sid, nm in [(PRE, "pre"), (POST, "post")]:
        for b in ("red", "nir", "swir22"):
            bands[nm, b] = dn(sid, b).astype(np.uint16)
        scl_ok[nm] = np.isin(dn(sid, "scl").astype(np.uint8), list(VALID_SCL))

    scars = gpd.read_file(RAW / "qld_firescars_2022.geojson").to_crs(prof["crs"])
    shape = (H0, W0)
    def ras(months):
        return rasterize([(g, 1) for g, m in zip(scars.geometry, scars["month"]) if m in months and g is not None],
                         out_shape=shape, transform=t, fill=0, dtype=np.uint8).astype(bool)
    truth, amb = np.load(PROC / "truth.npy"), ras(AMB_M)

    flags = (scored[r, c].astype(np.uint16) | (truth[r, c].astype(np.uint16) << 1) | (amb[r, c].astype(np.uint16) << 2)
             | (scl_ok["pre"][r, c].astype(np.uint16) << 3) | (scl_ok["post"][r, c].astype(np.uint16) << 4)
             | (outside.astype(np.uint16) << 5))
    flags[outside] = 32
    dv = dnbr[r, c]
    k = np.zeros(dv.shape, np.uint8)
    for th in THRESH:
        k += (dv > th)  # same comparison as baseline.py; NaN -> False
    k[outside] = 0

    rec = np.zeros((H, MAP_W, 9), "<u2")
    rec[..., 0], rec[..., 1] = row, col
    for i, (nm, b) in enumerate([("pre", "red"), ("pre", "nir"), ("pre", "swir22"), ("post", "red"), ("post", "nir"), ("post", "swir22")]):
        rec[..., 2 + i] = bands[nm, b][r, c]
    rec[..., 8] = flags | (k.astype(np.uint16) << 8)  # high byte = k (0..81)
    rec[outside] = 0
    rec[..., 8][outside] = 32
    (OUT / "inspect.bin").write_bytes(rec.tobytes())
    Image.fromarray(np.dstack([k, flags.astype(np.uint8), np.zeros_like(k)]), "RGB").save(OUT / "map_k.png", optimize=True)

    for nm, sid in [("pre", PRE), ("post", POST)]:
        comp = composite(sid, shape, scl_ok[nm])  # per-date cloud mask so ambiguous-month ground stays visible
        out = comp[r, c]
        out[outside] = (7, 11, 20)
        Image.fromarray(out).save(OUT / f"map_{nm}.jpg", quality=86)
        del comp

    build_scars(prof["crs"], bounds)
    build_home_change(k, x0, y0, cell)

    # quadratic fit: source (col, row) pixel centre -> 3857 (x, y), in s = col/W0, t = row/H0
    gs, gt = np.meshgrid(np.linspace(0, 1, 21), np.linspace(0, 1, 21))
    gs, gt = gs.ravel(), gt.ravel()
    to3857 = pyproj.Transformer.from_crs(prof["crs"], 3857, always_xy=True).transform
    px, py = to3857(t.c + gs * W0 * t.a, t.f + gt * H0 * t.e)
    A = np.column_stack([np.ones_like(gs), gs, gt, gs * gs, gs * gt, gt * gt])
    cx_, *_ = np.linalg.lstsq(A, px, rcond=None)
    cy_, *_ = np.linalg.lstsq(A, py, rcond=None)
    resid = float(np.max(np.hypot(A @ cx_ - px, A @ cy_ - py)))
    assert resid < 1.0, f"quadratic fit residual {resid} m"

    to_ll = pyproj.Transformer.from_crs(prof["crs"], 4326, always_xy=True).transform
    xs = t.c + SPLIT_COL * t.a
    n_lon, n_lat = to_ll(xs, t.f)
    s_lon, s_lat = to_ll(xs, t.f + H0 * t.e)
    meta = {
        "grid": {"crs": "EPSG:3857", "W": MAP_W, "H": H, "x0": x0, "y0": y0, "cell": cell},
        "source": {"crs": "EPSG:32754", "rows": H0, "cols": W0, "pixel_m": 10, "origin": [t.c, t.f]},
        "scale": 0.0001, "offset": 0,
        "thresholds": [float(v) for v in THRESH],
        "inspect_record": {"bytes": 18, "dtype": "uint16 little-endian",
                           "fields": ["srcRow", "srcCol", "preRed", "preNir", "preSwir22", "postRed", "postNir", "postSwir22", "flags"],
                           "flags_layout": "bits 0-7 flags, bits 8-15 k (number of the 81 thresholds dNBR exceeds)"},
        "flags": {"0": "scored", "1": f"truth (QLD months {_rng(TRUTH_M)})", "2": f"ambiguous (months {_rng(AMB_M)})", "3": "pre SCL in 4,5,6",
                  "4": "post SCL in 4,5,6", "5": "outside scene"},
        "split": {"col": SPLIT_COL, "line_latlon": [[n_lat, n_lon], [s_lat, s_lon]]},
        "quad_fit": {"basis": "[1, s, t, s^2, s*t, t^2], s = col/cols, t = row/rows, pixel-edge coordinates",
                     "x": cx_.tolist(), "y": cy_.tolist(), "max_residual_m": resid},
        "scenes": {"pre": PRE, "post": POST},
    }
    (OUT / "map_meta.json").write_text(json.dumps(meta, separators=(",", ":")))
    print(f"map grid {MAP_W}x{H}, cell {cell:.2f} m, quad residual {resid:.4f} m")


def main():
    dnbr = np.load(PROC / "dnbr.npy")
    valid = np.load(PROC / "valid.npy")
    build_map(dnbr, valid)
    shutil.copy(PROC / "baseline_metrics.json", OUT / "baseline_metrics.json")
    shutil.copy(PROC / "block_cv.json", OUT / "block_cv.json")
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
