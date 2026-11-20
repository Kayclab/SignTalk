"""
scripts/generate_hand_shapes.py

Membuat bentuk tangan untuk kartu Kamus/Game dari dataset landmark.

Dataset kita bukan foto, tapi koordinat 21 titik sendi (hasil MediaPipe).
Script ini mengambil SATU sampel paling "tipikal" (medoid) untuk tiap huruf/
angka/kata, lalu menyimpannya ke public/static/js/hand-shapes.js. File itu dibaca
generateHandIllustrationSVG() di features-common.js untuk menggambar tangan
berwarna palet SignTalk di kartu.

Jalankan ulang hanya jika dataset berubah:
    python scripts/generate_hand_shapes.py
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset" / "dataset_tangan.csv"
OUTPUT = ROOT / "public" / "static" / "js" / "hand-shapes.js"
FEATURES_JS = ROOT / "public" / "static" / "js" / "features-common.js"

HAND_FEATURES = 63


def kamus_labels():
    """Ambil daftar char dari KAMUS_DATA supaya hanya label valid yang dibuat."""
    text = FEATURES_JS.read_text(encoding="utf-8")
    return re.findall(r"\{ char: '([^']+)', type:", text)


def medoid(block):
    """Baris yang paling dekat ke median semua sampel (bentuk tipikal)."""
    median = np.median(block, axis=0)
    distance = np.linalg.norm(block - median, axis=1)
    return block[int(np.argmin(distance))]


def to_points(vector):
    # (21,3) -> [[x, y, z], ...] dibulatkan 3 desimal
    return np.round(vector.reshape(21, 3), 3).tolist()


def main():
    df = pd.read_csv(DATASET, low_memory=False)
    feature_cols = list(df.columns[1:127])
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=feature_cols)

    shapes = {}
    for label in kamus_labels():
        block = df.loc[df["label"].astype(str) == label, feature_cols].to_numpy(
            dtype=np.float64
        )
        if len(block) == 0:
            print(f"[SKIP] {label}: tidak ada di dataset")
            continue

        sample = medoid(block)
        hands = []
        for start in (0, HAND_FEATURES):
            vector = sample[start:start + HAND_FEATURES]
            if np.max(np.abs(vector)) > 1e-9:  # slot kosong = nol semua
                hands.append(to_points(vector))
        shapes[label] = hands
        print(f"[OK] {label}: {len(block)} sampel, {len(hands)} tangan")

    OUTPUT.write_text(
        "// Dibuat otomatis oleh scripts/generate_hand_shapes.py - jangan edit manual.\n"
        "const HAND_SHAPES = "
        + json.dumps(shapes, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    print(f"\nTersimpan: {OUTPUT} ({len(shapes)} label)")


if __name__ == "__main__":
    main()
