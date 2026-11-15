
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ============================================================
# ROOT PROJECT
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from signtalk.paths import DATASET_PATH
from signtalk.features import FEATURE_COLUMNS

# ============================================================
# AUDIT DATASET
# ============================================================

print("=" * 65)
print("AUDIT DATASET SIGNTALK")
print("=" * 65)

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset tidak ditemukan: {DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

if "label" not in df.columns:
    raise ValueError("Kolom label tidak ditemukan.")

print("\n1. INFORMASI DATASET")
print("File          :", DATASET_PATH)
print("Jumlah baris  :", len(df))
print("Jumlah kolom  :", len(df.columns))
print("Jumlah kelas  :", df["label"].nunique())
print("Kolom fitur   :", len(FEATURE_COLUMNS))

# ============================================================
# VALIDASI KOLOM
# ============================================================

missing = [
    col for col in FEATURE_COLUMNS
    if col not in df.columns
]

print("Kolom hilang  :", missing)

if missing:
    raise ValueError("Kolom fitur tidak lengkap.")

# ============================================================
# JUMLAH DATA PER KELAS
# ============================================================

labels = df["label"].astype(str).str.strip()
counts = labels.value_counts()

print("\n2. JUMLAH DATA PER KELAS")
print(counts.sort_index().to_string())

print("\nStatistik jumlah sampel:")
print("Terbanyak :", counts.max())
print("Tersedikit:", counts.min())
print("Rata-rata :", round(counts.mean(), 2))
print("Median    :", round(counts.median(), 2))

print("\nKelas dengan data paling sedikit:")
print(counts.sort_values().head(15).to_string())

# ============================================================
# POLA URUTAN LABEL
# ============================================================

print("\n3. POLA URUTAN LABEL")

changes = labels.ne(labels.shift()).sum()

print("Jumlah blok label:", changes)
print("Jumlah kelas     :", labels.nunique())

runs = (
    labels.ne(labels.shift())
    .groupby(labels)
    .sum()
    .sort_values(ascending=False)
)

print("\nJumlah blok per kelas:")
print(runs.to_string())

# ============================================================
# DUPLIKASI DAN NILAI FITUR
# ============================================================

print("\n4. PEMERIKSAAN FITUR")

X = df[FEATURE_COLUMNS].apply(
    pd.to_numeric,
    errors="coerce"
)

print("Nilai kosong:", int(X.isna().sum().sum()))

X_array = X.to_numpy(dtype=np.float64)

print(
    "Nilai inf:",
    int(np.isinf(X_array).sum())
)

print(
    "Fitur duplikat persis:",
    int(X.duplicated().sum())
)

# ============================================================
# KETIDAKSEIMBANGAN DATA
# ============================================================

print("\n5. ANALISIS KETIDAKSEIMBANGAN")

imbalance_ratio = counts.max() / counts.min()

print("Rasio kelas terbanyak/tersedikit:",
      round(imbalance_ratio, 2))

if imbalance_ratio >= 3:
    print("PERINGATAN: Ketimpangan jumlah data cukup tinggi.")
else:
    print("Jumlah data relatif lebih merata.")

# ============================================================
# RINGKASAN
# ============================================================

print("\n6. RINGKASAN")

if runs.max() == 1:
    print("Pola label: Setiap kelas muncul dalam satu blok.")
else:
    print("Pola label: Ada kelas yang muncul dalam beberapa blok.")

print("Total kelas:", labels.nunique())
print("Total data :", len(df))

print("\nAudit selesai. Dataset tidak diubah.")
print("=" * 65)
