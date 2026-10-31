
import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# 1. Membaca dataset
df = pd.read_csv("dataset/dataset_tangan.csv")

X = df.drop(columns=["label"])
y = df["label"].astype(str)

print("Jumlah data:", len(df))
print("Jumlah fitur:", X.shape[1])
print("Jumlah kelas:", y.nunique())

# 2. Membagi data menjadi data latih dan data uji
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nJumlah data latih:", len(X_train))
print("Jumlah data uji:", len(X_test))

# 3. Membuat model Random Forest
# Menghitung bobot setiap kelas secara manual
from sklearn.utils.class_weight import compute_sample_weight

sample_weights = compute_sample_weight(
    class_weight="balanced",
    y=y_train.to_numpy()
)

# Membuat model Random Forest
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight=None,
    n_jobs=-1
)

# 4. Melatih model
print("\nSedang melatih model...")
model.fit(
    X_train,
    y_train,
    sample_weight=sample_weights
)

# 5. Melakukan prediksi
y_pred = model.predict(X_test)

# 6. Evaluasi model
accuracy = accuracy_score(y_test, y_pred)

print("\n" + "=" * 50)
print("HASIL EVALUASI MODEL")
print("=" * 50)

print(f"Akurasi: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

# 7. Menyimpan model
os.makedirs("model", exist_ok=True)

joblib.dump(model, "model/random_forest.pkl")

print("\nModel berhasil disimpan!")
print("Lokasi: model/random_forest.pkl")

# 8. Menyimpan confusion matrix
cm = confusion_matrix(
    y_test,
    y_pred,
    labels=model.classes_
)

cm_df = pd.DataFrame(
    cm,
    index=model.classes_,
    columns=model.classes_
)

cm_df.to_csv("model/confusion_matrix.csv")

print("Confusion matrix berhasil disimpan!")