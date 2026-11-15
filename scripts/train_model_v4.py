
"""
SIGNTALK - RANDOM FOREST V4
Training model baru tanpa menimpa model V2 dan V3.

Sumber:
1. dataset/dataset_v2.csv
2. dataset/dataset_test_independent.csv

CATATAN:
Dataset webcam sudah pernah dipakai untuk evaluasi V2/V3.
Setelah dimasukkan ke training V4, dataset tersebut bukan lagi
testing independen. Pengujian final V4 harus memakai data baru.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from signtalk.features import (
    FEATURE_COLUMNS,
    FEATURE_VERSION,
    EXPECTED_FEATURES,
    HAND_FEATURES
)

from signtalk.paths import DATASET_PATH, MODEL_DIR

# ============================================================
# KONFIGURASI
# ============================================================

WEBCAM_PATH = ROOT_DIR / "dataset" / "dataset_test_independent.csv"

MODEL_PATH_V4 = MODEL_DIR / "random_forest_v4.pkl"
META_PATH_V4 = MODEL_DIR / "model_v4_meta.json"

RANDOM_STATE = 42
VALIDATION_FRACTION = 0.20
GAP_ROWS = 10

RF_PARAMS = {
    "n_estimators": 400,
    "max_features": "sqrt",
    "min_samples_leaf": 1,
    "class_weight": "balanced_subsample",
    "n_jobs": -1,
    "random_state": RANDOM_STATE
}

JITTER_STD = 0.008
ROTATION_MAX = 0.035

# ============================================================
# LOAD DATASET
# ============================================================

def load_data(path, name):

    if not path.exists():
        raise SystemExit(f"[ERROR] File tidak ditemukan: {path}")

    df = pd.read_csv(path)

    missing = [
        col for col in FEATURE_COLUMNS + ["label"]
        if col not in df.columns
    ]

    if missing:
        raise SystemExit(
            f"[ERROR] Kolom tidak ditemukan pada {name}: {missing}"
        )

    X = df[FEATURE_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce"
    ).to_numpy(dtype=np.float32)

    y = df["label"].astype(str).str.strip().to_numpy()

    if not np.isfinite(X).all():
        raise SystemExit(f"[ERROR] NaN/inf ditemukan pada {name}")

    if (y == "").any():
        raise SystemExit(f"[ERROR] Label kosong pada {name}")

    print(
        f"{name}: {len(y):,} sampel | "
        f"{len(np.unique(y))} kelas"
    )

    return X, y


# ============================================================
# BLOCK SPLIT
# ============================================================

def blocked_split(X, y, source):

    train_indices = []
    val_indices = []

    for label in np.unique(y):

        indices = np.flatnonzero(y == label)
        n = len(indices)

        if n < 10:
            train_indices.extend(indices.tolist())
            print(
                f"[PERINGATAN] {source}: kelas {label} "
                f"hanya {n} sampel; tidak divalidasi."
            )
            continue

        val_count = max(
            1,
            int(round(n * VALIDATION_FRACTION))
        )

        split_point = n - val_count
        train_end = max(1, split_point - GAP_ROWS)

        train_indices.extend(indices[:train_end].tolist())
        val_indices.extend(indices[split_point:].tolist())

    train_indices = np.array(sorted(train_indices))
    val_indices = np.array(sorted(val_indices))

    print(
        f"{source} -> Training: {len(train_indices):,} | "
        f"Validation: {len(val_indices):,}"
    )

    return train_indices, val_indices


# ============================================================
# AUGMENTASI AMAN
# ============================================================

def augment_sample(features, rng):

    output = features.copy()

    for slot in range(2):

        start = slot * HAND_FEATURES
        end = start + HAND_FEATURES

        hand = output[start:end]

        # Jangan memberikan noise pada slot tangan kosong.
        if np.abs(hand).sum() < 1e-8:
            continue

        hand = hand.reshape(21, 3).copy()

        # Rotasi kecil pada koordinat X dan Y.
        angle = rng.uniform(
            -ROTATION_MAX,
            ROTATION_MAX
        )

        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        x = hand[:, 0].copy()
        y = hand[:, 1].copy()

        hand[:, 0] = x * cos_a - y * sin_a
        hand[:, 1] = x * sin_a + y * cos_a

        # Noise ringan hanya pada tangan yang terdeteksi.
        noise = rng.normal(
            0,
            JITTER_STD,
            size=hand.shape
        )

        hand += noise.astype(np.float32)

        output[start:end] = hand.flatten()

    return np.clip(output, -1, 1)


def augment_training(X, y):

    rng = np.random.default_rng(RANDOM_STATE)

    augmented = []

    for row in X:
        augmented.append(
            augment_sample(row, rng)
        )

    X_aug = np.vstack([
        X,
        np.asarray(augmented, dtype=np.float32)
    ])

    y_aug = np.concatenate([y, y.copy()])

    return X_aug, y_aug


# ============================================================
# MAIN TRAINING
# ============================================================

def main():

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("SIGNTALK RANDOM FOREST V4")
    print("=" * 65)

    if MODEL_PATH_V4.exists():

        answer = input(
            "Model V4 sudah ada. Ganti model V4 tersebut? (y/n): "
        ).strip().lower()

        if answer != "y":
            print("Training dibatalkan.")
            return

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    X_old, y_old = load_data(
        DATASET_PATH,
        "Dataset training lama"
    )

    X_web, y_web = load_data(
        WEBCAM_PATH,
        "Dataset webcam"
    )

    old_classes = set(y_old)
    web_classes = set(y_web)

    unknown = sorted(web_classes - old_classes)

    if unknown:
        raise SystemExit(
            "[ERROR] Label webcam tidak ada pada dataset training: "
            + str(unknown)
        )

    missing_web = sorted(old_classes - web_classes)

    if missing_web:
        print(
            "[PERINGATAN] Label tanpa data webcam:",
            missing_web
        )

    # --------------------------------------------------------
    # SPLIT SETIAP SUMBER DATA SECARA TERPISAH
    # --------------------------------------------------------

    old_train, old_val = blocked_split(
        X_old, y_old, "Dataset lama"
    )

    web_train, web_val = blocked_split(
        X_web, y_web, "Dataset webcam"
    )

    X_train = np.vstack([
        X_old[old_train],
        X_web[web_train]
    ])

    y_train = np.concatenate([
        y_old[old_train],
        y_web[web_train]
    ])

    val_X = []
    val_y = []

    if len(old_val):
        val_X.append(X_old[old_val])
        val_y.append(y_old[old_val])

    if len(web_val):
        val_X.append(X_web[web_val])
        val_y.append(y_web[web_val])

    X_val = np.vstack(val_X)
    y_val = np.concatenate(val_y)

    print("\nRINGKASAN DATA")
    print("Training   :", len(y_train))
    print("Validation :", len(y_val))
    print("Kelas      :", len(np.unique(y_train)))

    # --------------------------------------------------------
    # AUGMENTASI TRAINING SAJA
    # --------------------------------------------------------

    X_aug, y_aug = augment_training(
        X_train,
        y_train
    )

    print("Training setelah augmentasi:", len(y_aug))

    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    print("\n[INFO] Training Random Forest V4...")

    model = RandomForestClassifier(**RF_PARAMS)

    model.fit(X_aug, y_aug)

    print("[INFO] Training selesai.")

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    prediction = model.predict(X_val)

    accuracy = accuracy_score(y_val, prediction)

    macro_f1 = f1_score(
        y_val,
        prediction,
        average="macro",
        zero_division=0
    )

    weighted_f1 = f1_score(
        y_val,
        prediction,
        average="weighted",
        zero_division=0
    )

    print("\nHASIL VALIDATION V4")
    print(f"Accuracy   : {accuracy * 100:.2f}%")
    print(f"Macro F1   : {macro_f1 * 100:.2f}%")
    print(f"Weighted F1: {weighted_f1 * 100:.2f}%")

    # --------------------------------------------------------
    # SIMPAN LAPORAN
    # --------------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = MODEL_DIR / f"evaluation_v4_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    report = classification_report(
        y_val,
        prediction,
        output_dict=True,
        zero_division=0
    )

    pd.DataFrame(report).transpose().to_csv(
        output_dir / "classification_report_v4.csv"
    )

    labels = sorted(
        set(y_val) | set(prediction)
    )

    cm = confusion_matrix(
        y_val,
        prediction,
        labels=labels
    )

    pd.DataFrame(
        cm,
        index=labels,
        columns=labels
    ).to_csv(
        output_dir / "confusion_matrix_v4.csv"
    )

    pd.DataFrame([{
        "model": "Random Forest V4",
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "training_samples": len(y_aug),
        "validation_samples": len(y_val)
    }]).to_csv(
        output_dir / "model_metrics_v4.csv",
        index=False
    )

    # --------------------------------------------------------
    # SIMPAN MODEL BARU
    # --------------------------------------------------------

    joblib.dump(
        model,
        MODEL_PATH_V4,
        compress=3
    )

    metadata = {
        "model_name": "Random Forest V4",
        "feature_version": FEATURE_VERSION,
        "n_features": EXPECTED_FEATURES,
        "classes": [str(c) for c in model.classes_],
        "trained_at": datetime.now().isoformat(),
        "training_samples": int(len(y_aug)),
        "validation_samples": int(len(y_val)),
        "augmentation": "active-hand-only jitter and small xy rotation",
        "validation_method": "ordered block split per label and source",
        "metrics": {
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1)
        },
        "note": (
            "Webcam data was previously used for V2/V3 evaluation. "
            "It is now used in V4 development and is not an untouched "
            "independent test set."
        )
    }

    with open(
        META_PATH_V4,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n" + "=" * 65)
    print("TRAINING V4 SELESAI")
    print("=" * 65)

    print("Model   :", MODEL_PATH_V4)
    print("Metadata:", META_PATH_V4)
    print("Laporan :", output_dir)

    print("\nV2 dan V3 tidak diubah.")
    print(
        "PENTING: hasil validation ini bukan pengujian independen final."
    )


if __name__ == "__main__":
    main()
