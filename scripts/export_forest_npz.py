"""
Ekspor RandomForest scikit-learn (.pkl) ke .npz untuk server ringan (numpy murni).

Pemakaian:  python scripts/export_forest_npz.py [model.pkl] [keluaran.npz]
Bawaan   :  model/random_forest_v4_lite.pkl -> model/random_forest_v4_lite.npz
"""

import sys
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "model" / "random_forest_v4_lite.pkl"
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".npz")

model = joblib.load(src)
lefts, rights, feats, thrs, vals, roots = [], [], [], [], [], []
offset = 0
for est in model.estimators_:
    t = est.tree_
    n = t.node_count
    roots.append(offset)
    lefts.append(np.where(t.children_left >= 0, t.children_left + offset, -1))
    rights.append(np.where(t.children_right >= 0, t.children_right + offset, -1))
    feats.append(np.maximum(t.feature, 0))  # -2 pada daun -> 0 (tidak dipakai)
    thrs.append(t.threshold)
    v = t.value[:, 0, :].astype(np.float64)
    s = v.sum(axis=1, keepdims=True)
    s[s == 0] = 1
    vals.append((v / s).astype(np.float32))
    offset += n

np.savez_compressed(
    dst,
    classes=np.asarray(model.classes_).astype(str),
    n_features=np.int64(model.n_features_in_),
    roots=np.asarray(roots, dtype=np.int64),
    left=np.concatenate(lefts).astype(np.int32),
    right=np.concatenate(rights).astype(np.int32),
    feature=np.concatenate(feats).astype(np.int32),
    threshold=np.concatenate(thrs).astype(np.float64),
    value=np.concatenate(vals),
)
print(f"OK: {dst} ({dst.stat().st_size / 1e6:.1f} MB), {len(roots)} pohon, {offset} node")
