"""Leave-one-block-out dNBR test on mid-density Cape York blocks.

Uses outputs of pipeline/baseline.py capeyork (dnbr.npy, valid.npy, truth.npy).
Blocks are 1000x1000 px (10 km at 10 m), origins (row, col). Threshold chosen by pooled F1 on the
other blocks, scored on the held-out block. Compares the model with all-burnt and the 0.27 threshold.
Run from the project root:  python3 pipeline/block_cv.py
"""
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "data" / "capeyork" / "processed"
BLOCK = 1000
BLOCKS = [(1000, 0), (3000, 1000), (1000, 2000), (2000, 0), (4000, 2000), (2000, 2000)]
THRESHOLDS = np.round(np.arange(0.05, 0.85, 0.01), 2)


def counts(pred, truth, mask):
    p, t = pred[mask], truth[mask]
    return int(np.sum(p & t)), int(np.sum(p & ~t)), int(np.sum(~p & t))


def f1(tp, fp, fn):
    return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else None


def main():
    dnbr = np.load(OUT / "dnbr.npy")
    valid = np.load(OUT / "valid.npy")
    truth = np.load(OUT / "truth.npy")
    masks = {}
    for r0, c0 in BLOCKS:
        m = np.zeros(truth.shape, bool)
        m[r0:r0 + BLOCK, c0:c0 + BLOCK] = True
        masks[(r0, c0)] = m & valid

    pooled = {"model": [0, 0, 0], "allburnt": [0, 0, 0], "s27": [0, 0, 0]}
    per_block = {}
    for test in BLOCKS:
        train_mask = np.zeros(truth.shape, bool)
        for b in BLOCKS:
            if b != test:
                train_mask |= masks[b]
        best = max(THRESHOLDS, key=lambda th: f1(*counts(dnbr > th, truth, train_mask)) or 0)
        tm = counts(dnbr > best, truth, masks[test])
        ab = counts(np.ones_like(truth, bool), truth, masks[test])
        s27 = counts(dnbr > 0.27, truth, masks[test])
        for key, c in [("model", tm), ("allburnt", ab), ("s27", s27)]:
            pooled[key] = [a + b for a, b in zip(pooled[key], c)]
        per_block[str(test)] = {"threshold": float(best), "model_f1": f1(*tm), "allburnt_f1": f1(*ab),
                                "s27_f1": f1(*s27), "prevalence": float(truth[masks[test]].mean())}
    summary = {k: f1(*v) for k, v in pooled.items()}
    result = {"blocks": per_block, "pooled_f1": summary,
              "model_beats_allburnt_blocks": sum(1 for b in per_block.values() if b["model_f1"] > b["allburnt_f1"])}
    (OUT / "block_cv.json").write_text(json.dumps(result, indent=2))
    print("pooled F1:", {k: round(v, 3) for k, v in summary.items()})
    print("model beats all-burnt on", result["model_beats_allburnt_blocks"], "of", len(BLOCKS), "blocks")


if __name__ == "__main__":
    main()
