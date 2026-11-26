"""
Ekspor MLPClassifier scikit-learn (.pkl) ke .npz untuk server ringan (numpy murni).

Pemakaian:  python scripts/export_mlp_npz.py model/mlp_v8.pkl model/mlp_v8.npz
"""

import sys
from pathlib import Path

import joblib
import numpy as np

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
m = joblib.load(src)
assert len(m.coefs_) == 3 and m.activation == "relu", "bentuk MLP tidak didukung NumpyMLP"
np.savez_compressed(
    dst,
    classes=np.asarray(m.classes_).astype(str),
    n_features=np.int64(m.n_features_in_),
    W0=m.coefs_[0].astype(np.float32), b0=m.intercepts_[0].astype(np.float32),
    W1=m.coefs_[1].astype(np.float32), b1=m.intercepts_[1].astype(np.float32),
    W2=m.coefs_[2].astype(np.float32), b2=m.intercepts_[2].astype(np.float32),
)
print(f"OK: {dst} ({dst.stat().st_size / 1e6:.2f} MB), {len(m.classes_)} kelas")
