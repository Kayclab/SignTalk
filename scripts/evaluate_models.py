
import sys
import json
import joblib
import argparse
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from signtalk.features import (
    FEATURE_COLUMNS,
    FEATURE_VERSION
)

from signtalk.paths import MODEL_DIR

V2 = MODEL_DIR / "random_forest_v2.pkl"
V3 = MODEL_DIR / "random_forest_v3_augmented.pkl"

META_V2 = MODEL_DIR / "model_meta.json"
META_V3 = MODEL_DIR / "model_v3_augmented_meta.json"


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test-csv",
        default=str(
            ROOT / "dataset" /
            "dataset_test_independent.csv"
        )
    )

    args = parser.parse_args()

    test_path = Path(args.test_csv)

    if not test_path.is_absolute():
        test_path = ROOT / test_path

    if not test_path.exists():
        raise SystemExit("Dataset pengujian tidak ditemukan.")

    df = pd.read_csv(test_path)

    required = FEATURE_COLUMNS + ["label"]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise SystemExit(f"Kolom hilang: {missing}")

    X = df[FEATURE_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce"
    ).to_numpy(np.float32)

    y = df["label"].astype(str).str.strip().to_numpy()

    if not np.isfinite(X).all():
        raise SystemExit("Fitur mengandung NaN atau inf.")

    if np.any(y == ""):
        raise SystemExit("Label kosong ditemukan.")

    print("JUMLAH PENGUJIAN:", len(y))
    print("JUMLAH KELAS:", len(np.unique(y)))

    for col in ["participant_id", "session_id"]:
        if col in df.columns:
            print(col, ":", df[col].nunique())

    for path in [META_V2, META_V3]:
        if path.exists():
            meta = json.loads(
                path.read_text(encoding="utf-8")
            )

            if meta.get("feature_version") != FEATURE_VERSION:
                raise SystemExit(
                    f"Feature version tidak cocok: {path.name}"
                )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output = MODEL_DIR / f"evaluation_{timestamp}"
    output.mkdir(parents=True, exist_ok=False)

    models = [
        ("V2", V2),
        ("V3", V3)
    ]

    comparison = []
    predictions = df.copy()

    for name, path in models:

        if not path.exists():
            print("Model tidak ditemukan:", path)
            continue

        model = joblib.load(path)

        if getattr(model, "n_features_in_", None) != 126:
            raise SystemExit(
                f"Model {name} bukan model 126 fitur."
            )

        unknown = sorted(
            set(y) - set(map(str, model.classes_))
        )

        if unknown:
            raise SystemExit(
                f"Label tidak dikenal {name}: {unknown}"
            )

        if hasattr(model, "n_jobs"):
            model.n_jobs = 1

        pred = model.predict(X).astype(str)

        accuracy = accuracy_score(y, pred)

        macro = f1_score(
            y, pred,
            average="macro",
            zero_division=0
        )

        weighted = f1_score(
            y, pred,
            average="weighted",
            zero_division=0
        )

        comparison.append({
            "model": name,
            "samples": len(y),
            "accuracy": accuracy,
            "macro_f1": macro,
            "weighted_f1": weighted
        })

        labels = sorted(
            set(map(str, model.classes_)) | set(y)
        )

        report = classification_report(
            y,
            pred,
            labels=labels,
            output_dict=True,
            zero_division=0
        )

        pd.DataFrame(report).transpose().to_csv(
            output / f"classification_report_{name}.csv"
        )

        cm = confusion_matrix(
            y, pred, labels=labels
        )

        pd.DataFrame(
            cm,
            index=labels,
            columns=labels
        ).to_csv(
            output / f"confusion_matrix_{name}.csv"
        )

        predictions[f"prediction_{name}"] = pred

        if hasattr(model, "predict_proba"):
            predictions[f"confidence_{name}"] = (
                model.predict_proba(X).max(axis=1)
            )

        print(f"\nMODEL {name}")
        print("Accuracy:", round(accuracy, 4))
        print("Macro F1:", round(macro, 4))
        print("Weighted F1:", round(weighted, 4))

    if not comparison:
        raise SystemExit("Tidak ada model yang dapat dievaluasi.")

    pd.DataFrame(comparison).to_csv(
        output / "model_comparison.csv",
        index=False
    )

    predictions.to_csv(
        output / "predictions.csv",
        index=False
    )

    print("\nEvaluasi selesai.")
    print("Hasil disimpan di:", output)
    print("Model lama tidak diubah.")


if __name__ == "__main__":
    main()
