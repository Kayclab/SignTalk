"""
features.py  -  SATU-SATUNYA standar fitur SignTalk.

Dipakai oleh: collect_data.py, prepare_dataset.py, train_model.py,
app.py dan test_live.py. Jangan menulis ulang logika ini di file lain.
Jika Anda mengubah apa pun di sini, naikkan FEATURE_VERSION lalu
latih ulang model.
"""

import urllib.request
from pathlib import Path

import numpy as np

# ------------------------------------------------------------
# Standar fitur
# ------------------------------------------------------------
FEATURE_VERSION = "v2-mirror-pixel-maxnorm-sorted"

NUM_LANDMARKS = 21
HAND_FEATURES = NUM_LANDMARKS * 3          # 63
EXPECTED_FEATURES = HAND_FEATURES * 2      # 126
FEATURE_COLUMNS = [f"f_{i}" for i in range(EXPECTED_FEATURES)]

# Semua frame dicerminkan (tampilan selfie) SEBELUM dideteksi.
# Dataset lama terbukti direkam dengan orientasi cermin.
MIRROR_INPUT = True

# Resolusi yang diasumsikan untuk dataset lama (hanya dipakai
# oleh prepare_dataset.py untuk mengonversi data lama).
LEGACY_WIDTH = 640
LEGACY_HEIGHT = 480

# ------------------------------------------------------------
# Konfigurasi detektor (dipakai sama oleh collector, app, test)
# ------------------------------------------------------------
DETECTION_CONFIDENCE = 0.4
PRESENCE_CONFIDENCE = 0.4
TRACKING_CONFIDENCE = 0.4

TASK_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


def ensure_hand_model(task_path):
    task_path = Path(task_path)
    if task_path.exists() and task_path.stat().st_size > 0:
        return task_path
    print("[INFO] Mengunduh hand_landmarker.task ...")
    try:
        urllib.request.urlretrieve(TASK_MODEL_URL, str(task_path))
    except Exception as error:
        if task_path.exists():
            task_path.unlink()
        raise RuntimeError(
            "Gagal mengunduh hand_landmarker.task. Unduh manual dari "
            + TASK_MODEL_URL
        ) from error
    return task_path


def create_landmarker(task_path):
    """Detektor MediaPipe mode IMAGE (tiap frame berdiri sendiri)."""
    import mediapipe as mp

    task_path = ensure_hand_model(task_path)
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(task_path)),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=DETECTION_CONFIDENCE,
        min_hand_presence_confidence=PRESENCE_CONFIDENCE,
        min_tracking_confidence=TRACKING_CONFIDENCE,
    )
    return mp.tasks.vision.HandLandmarker.create_from_options(options)


def detect_bgr(landmarker, frame_bgr):
    """Frame BGR (sudah dicerminkan jika perlu) -> hasil MediaPipe."""
    import cv2
    import mediapipe as mp

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return landmarker.detect(image)


# ------------------------------------------------------------
# Ekstraksi fitur
# ------------------------------------------------------------
def _scale_and_center(points, width, height):
    """points: array (21,3) koordinat ternormalisasi 0..1 (x,y,z)."""
    pts = np.asarray(points, dtype=np.float64).reshape(NUM_LANDMARKS, 3)

    # 1) Koordinat piksel -> proporsi tangan tidak terdistorsi aspect ratio.
    #    (z pada MediaPipe berskala sama dengan x)
    pts = pts * np.array([width, height, width], dtype=np.float64)

    # 2) Pergelangan tangan (landmark 0) jadi titik asal.
    pts = pts - pts[0]

    # 3) Skala per tangan: tidak peka jarak tangan ke kamera.
    scale = np.max(np.abs(pts))
    if scale < 1e-9:
        return np.zeros(HAND_FEATURES, dtype=np.float32)
    return (pts / scale).astype(np.float32).flatten()


def landmarks_to_array(hand_landmarks):
    return np.array(
        [[p.x, p.y, p.z] for p in hand_landmarks], dtype=np.float64
    )


def extract_features(hand_landmarks_list, width, height):
    """
    Mengembalikan 126 fitur.
    - Tangan diurutkan dari yang paling KIRI pada layar (pergelangan x
      terkecil), sehingga urutan slot deterministik.
    - 1 tangan  -> slot pertama terisi, slot kedua nol.
    - 2 tangan  -> kedua slot terisi.
    """
    hands = []
    for hand in hand_landmarks_list[:2]:
        arr = landmarks_to_array(hand)
        hands.append((arr[0, 0], arr))
    hands.sort(key=lambda item: item[0])

    slots = [np.zeros(HAND_FEATURES, dtype=np.float32) for _ in range(2)]
    for index, (_, arr) in enumerate(hands):
        slots[index] = _scale_and_center(arr, width, height)

    features = np.concatenate(slots)
    assert features.shape[0] == EXPECTED_FEATURES
    return features


# ------------------------------------------------------------
# Konversi data lama -> standar sekarang (untuk prepare_dataset.py)
# ------------------------------------------------------------
def legacy_rows_to_v2(raw, width=LEGACY_WIDTH, height=LEGACY_HEIGHT,
                      mirror=False):
    """
    raw: array (n,126) berisi koordinat relatif-wrist ternormalisasi
    (tanpa koreksi aspect). Mengembalikan fitur standar v2.
    mirror=True untuk data yang direkam tanpa flip.
    Skala per tangan dihitung ulang sehingga data yang sudah di-max-norm
    juga dikonversi secara eksak.
    """
    raw = np.asarray(raw, dtype=np.float64).copy()
    if mirror:
        raw[:, 0::3] *= -1.0
    out = np.zeros_like(raw, dtype=np.float32)
    factor = np.tile(
        np.array([width, height, width], dtype=np.float64), NUM_LANDMARKS
    )
    for start in (0, HAND_FEATURES):
        block = raw[:, start:start + HAND_FEATURES] * factor
        scale = np.max(np.abs(block), axis=1, keepdims=True)
        valid = scale[:, 0] > 1e-12
        res = np.zeros_like(block)
        res[valid] = block[valid] / scale[valid]
        out[:, start:start + HAND_FEATURES] = res.astype(np.float32)
    return out
