"""
paths.py  -  SATU-SATUNYA tempat lokasi file/folder SignTalk.

Semua path dihitung dari root proyek, sehingga skrip bisa dijalankan
dari folder mana pun (python scripts/train_model.py, dari VS Code, dll).
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

# Folder utama
DATASET_DIR = ROOT_DIR / "dataset"
MODEL_DIR = ROOT_DIR / "model"
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

# Dataset
DATASET_PATH = DATASET_DIR / "dataset_v2.csv"            # standar v2 (aktif)
LEGACY_DATASET_PATH = DATASET_DIR / "dataset_tangan.csv"  # data lama (sumber)
REJECTED_ROWS_PATH = DATASET_DIR / "baris_ditolak.csv"

# Model
MODEL_PATH = MODEL_DIR / "random_forest_v2.pkl"          # model aktif
LEGACY_MODEL_PATH = MODEL_DIR / "random_forest.pkl"      # model lama (v1)
META_PATH = MODEL_DIR / "model_meta.json"
TASK_MODEL_PATH = MODEL_DIR / "hand_landmarker.task"     # MediaPipe

# Laporan hasil training / pengujian
CONFUSION_MATRIX_PATH = MODEL_DIR / "confusion_matrix_v2.csv"
CLASSIFICATION_REPORT_PATH = MODEL_DIR / "classification_report_v2.csv"
MODEL_COMPARISON_PATH = MODEL_DIR / "perbandingan_model.csv"
LIVE_TEST_RESULT_PATH = MODEL_DIR / "hasil_uji_live.csv"
DETECTION_DIAGNOSIS_PATH = MODEL_DIR / "diagnosa_deteksi.csv"
