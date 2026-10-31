
import joblib
import pandas as pd

# 1. Memuat model yang sudah dilatih
model = joblib.load("model/random_forest.pkl")

print("Model berhasil dimuat!")
print("Jumlah kelas:", len(model.classes_))
print("Daftar kelas:", model.classes_)

# 2. Mengambil satu sampel dari dataset
df = pd.read_csv("dataset/dataset_tangan.csv")

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
