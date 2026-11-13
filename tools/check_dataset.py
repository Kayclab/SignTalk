"""
tools/check_dataset.py - ringkasan kualitas dataset v2 per label.

Pemakaian (dari root proyek):  python tools/check_dataset.py
"""

import sys
from pathlib import Path

# root proyek -> agar `import signtalk` berfungsi saat dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from signtalk.features import FEATURE_COLUMNS, HAND_FEATURES
from signtalk.paths import DATASET_PATH

df = pd.read_csv(DATASET_PATH)
X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
two = np.abs(X[:, HAND_FEATURES:]).sum(axis=1) > 0

print("Total data      :", len(df))
print("Jumlah fitur    :", X.shape[1])
print("Data kosong     :", int(df.isnull().sum().sum()))
print("Baris duplikat  :", int(df[FEATURE_COLUMNS].duplicated().sum()))
print("Skala per tangan 1.0 semua:",
      bool(np.allclose(np.abs(X[:, :HAND_FEATURES]).max(axis=1), 1.0, atol=1e-3)))

summary = pd.DataFrame({
    "jumlah": df["label"].value_counts(),
    "persen_dua_tangan": (
        pd.Series(two, index=df["label"]).groupby(level=0).mean() * 100
    ).round(0),
}).sort_values("jumlah")
print("\nPer label (dari yang tersedikit):")
print(summary.to_string())
print("\nCatatan: label dengan jumlah < 150 sebaiknya ditambah datanya.")