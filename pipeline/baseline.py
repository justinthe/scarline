"""dNBR baseline for Scarline: threshold burn index change, score vs QLD 2022 fire scars.

AOI and scenes come from pipeline/aoi_config.py (argument: aoi name, default capeyork).

Reflectance = DN * scale + offset. Offset is 0 when the STAC flag boa_offset_applied is True (both scenes here).
Truth window and ambiguous months come from pipeline/aoi_config.py for each AOI.
Ambiguous-month pixels (may burn before pre or after post) are excluded from scoring.
Threshold chosen on the west half, scored on the east half. F1/IoU are null where a split has no positives.
Run from the project root:  python3 pipeline/baseline.py gulf
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aoi_config import AOIS

ROOT = Path(__file__).resolve().parent.parent
NAME = sys.argv[1] if len(sys.argv) > 1 else "capeyork"
CFG = AOIS[NAME]
RAW = ROOT / "data" / NAME / "raw"
OUT = ROOT / "data" / NAME / "processed"
OUT.mkdir(parents=True, exist_ok=True)

PRE = CFG["pre"]
POST = CFG["post"]
VALID_SCL = {4, 5, 6}  # vegetation, bare soil, water
TRUTH_MONTHS = set(CFG["truth_months"])
AMBIGUOUS_MONTHS = set(CFG["ambiguous_months"])
THRESHOLDS = np.round(np.arange(0.05, 0.85, 0.01), 2)

manifest = json.loads((RAW / "manifest.json").read_text())


def band_scale_offset(sid):
    """Scale and offset per band from the STAC raster:bands metadata saved at fetch time."""
    scene = manifest["scenes"][sid]
    rb = scene["raster_bands"]
    if scene["boa_offset_applied"]:  # offset already removed from pixel values (STAC earthsearch:boa_offset_applied)
        return {band: (rb[band][0][0], 0.0) for band in rb}
    return {band: rb[band][0] for band in rb}  # (scale, offset) tuples


def read_on_grid(path, ref_profile, resampling):
    with rasterio.open(path) as src:
        dst = np.zeros((ref_profile["height"], ref_profile["width"]), dtype=np.float32)
        reproject(source=rasterio.band(src, 1), destination=dst,
                  src_transform=src.transform, src_crs=src.crs,
                  dst_transform=ref_profile["transform"], dst_crs=ref_profile["crs"],
                  resampling=resampling)
    return dst


def nbr(nir, swir):
    denom = nir + swir
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (nir - swir) / denom
    out[denom == 0] = np.nan
    return out


def load_scene(sid, ref):
    sc = band_scale_offset(sid)
    nir_s, nir_o = sc["nir"]
    swir_s, swir_o = sc["swir22"]
    nir = read_on_grid(RAW / f"{sid}_nir.tif", ref, Resampling.nearest) * nir_s + nir_o
    swir = read_on_grid(RAW / f"{sid}_swir22.tif", ref, Resampling.nearest) * swir_s + swir_o
    scl = read_on_grid(RAW / f"{sid}_scl.tif", ref, Resampling.nearest).astype(np.uint8)
    valid = np.isin(scl, list(VALID_SCL)) & (nir > 0) & (swir > 0)
    return nbr(nir, swir), valid


def score(pred, truth, mask):
    p = pred[mask].astype(bool)
    t = truth[mask].astype(bool)
    tp = int(np.sum(p & t))
    fp = int(np.sum(p & ~t))
    fn = int(np.sum(~p & t))
    has_positives = bool(tp + fn > 0)
    # F1 and IoU are undefined when the split has no positive pixels: report null, not 0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) and has_positives else None
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) and has_positives else None
    return {"iou": iou, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "has_positives": has_positives}


def main():
    with rasterio.open(RAW / f"{PRE}_nir.tif") as ref:
        ref_profile = {"height": ref.height, "width": ref.width, "transform": ref.transform, "crs": ref.crs}
    nbr_pre, valid_pre = load_scene(PRE, ref_profile)
    nbr_post, valid_post = load_scene(POST, ref_profile)
    dnbr = nbr_pre - nbr_post
    valid = valid_pre & valid_post & np.isfinite(dnbr)

    scars = gpd.read_file(RAW / "qld_firescars_2022.geojson").to_crs(ref_profile["crs"])
    shape, tr = (ref_profile["height"], ref_profile["width"]), ref_profile["transform"]
    truth = rasterize([(g, 1) for g, m in zip(scars.geometry, scars["month"]) if m in TRUTH_MONTHS and g is not None],
                      out_shape=shape, transform=tr, fill=0, dtype=np.uint8).astype(bool)
    ambiguous = rasterize([(g, 1) for g, m in zip(scars.geometry, scars["month"]) if m in AMBIGUOUS_MONTHS and g is not None],
                          out_shape=shape, transform=tr, fill=0, dtype=np.uint8).astype(bool)
    scored = valid & ~ambiguous  # pixels we can score

    cols = np.arange(ref_profile["width"])
    west = np.broadcast_to(cols < ref_profile["width"] // 2, dnbr.shape)
    train_mask = scored & west
    test_mask = scored & ~west

    sweep = []
    for t in THRESHOLDS:
        pred = dnbr > t
        sweep.append({"threshold": float(t), "train": score(pred, truth, train_mask), "test": score(pred, truth, test_mask)})
    best = max(sweep, key=lambda r: np.nan_to_num(r["train"]["f1"], nan=-1))
    t_star = best["threshold"]
    pred_star = dnbr > t_star

    all_burnt = np.ones(shape, dtype=bool)
    result = {
        "pre": PRE, "post": POST,
        "truth_months": sorted(TRUTH_MONTHS), "ambiguous_months_excluded": sorted(AMBIGUOUS_MONTHS),
        "scored_pixels": {"train_west": int(train_mask.sum()), "test_east": int(test_mask.sum())},
        "scar_fraction": {"train_west": float(truth[train_mask].mean()), "test_east": float(truth[test_mask].mean())},
        "threshold": t_star,
        "test_east": score(pred_star, truth, test_mask),
        "train_west": score(pred_star, truth, train_mask),
        "baseline_all_burnt_test_east": score(all_burnt, truth, test_mask),
        "baseline_threshold_0.27_test_east": score(dnbr > 0.27, truth, test_mask),
        "sweep": sweep,
    }
    (OUT / "baseline_metrics.json").write_text(json.dumps(result, indent=2))
    for name, arr in [("dnbr", dnbr), ("valid", scored), ("truth", truth)]:
        np.save(OUT / f"{name}.npy", arr)

    print("scar fraction (train/test):", {k: round(v, 3) for k, v in result["scar_fraction"].items()})
    print("threshold (west train):", t_star)
    if not result["test_east"]["has_positives"]:
        print("WARNING: east (test) half has no scar pixels; F1/IoU undefined")
    print("test east, model   :", {k: round(v, 3) if isinstance(v, float) else v for k, v in result["test_east"].items()})
    print("test east, all-burnt:", {k: round(v, 3) if isinstance(v, float) else v for k, v in result["baseline_all_burnt_test_east"].items()})


if __name__ == "__main__":
    main()
