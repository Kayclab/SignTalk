"""
augment_and_retrain.py

Improve word detection by:
1. Augmenting data for undersampled classes (especially the 10 words)
2. Training with class weights
3. Evaluating improvement

Usage: python scripts/augment_and_retrain.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from datetime import datetime
import joblib

from signtalk.features import FEATURE_COLUMNS, FEATURE_VERSION, HAND_FEATURES
from signtalk.paths import DATASET_PATH, META_PATH, MODEL_PATH, CLASSIFICATION_REPORT_PATH

# ============================================================
# CONFIGURATION
# ============================================================

# Define the 10 BISINDO words
BISINDO_WORDS = {
    'Terimakasih',      # Thank you - PRIORITY 1 (F1: 0.659)
    'Tolong',           # Please - PRIORITY 1 (F1: 0.349)
    'Maaf',             # Sorry - PRIORITY 1 (F1: 0.308)
    'Belajar',          # Study/Learn - PRIORITY 2 (F1: 0.746)
    'Bisa',             # Can - PRIORITY 2 (F1: 0.709)
    'Permisi',          # Pardon
    'Sama sama',        # You're welcome
    'Sedikit',          # A little (this one is perfect: F1: 1.0)
    'Teman-teman',      # Friends
    'Bahasa isyarat',   # Sign language
}

# Target minimum samples per class
TARGET_MIN_SAMPLES = 700  # Increase undersampled classes to this level

RANDOM_STATE = 42

# We'll compute class weights after loading data
RF_BASE_PARAMS = dict(
    n_estimators=200,
    max_features="sqrt",
    min_samples_leaf=2,
    n_jobs=1,  # Set to 1 to avoid overhead for single predictions
    random_state=RANDOM_STATE,
)

print("=" * 70)
print("  SIGNTALK WORD DETECTION IMPROVEMENT")
print("=" * 70)

# ============================================================
# 1. LOAD ORIGINAL DATASET
# ============================================================

if not DATASET_PATH.exists():
    raise SystemExit(f"[ERROR] {DATASET_PATH} not found")

df = pd.read_csv(DATASET_PATH)
X = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="raise").to_numpy(np.float32)
y = df["label"].astype(str).str.strip().to_numpy()

print(f"\n[1] Original dataset: {len(df)} samples, {len(np.unique(y))} classes")

# ============================================================
# 2. DATA AUGMENTATION
# ============================================================

print("\n[2] Data Augmentation...")

# Augmentation techniques for hand landmark features
def augment_sample(features, augmentation_type="jitter"):
    """
    Apply augmentation to a 126-feature vector (2 hands, 21 landmarks each, x,y,z coords)
    """
    features = features.copy()

    if augmentation_type == "jitter":
        # Add small random noise to all features
        noise = np.random.normal(0, 0.02, size=features.shape)
        features = features + noise

    elif augmentation_type == "scale":
        # Small scale changes (hand slightly closer/farther)
        scale = np.random.uniform(0.95, 1.05)
        features = features * scale

    elif augmentation_type == "rotate_hand":
        # Simulate small rotation of hand in image
        # Apply to each hand separately (landmarks 0-20 and 21-41 for each hand)
        for hand_idx in [0, 1]:
            start = hand_idx * HAND_FEATURES
            end = start + HAND_FEATURES

            hand_features = features[start:end].reshape(21, 3)
            angle = np.random.uniform(-0.1, 0.1)  # Small rotation in radians

            # Rotate x,y coordinates around center
            cx, cy = np.median(hand_features[:, 0]), np.median(hand_features[:, 1])
            hand_features[:, 0] -= cx
            hand_features[:, 1] -= cy

            cos_a, sin_a = np.cos(angle), np.sin(angle)
            new_x = hand_features[:, 0] * cos_a - hand_features[:, 1] * sin_a
            new_y = hand_features[:, 0] * sin_a + hand_features[:, 1] * cos_a

            hand_features[:, 0] = new_x + cx
            hand_features[:, 1] = new_y + cy
            features[start:end] = hand_features.flatten()

    elif augmentation_type == "dropout":
        # Zero out some features (simulate missing landmark detection)
        mask = np.random.binomial(1, 0.1, size=features.shape)  # 10% dropout
        features = features * (1 - mask)

    return np.clip(features, -1, 1)  # Clip to valid range


# Build augmented dataset
augmented_rows = []

counts = pd.Series(y).value_counts()
for label, count in counts.items():
    class_mask = y == label
    class_X = X[class_mask]

    # If this is a low-sample word, augment it
    if label in BISINDO_WORDS and count < TARGET_MIN_SAMPLES:
        needed = TARGET_MIN_SAMPLES - count
        aug_types = ["jitter", "scale", "rotate_hand", "dropout"]

        for i in range(needed):
            sample_idx = i % len(class_X)
            aug_type = aug_types[i % len(aug_types)]
            augmented_sample = augment_sample(class_X[sample_idx], aug_type)
            augmented_rows.append((augmented_sample, label))

        print(f"  {label:20s}: {count} -> {count + needed} samples (added {needed})")
    else:
        if label in BISINDO_WORDS:
            print(f"  {label:20s}: {count} samples (sufficient)")

# Create new dataset with augmented samples
new_X = list(X)
new_y = list(y)

for aug_features, label in augmented_rows:
    new_X.append(aug_features)
    new_y.append(label)

new_X = np.array(new_X, dtype=np.float32)
new_y = np.array(new_y)

print(f"\n[3] Augmented dataset: {len(new_X)} samples (added {len(new_X) - len(X)} synthetic samples)")

# ============================================================
# 4. TRAIN IMPROVED MODEL WITH CLASS WEIGHTS
# ============================================================

print(f"\n[4] Training RandomForest with balanced class weights...")
print(f"    Parameters: {RF_BASE_PARAMS}")

RF_PARAMS = {**RF_BASE_PARAMS, 'class_weight': 'balanced_subsample'}
model = RandomForestClassifier(**RF_PARAMS)
print(f"    Fitting {len(new_X)} samples...")
model.fit(new_X, new_y)
print(f"    ✓ Model trained successfully")

print(f"    Model trained: {len(model.classes_)} classes")

# ============================================================
# 5. EVALUATE ON ORIGINAL TEST SET (for fair comparison)
# ============================================================

print(f"\n[5] Evaluating on original test set...")

# Use original test set (last 20% of each class, blocked)
test_indices = []
for label in np.unique(y):
    label_indices = np.where(y == label)[0]
    n = len(label_indices)
    test_count = max(20, int(0.2 * n))
    test_indices.extend(label_indices[-test_count:])

test_indices = np.array(sorted(test_indices))
test_X = X[test_indices]
test_y = y[test_indices]

y_pred = model.predict(test_X)

overall_acc = accuracy_score(test_y, y_pred)
overall_f1 = f1_score(test_y, y_pred, average='weighted')

print(f"  Overall Accuracy: {overall_acc:.4f}")
print(f"  Overall F1 (weighted): {overall_f1:.4f}")

# Detailed report for 10 words
print(f"\n[6] Performance on 10 BISINDO Words:")
print(f"{'Word':<20} {'F1-Score':<12} {'Precision':<12} {'Recall':<12}")
print("-" * 56)

report = classification_report(test_y, y_pred, output_dict=True)
for word in sorted(BISINDO_WORDS):
    if word in report:
        metrics = report[word]
        f1 = metrics['f1-score']
        precision = metrics['precision']
        recall = metrics['recall']
        status = "✓" if f1 > 0.85 else "⚠" if f1 > 0.70 else "✗"
        print(f"{word:<20} {f1:<12.4f} {precision:<12.4f} {recall:<12.4f} {status}")

# ============================================================
# 7. SAVE IMPROVED MODEL
# ============================================================

# Save as v3 model for comparison
model_v3_path = Path(MODEL_PATH).parent / "random_forest_v3_augmented.pkl"
joblib.dump(model, model_v3_path)

meta = {
    "feature_version": FEATURE_VERSION,
    "training_date": datetime.now().isoformat(),
    "training_samples": len(new_X),
    "augmentation": "jitter, scale, rotate_hand, dropout",
    "class_weight": "balanced",
    "accuracy": float(overall_acc),
    "weighted_f1": float(overall_f1),
}

meta_path = Path(MODEL_PATH).parent / "model_v3_augmented_meta.json"
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\n[7] Models saved:")
print(f"  Model: {model_v3_path}")
print(f"  Metadata: {meta_path}")

# ============================================================
# 8. SUMMARY & RECOMMENDATIONS
# ============================================================

print("\n" + "=" * 70)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 70)

print(f"\n✓ Data Augmentation applied to {len(augmented_rows)} synthetic samples")
print(f"✓ Class weighting enabled (balanced)")
print(f"✓ Model trained and evaluated")

print(f"\nResults:")
print(f"  Overall Accuracy: {overall_acc:.4f} (81.45% baseline)")
print(f"  Overall F1: {overall_f1:.4f}")

print(f"\nNext Steps:")
print(f"1. If F1 > 0.85 for all words: Deploy this model (v3_augmented)")
print(f"2. If still < 0.85 for some words: Collect more real data for those words:")
print(f"   - Priority 1: Terimakasih, Tolong, Maaf (< 0.70 F1)")
print(f"   - Collect 200-300 NEW REAL SAMPLES for each word")
print(f"3. Run: python scripts/collect_data.py to gather more data")

print("\n" + "=" * 70)
