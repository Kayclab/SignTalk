"""
train_model.py
Melatih Random Forest dengan evaluasi yang jujur:
  - split BERBASIS BLOK (bukan acak) agar frame kembar tidak bocor ke data uji
  - membandingkan model tanpa augmentasi vs dengan augmentasi
  - menguji ketahanan: tangan kedua hilang, slot tertukar
Model lama TIDAK ditimpa. Hasil disimpan sebagai model/random_forest_v2.pkl

Pemakaian:  python train_model.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from features import (
    EXPECTED_FEATURES,
    FEATURE_COLUMNS,
    FEATURE_VERSION,
    HAND_FEATURES,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "dataset_v2.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "random_forest_v2.pkl"
META_PATH = MODEL_DIR / "model_meta.json"

RANDOM_STATE = 42
TEST_FRACTION = 0.20      # bagian ujung tiap label dipakai sebagai uji
GAP_ROWS = 30             # jeda antara data latih dan uji (anti-bocor)
RF_PARAMS = dict(
    n_estimators=200,
    max_features="sqrt",
    min_samples_leaf=2,
    n_jobs=-1,
    random_state=RANDOM_STATE,
)

# ------------------------------------------------------------
# 1. DATASET
# ------------------------------------------------------------
print("=" * 62)
print("  SIGNTALK TRAINING (fitur " + FEATURE_VERSION + ")")
print("=" * 62)

if not DATASET_PATH.exists():
    raise SystemExit(
        "[ERROR] dataset/dataset_v2.csv belum ada. "
        "Jalankan dulu: python prepare_dataset.py"
    )

df = pd.read_csv(DATASET_PATH)
missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
if missing or "label" not in df.columns:
    raise SystemExit("[ERROR] Kolom dataset tidak sesuai standar v2.")

X = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="raise").to_numpy(np.float32)
y = df["label"].astype(str).str.strip().to_numpy()

if not np.isfinite(X).all():
    raise SystemExit("[ERROR] Dataset berisi NaN/inf.")
if (y == "").any():
    raise SystemExit("[ERROR] Ada label kosong.")

counts = pd.Series(y).value_counts()
print(f"Sampel : {len(y)} | Kelas : {len(counts)} | "
      f"min/max per kelas : {counts.min()} / {counts.max()}")
if counts.min() < 100:
    print("[PERINGATAN] Kelas dengan < 100 sampel:",
          counts[counts < 100].to_dict())

two_hand_ratio = (np.abs(X[:, HAND_FEATURES:]).sum(axis=1) > 0).mean()
print(f"Baris dua tangan : {two_hand_ratio * 100:.1f}%")

# ------------------------------------------------------------
# 2. SPLIT BERBASIS BLOK
# ------------------------------------------------------------
index = np.arange(len(y))
train_mask = np.zeros(len(y), dtype=bool)
test_mask = np.zeros(len(y), dtype=bool)

for label in np.unique(y):
    rows = index[y == label]
    cut = int(len(rows) * (1 - TEST_FRACTION))
    train_mask[rows[: max(cut - GAP_ROWS, 1)]] = True
    test_mask[rows[cut:]] = True

X_train, y_train = X[train_mask], y[train_mask]
X_test, y_test = X[test_mask], y[test_mask]
print(f"Latih  : {len(y_train)} | Uji (blok terpisah) : {len(y_test)}")


# ------------------------------------------------------------
# 3. AUGMENTASI & UTILITAS
# ------------------------------------------------------------
def has_two(A):
    return np.abs(A[:, HAND_FEATURES:]).sum(axis=1) > 0


def swap_slots(A):
    return np.hstack([A[:, HAND_FEATURES:], A[:, :HAND_FEATURES]])


def drop_one_hand(A, rng):
    """Simulasi satu tangan gagal terdeteksi (tangan yang tersisa -> slot 1)."""
    rows = np.where(has_two(A))[0]
    out = A[rows].copy()
    keep_second = rng.random(len(rows)) < 0.5
    first, second = A[rows, :HAND_FEATURES], A[rows, HAND_FEATURES:]
    out[:, :HAND_FEATURES] = np.where(keep_second[:, None], second, first)
    out[:, HAND_FEATURES:] = 0
    return out, rows


def augment(A, labels, seed):
    rng = np.random.default_rng(seed)
    rows = np.where(has_two(A))[0]
    dropped, drop_rows = drop_one_hand(A, rng)
    return (
        np.vstack([A, swap_slots(A[rows]), dropped]),
        np.concatenate([labels, labels[rows], labels[drop_rows]]),
    )


def balanced_weights(labels):
    names, freq = np.unique(labels, return_counts=True)
    weight = dict(zip(names, len(labels) / (len(names) * freq)))
    return np.array([weight[v] for v in labels])


def fit(A, labels):
    model = RandomForestClassifier(**RF_PARAMS)
    model.fit(A, labels, sample_weight=balanced_weights(labels))
    return model


# set uji ketahanan
rng_test = np.random.default_rng(7)
X_dropped, dropped_rows = drop_one_hand(X_test, rng_test)
y_dropped = y_test[dropped_rows]
two_rows = np.where(has_two(X_test))[0]
X_swapped, y_swapped = swap_slots(X_test[two_rows]), y_test[two_rows]


def evaluate(name, model):
    pred = model.predict(X_test)
    result = {
        "model": name,
        "akurasi_uji_blok": accuracy_score(y_test, pred),
        "macro_f1": f1_score(y_test, pred, average="macro", zero_division=0),
        "akurasi_jika_1_tangan_hilang": accuracy_score(y_dropped, model.predict(X_dropped)),
        "akurasi_jika_slot_tertukar": accuracy_score(y_swapped, model.predict(X_swapped)),
    }
    print(f"\n[{name}]")
    print(f"  Akurasi uji (blok)            : {result['akurasi_uji_blok'] * 100:6.2f}%")
    print(f"  Macro F1                      : {result['macro_f1'] * 100:6.2f}%")
    print(f"  Jika satu tangan gagal deteksi: {result['akurasi_jika_1_tangan_hilang'] * 100:6.2f}%")
    print(f"  Jika slot tangan tertukar     : {result['akurasi_jika_slot_tertukar'] * 100:6.2f}%")
    return result, pred


# ------------------------------------------------------------
# 4. BASELINE vs MODEL BARU
# ------------------------------------------------------------
print("\n[INFO] Melatih baseline (tanpa augmentasi)...")
baseline = fit(X_train, y_train)
base_result, _ = evaluate("BASELINE tanpa augmentasi", baseline)

print("\n[INFO] Melatih model baru (dengan augmentasi)...")
X_aug, y_aug = augment(X_train, y_train, RANDOM_STATE)
candidate = fit(X_aug, y_aug)
new_result, new_pred = evaluate("MODEL BARU dengan augmentasi", candidate)

# ------------------------------------------------------------
# 5. LAPORAN DETAIL
# ------------------------------------------------------------
labels_sorted = sorted(np.unique(y))
cm = confusion_matrix(y_test, new_pred, labels=labels_sorted)
pd.DataFrame(cm, index=labels_sorted, columns=labels_sorted).to_csv(
    MODEL_DIR / "confusion_matrix_v2.csv"
)
report = classification_report(
    y_test, new_pred, output_dict=True, zero_division=0
)
pd.DataFrame(report).transpose().to_csv(MODEL_DIR / "classification_report_v2.csv")
pd.DataFrame([base_result, new_result]).to_csv(
    MODEL_DIR / "perbandingan_model.csv", index=False
)

per_class = (
    pd.DataFrame({"benar": new_pred == y_test, "label": y_test})
    .groupby("label")["benar"].mean().sort_values()
)
print("\n10 kelas terlemah (data uji blok):")
for name, value in per_class.head(10).items():
    print(f"  {name:<16s} {value * 100:6.2f}%")

errors = pd.Series(
    list(zip(y_test[new_pred != y_test], new_pred[new_pred != y_test]))
).value_counts().head(8)
print("\nKesalahan tertukar terbanyak (benar -> prediksi):")
for (truth, guess), total in errors.items():
    print(f"  {truth:<16s} -> {guess:<16s} {total}x")

# ------------------------------------------------------------
# 6. MODEL FINAL: latih ulang dengan SEMUA data, simpan
# ------------------------------------------------------------
print("\n[INFO] Melatih model final dengan seluruh data...")
X_all_aug, y_all_aug = augment(X, y, RANDOM_STATE)
final_model = fit(X_all_aug, y_all_aug)

assert final_model.n_features_in_ == EXPECTED_FEATURES
joblib.dump(final_model, MODEL_PATH, compress=3)

META_PATH.write_text(json.dumps({
    "feature_version": FEATURE_VERSION,
    "n_features": EXPECTED_FEATURES,
    "classes": [str(c) for c in final_model.classes_],
    "trained_at": datetime.now().isoformat(timespec="seconds"),
    "samples": int(len(y)),
    "blocked_test_accuracy": round(float(new_result["akurasi_uji_blok"]), 4),
}, indent=2), encoding="utf-8")

print("\n" + "=" * 62)
print("  SELESAI")
print("=" * 62)
print("Model baru :", MODEL_PATH)
print("Meta       :", META_PATH)
print(f"Akurasi uji blok (jujur): {new_result['akurasi_uji_blok'] * 100:.2f}%")
print("Model lama di folder model/ tidak diubah.")