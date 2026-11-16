
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "dataset_v2.csv"
MODEL_DIR = ROOT / "model"

OUTPUT_MODEL = MODEL_DIR / "random_forest_v5.pkl"
BACKUP_V4 = MODEL_DIR / "random_forest_v4_backup.pkl"

# Baca dataset
df = pd.read_csv(DATASET)
X = df.drop(columns=["label"]).to_numpy(dtype=np.float32)
y = df["label"].astype(str).to_numpy()

assert X.shape[1] == 126, "Jumlah fitur harus 126."

# Pisahkan data untuk evaluasi
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Berikan bobot lebih besar pada angka 5
weights = {str(label): 1.0 for label in np.unique(y)}
weights["5"] = 2.0

model = RandomForestClassifier(
    n_estimators=500,
    max_features="sqrt",
    class_weight=weights,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)

print("Melatih model V5...")
model.fit(X_train, y_train)

pred = model.predict(X_test)

print("\nHASIL EVALUASI V5")
print(classification_report(
    y_test, pred,
    labels=["5", "Bisa"],
    zero_division=0
))

print("CONFUSION MATRIX")
print(confusion_matrix(
    y_test, pred,
    labels=["5", "Bisa"]
))

# Latih model final menggunakan seluruh dataset
print("\nMelatih model final menggunakan seluruh dataset...")
model.fit(X, y)

# Simpan V5 sebagai file baru
joblib.dump(model, OUTPUT_MODEL)

print("\nMODEL V5 BERHASIL DISIMPAN")
print(OUTPUT_MODEL)

c