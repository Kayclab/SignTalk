
import sys
from pathlib import Path

# Tambahkan root folder SignTalk ke Python path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from signtalk.paths import DATASET_PATH

print("=" * 75)
print("RINCIAN BLOK DATASET SIGNTALK")
print("=" * 75)

df = pd.read_csv(DATASET_PATH)
labels = df["label"].astype(str).str.strip()

# Identifikasi pergantian label
block_id = labels.ne(labels.shift()).cumsum()

blocks = pd.DataFrame({
    "baris": range(len(df)),
    "label": labels,
    "blok": block_id
})

summary = (
    blocks.groupby(["blok", "label"])
    .agg(
        baris_awal=("baris", "min"),
        baris_akhir=("baris", "max"),
        jumlah_sampel=("baris", "count")
    )
    .reset_index()
)

print(summary.to_string(index=False))

print("\nJumlah seluruh blok:", len(summary))

print("\nJumlah blok per kelas:")
print(
    summary.groupby("label")
    .size()
    .sort_values(ascending=False)
    .to_string()
)

output_path = ROOT_DIR / "dataset" / "audit_blocks.csv"
summary.to_csv(output_path, index=False)

print("\nFile tersimpan:", output_path)
print("\nAudit selesai. Dataset asli tidak diubah.")
