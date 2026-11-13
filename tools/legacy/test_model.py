
"""tools/legacy/test_model.py - uji 1 sampel dengan model lama.
CATATAN: skrip LAMA (v1), tidak memakai signtalk/features.py.
"""

from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]  # root proyek

# 1. Memuat model yang sudah dilatih
model = joblib.load(BASE_DIR / "model" / "random_forest.pkl")

print("Model berhasil dimuat!")
print("Jumlah kelas:", len(model.classes_))
print("Daftar kelas:", model.classes_)

# 2. Mengambil satu sampel dari dataset
df = pd.read_csv(BASE_DIR / "dataset" / "dataset_tangan.csv")

sample = df.iloc[[0], 1:]
actual_label = str(df.iloc[0]["label"])

# 3. Melakukan prediksi
prediction = model.predict(sample)[0]

print("\n" + "=" * 40)
print("PENGUJIAN PREDIKSI")
print("=" * 40)

print("Label sebenarnya :", actual_label)
print("Hasil prediksi   :", prediction)

if actual_label == prediction:
    print("Status           : BENAR")
else:
    print("Status           : SALAH")
