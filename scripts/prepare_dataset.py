"""
prepare_dataset.py
Mengonversi dataset lama menjadi dataset standar v2 TANPA mengubah
file asli. Aman dijalankan berulang kali.

Pemakaian (dari root proyek):
    python scripts/prepare_dataset.py
    python scripts/prepare_dataset.py dataset/dataset_tangan.csv
"""

import csv
import sys
from pathlib import Path

# root proyek -> agar `import signtalk` berfungsi saat dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collections import Counter

import numpy as np

from signtalk.features import (
    EXPECTED_FEATURES,
    FEATURE_COLUMNS,
    legacy_rows_to_v2,
)

from signtalk.paths import (
    DATASET_PATH as OUTPUT,
    LEGACY_DATASET_PATH,
    REJECTED_ROWS_PATH as REPORT_REJECT,
)

SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else LEGACY_DATASET_PATH

if not SOURCE.exists():
    raise SystemExit(f"[ERROR] File tidak ditemukan: {SOURCE}")

print("=" * 60)
print("  PREPARE DATASET -> v2")
print("=" * 60)
print("Sumber :", SOURCE)

old_rows, old_labels = [], []      # format lama: label di kolom pertama
mirror_rows, mirror_labels = [], []  # format collector lama: label terakhir
rejected = []

with open(SOURCE, newline="", encoding="utf-8") as file:
    reader = csv.reader(file)
    header = next(reader)
    for number, row in enumerate(reader, start=2):
        if len(row) != EXPECTED_FEATURES + 1:
            rejected.append((number, "jumlah kolom salah", row[:1]))
            continue
        try:
            if "." in row[0]:
                # label di kolom terakhir (hasil scripts/collect_data.py lama)
                values = np.array(row[:EXPECTED_FEATURES], dtype=np.float64)
                label = row[-1].strip()
                kind = "terakhir"
            else:
                values = np.array(row[1:], dtype=np.float64)
                label = row[0].strip()
                kind = "pertama"
        except ValueError:
            rejected.append((number, "nilai non-numerik", row[:1]))
            continue

        if not label or not np.isfinite(values).all():
            rejected.append((number, "label kosong / nilai tidak valid", row[:1]))
            continue

        if kind == "pertama":
            old_rows.append(values)
            old_labels.append(label)
        else:
            top = max(
                np.abs(values[:63]).max(), np.abs(values[63:]).max()
            )
            if abs(top - 1.0) > 1e-3:
                rejected.append((number, "format label-terakhir tak dikenal", [label]))
                continue
            mirror_rows.append(values)
            mirror_labels.append(label)

print(f"Baris format lama (label di depan)        : {len(old_rows)}")
print(f"Baris format collector lama (label di belakang, TANPA flip): {len(mirror_rows)}")
print(f"Baris ditolak                              : {len(rejected)}")

parts, labels = [], []
if old_rows:
    parts.append(legacy_rows_to_v2(np.array(old_rows), mirror=False))
    labels += old_labels
if mirror_rows:
    # direkam tanpa flip -> cerminkan agar searah dengan data lama
    parts.append(legacy_rows_to_v2(np.array(mirror_rows), mirror=True))
    labels += mirror_labels

if not parts:
    raise SystemExit("[ERROR] Tidak ada baris valid.")

features = np.vstack(parts)

with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(FEATURE_COLUMNS + ["label"])
    for vector, label in zip(features, labels):
        writer.writerow([f"{v:.6f}" for v in vector] + [label])

if rejected:
    with open(REPORT_REJECT, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["nomor_baris_sumber", "alasan", "label_atau_awal"])
        for item in rejected:
            writer.writerow([item[0], item[1], item[2]])
    print("Baris ditolak dicatat di:", REPORT_REJECT)

counts = Counter(labels)
print(f"\nTotal baris v2 : {len(labels)}")
print(f"Jumlah kelas   : {len(counts)}")
print(f"Terkecil/terbesar: {min(counts.values())} / {max(counts.values())}")
print("Hasil         :", OUTPUT)
print("File asli tidak diubah.")
