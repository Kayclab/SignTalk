"""
DEBUG_COMPARE.PY
================

Skrip ini membandingkan fitur yang tertangkap dari kamera (dari debug_features.log)
dengan fitur yang ada di dataset untuk label tertentu.

CARA PAKAI:
1. Jalankan debug_features.py
2. Di kamera, coba isyarat huruf "A" selama 5 detik
3. Hentikan kamera
4. Jalankan: python debug_compare.py
5. Lihat output yang membandingkan rata-rata fitur A dari kamera vs dataset

"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FEATURES_LOG = BASE_DIR / "debug_features.log"
DATASET_PATH = BASE_DIR / "dataset" / "dataset_tangan.csv"

if not FEATURES_LOG.exists():
    print(f"[ERROR] File {FEATURES_LOG} tidak ditemukan.")
    print("        Jalankan debug_features.py terlebih dahulu dan coba isyarat di kamera.")
    exit(1)

if not DATASET_PATH.exists():
    print(f"[ERROR] Dataset tidak ditemukan di {DATASET_PATH}")
    exit(1)

print("[INFO] Membaca fitur dari kamera...")
import ast
camera_features = []
with open(FEATURES_LOG, "r") as f:
    for line in f:
        try:
            # Setiap baris adalah representasi array numpy sebagai string
            # Konversi menjadi array
            line = line.strip()
            if line:
                arr = np.array(ast.literal_eval(line), dtype=np.float32)
                if len(arr) == 126:
                    camera_features.append(arr)
        except Exception as e:
            pass

if not camera_features:
    print("[ERROR] Tidak ada fitur valid di log file.")
    print("        Pastikan kamera dapat mendeteksi tangan dan isyarat berlangsung cukup lama.")
    exit(1)

camera_features = np.array(camera_features)
print(f"[OK] Membaca {len(camera_features)} frame dari kamera")

print("\n[INFO] Membaca dataset...")
df = pd.read_csv(DATASET_PATH)
X = df.drop(columns=["label"]).to_numpy(np.float32)
y = df["label"].astype(str).to_numpy()

print(f"[OK] Dataset berisi {len(df)} sampel, {y.nunique()} kelas")

# Perbandingan untuk beberapa label
print("\n" + "="*70)
print("PERBANDINGAN STATISTIK FITUR")
print("="*70)

labels_to_check = ["A", "B", "C", "D"]
for label in labels_to_check:
    print(f"\nLabel: {label}")
    print("-" * 70)

    # Ambil data dari dataset untuk label ini
    mask = (y == label)
    if not mask.any():
        print(f"  [SKIP] Label '{label}' tidak ada di dataset")
        continue

    dataset_samples = X[mask]

    print(f"  Dataset ({len(dataset_samples)} sampel):")
    print(f"    Min per fitur  (median): {np.median(dataset_samples.min(axis=0)):.6f}")
    print(f"    Max per fitur  (median): {np.median(dataset_samples.max(axis=0)):.6f}")
    print(f"    Mean           (median): {np.median(dataset_samples.mean(axis=0)):.6f}")
    print(f"    Std            (median): {np.median(dataset_samples.std(axis=0)):.6f}")

    print(f"\n  Kamera ({len(camera_features)} frame):")
    print(f"    Min per fitur  (median): {np.median(camera_features.min(axis=1)):.6f}")
    print(f"    Max per fitur  (median): {np.median(camera_features.max(axis=1)):.6f}")
    print(f"    Mean           (median): {np.median(camera_features.mean(axis=1)):.6f}")
    print(f"    Std            (median): {np.median(camera_features.std(axis=1)):.6f}")

    # Hitung jarak Euclidean rata-rata antara kamera dan dataset
    dataset_mean = dataset_samples.mean(axis=0)
    camera_mean = camera_features.mean(axis=0)
    euclidean = np.sqrt(np.sum((camera_mean - dataset_mean) ** 2))
    print(f"\n  Jarak Euclidean (fitur kamera vs rata-rata dataset): {euclidean:.4f}")

    # Jika jarak besar, ada perbedaan signifikan
    if euclidean > 0.5:
        print(f"  ⚠️  JARAK BESAR! Ada perbedaan signifikan antara kamera dan dataset")
        print(f"      Kemungkinan penyebab:")
        print(f"      - Normalisasi fitur berbeda saat training vs inference")
        print(f"      - Versi MediaPipe berbeda")
        print(f"      - Dataset dibuat dengan cermin/flip berbeda")
    else:
        print(f"  ✓ Jarak wajar, fitur dari kamera cocok dengan dataset")

print("\n" + "="*70)
print("\nCATATAN:")
print("Jika semua label menunjukkan jarak besar, masalahnya sistemik (normalisasi).")
print("Jika hanya beberapa label, masalahnya mungkin di teknik isyarat saat di kamera.")
