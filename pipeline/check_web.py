"""Checks for the 2D map assets in docs/data/ against the source tifs and processed arrays.
Plain asserts. Run from the project root after build_web.py:  python3 pipeline/check_web.py
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyproj
import rasterio
from PIL import Image
from shapely.geometry import Point

from aoi_config import AOIS

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
RAW, PROC, OUT = ROOT / "data/capeyork/raw", ROOT / "data/capeyork/processed", ROOT / "docs/data"
AMB_M = set(AOIS["capeyork"]["ambiguous_months"])  # truth months {8, 9, 10}: aoi_config
PRE, POST = "S2A_54LXL_20220713_0_L2A", "S2B_54LXL_20221026_0_L2A"

meta = json.loads((OUT / "map_meta.json").read_text())
g = meta["grid"]
W, H, x0, y0, cell = g["W"], g["H"], g["x0"], g["y0"], g["cell"]
T = np.array(meta["thresholds"])
assert len(T) == 81 and np.array_equal(T, np.round(np.arange(0.05, 0.851, 0.01), 2))

inspect = np.fromfile(OUT / "inspect.bin", dtype="<u2")
assert (OUT / "inspect.bin").stat().st_size == W * H * 18
inspect = inspect.reshape(H, W, 9)
mk = np.array(Image.open(OUT / "map_k.png"))
assert mk.shape == (H, W, 3), mk.shape
assert (mk[..., 2] == 0).all()
assert (OUT / "scars.json").stat().st_size < 600_000
assert meta["quad_fit"]["max_residual_m"] < 1.0

dnbr = np.load(PROC / "dnbr.npy")
valid, truth = np.load(PROC / "valid.npy"), np.load(PROC / "truth.npy")
scars = gpd.read_file(RAW / "qld_firescars_2022.geojson").to_crs(32754)
amb_geoms = [x for x, m in zip(scars.geometry, scars["month"]) if m in AMB_M and x is not None]
amb_tree = gpd.GeoSeries(amb_geoms, crs=32754)
amb_sidx = amb_tree.sindex
to_utm = pyproj.Transformer.from_crs(3857, 32754, always_xy=True)
to_ll = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
tifs = {(sid, b): rasterio.open(RAW / f"{sid}_{b}.tif") for sid in (PRE, POST) for b in ("red", "nir", "swir22", "scl")}


def sample(sid, b, E, N):
    ds = tifs[sid, b]
    r, c = ds.index(E, N)  # floor
    return int(ds.read(1, window=((r, r + 1), (c, c + 1)))[0, 0])


def check_cell(row, col, verbose=False):
    x, y = x0 + (col + .5) * cell, y0 - (row + .5) * cell
    E, N = to_utm.transform(x, y)
    rec = inspect[row, col]
    r, c = tifs[PRE, "nir"].index(E, N)
    inside = 0 <= r < dnbr.shape[0] and 0 <= c < dnbr.shape[1]
    if not inside:
        assert rec[8] == 32 and (rec[:8] == 0).all() and mk[row, col, 0] == 0 and mk[row, col, 1] == 32
        return None
    assert not rec[8] & 32
    assert (rec[0], rec[1]) == (r, c), ((rec[0], rec[1]), (r, c))
    dn = [sample(s, b, E, N) for s in (PRE, POST) for b in ("red", "nir", "swir22")]
    assert list(rec[2:8]) == dn, (list(rec[2:8]), dn)
    pre_ok = sample(PRE, "scl", E, N) in (4, 5, 6)
    post_ok = sample(POST, "scl", E, N) in (4, 5, 6)
    pn, ps, qn, qs = dn[1], dn[2], dn[4], dn[5]
    den1, den2 = pn + ps, qn + qs
    d = None
    if den1 and den2:
        d = (pn - ps) / den1 - (qn - qs) / den2
    amb = any(amb_tree.iloc[i].contains(Point(E, N)) for i in amb_sidx.query(Point(E, N)))
    ok = pre_ok and post_ok and pn > 0 and ps > 0 and qn > 0 and qs > 0 and d is not None and not amb
    f = int(rec[8]) & 255
    assert bool(f & 1) == bool(valid[r, c]) == ok, (f, valid[r, c], ok)
    assert bool(f & 2) == bool(truth[r, c])
    assert bool(f & 4) == amb
    assert bool(f & 8) == pre_ok and bool(f & 16) == post_ok
    assert mk[row, col, 1] == f and int(rec[8]) >> 8 == mk[row, col, 0]
    ref = float(dnbr[r, c])
    if d is None:
        assert np.isnan(ref)
    elif np.isfinite(ref):
        assert abs(d - ref) < 1e-6, (d, ref)
    k = int((dnbr[r, c] > T).sum())  # same comparison as baseline.py
    assert mk[row, col, 0] == k == int(rec[8]) >> 8, (mk[row, col, 0], k)
    if verbose:
        lon, lat = to_ll.transform(x, y)
        print(f"cell col={col} row={row} lat={lat:.5f} lon={lon:.5f} src(row={r},col={c}) DN pre r/n/s={dn[:3]} post r/n/s={dn[3:]} "
              f"dNBR={'n/a' if d is None else f'{d:.4f}'} k={k} flags={f} half={'west' if c < SPLIT_COL else 'east'}")
    return True


SPLIT_COL = dnbr.shape[1] // 2
assert SPLIT_COL == 2503 == meta["split"]["col"]

# 3 fixed cells: scored scar (east), scored non-scar (west), unscored. Chosen deterministically from the arrays.
rows, cols = np.mgrid[0:H, 0:W]
fl = inspect[..., 8] & 255
def first(mask):
    i = np.flatnonzero(mask.ravel())
    return divmod(int(i[len(i) // 3]), W)
fixed = [first((fl & 3 == 3) & (cols > W // 2)), first((fl & 3 == 1) & (cols < W // 2 - 50)), first((fl & 33 == 0) & (fl & 8 == 0))]
print("fixed cells for browser check (row, col):", fixed)
for rc in fixed:
    check_cell(*rc, verbose=True)
rng = np.random.default_rng(7)
n_in = 0
for _ in range(200):
    n_in += bool(check_cell(int(rng.integers(H)), int(rng.integers(W))))
print(f"200 random cells ok ({n_in} inside the scene)")

# every cell: k in map_k.png and in the inspect high byte equals (dnbr > T).sum() over all 81 thresholds
from pyproj import Transformer
cx = x0 + (np.arange(W) + .5) * cell
cy = y0 - (np.arange(H) + .5) * cell
E, N = Transformer.from_crs(3857, 32754, always_xy=True).transform(*np.meshgrid(cx, cy))
t = tifs[PRE, "nir"].transform
R_ = np.floor((t.f - N) / -t.e).astype(int); C_ = np.floor((E - t.c) / t.a).astype(int)
ins = (R_ >= 0) & (R_ < dnbr.shape[0]) & (C_ >= 0) & (C_ < dnbr.shape[1])
dv = np.where(ins, dnbr[np.clip(R_, 0, dnbr.shape[0] - 1), np.clip(C_, 0, dnbr.shape[1] - 1)], np.nan)
kall = np.zeros((H, W), np.uint8)
for th in T:
    kall += dv > th
assert (mk[..., 0] == kall).all() and ((inspect[..., 8] >> 8) == kall).all()
print(f"all {H * W} cells: map_k and inspect high byte == (dnbr > T).sum()")

# East-half counts from full-resolution dnbr.npy reproduce baseline_metrics.json exactly
bm = json.loads((PROC / "baseline_metrics.json").read_text())
east = valid & (np.arange(dnbr.shape[1]) >= dnbr.shape[1] // 2)[None, :]
for t, key in [(0.21, "test_east"), (0.27, "baseline_threshold_0.27_test_east")]:
    p = dnbr > t
    got = {"tp": int((p & truth & east).sum()), "fp": int((p & ~truth & east).sum()), "fn": int((~p & truth & east).sum())}
    assert got == {k: bm[key][k] for k in got}, (t, got, bm[key])
    print(f"east counts at {t} match baseline_metrics.json: {got}")
print("ALL CHECKS PASSED")
