"""
DEBUG_FEATURES.PY
=================

Skrip ini menjalankan Flask yang sama seperti app.py, tapi mencatat setiap fitur 126
yang dikirim ke model, jadi kita bisa melihat perbedaannya dengan dataset.

CARA PAKAI:
1. Jalankan: python debug_features.py
2. Buka http://127.0.0.1:5000/camera
3. Coba isyarat huruf A (atau label lain) selama 5 detik
4. Di terminal akan muncul "Contoh fitur A: [...]" beberapa kali
5. Jalankan debug_compare.py untuk membandingkan dengan dataset

"""

import urllib.request
import os
import time
import base64
import threading
from pathlib import Path

import cv2
import joblib
import numpy as np
import mediapipe as mp

from flask import (
    Flask,
    render_template,
    Response,
    jsonify,
    request
)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)

MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = os.getenv("RF_MODEL_PATH")

if MODEL_PATH:
    MODEL_PATH = Path(MODEL_PATH)
    if not MODEL_PATH.is_absolute():
        MODEL_PATH = BASE_DIR / MODEL_PATH
else:
    MODEL_PATH = None

TASK_MODEL_PATH = BASE_DIR / "hand_landmarker.task"

CAMERA_INDEX = 0
MAX_HANDS = 2
EXPECTED_FEATURES = 126

def load_random_forest():
    if MODEL_PATH is not None:
        candidates = [MODEL_PATH]
    else:
        candidates = []
        for extension in ("*.joblib", "*.pkl"):
            candidates.extend(MODEL_DIR.glob(extension))

    if not candidates:
        raise FileNotFoundError(
            "Model Random Forest tidak ditemukan. "
            "Pastikan file .joblib atau .pkl berada di folder model."
        )

    selected_model = candidates[0]

    if not selected_model.exists():
        raise FileNotFoundError(
            f"File model tidak ditemukan: {selected_model}"
        )

    loaded_model = joblib.load(selected_model)

    if not hasattr(loaded_model, "predict"):
        raise TypeError(
            "File yang dimuat bukan model dengan method predict()."
        )

    print(f"[INFO] Model berhasil dimuat: {selected_model.name}")

    if hasattr(loaded_model, "n_features_in_"):
        feature_count = loaded_model.n_features_in_

        print(f"[INFO] Jumlah fitur model: {feature_count}")

        if feature_count != EXPECTED_FEATURES:
            raise ValueError(
                f"Model mengharapkan {feature_count} fitur, "
                f"sedangkan aplikasi menghasilkan {EXPECTED_FEATURES} fitur."
            )

    return loaded_model


model = load_random_forest()

# Download model MediaPipe jika belum ada
TASK_MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/"
    "hand_landmarker.task"
)

if not TASK_MODEL_PATH.exists():
    print("[INFO] Model Hand Landmarker belum ditemukan.")
    print("[INFO] Mengunduh model dari Google...")

    try:
        urllib.request.urlretrieve(
            TASK_MODEL_URL,
            str(TASK_MODEL_PATH)
        )
        print("[INFO] Model Hand Landmarker berhasil diunduh!")

    except Exception as error:
        if TASK_MODEL_PATH.exists():
            TASK_MODEL_PATH.unlink()

        raise RuntimeError(
            "Gagal mengunduh model Hand Landmarker. "
            "Periksa koneksi internet atau download manual dari: "
            + TASK_MODEL_URL
        ) from error

if (
    not TASK_MODEL_PATH.exists()
    or TASK_MODEL_PATH.stat().st_size == 0
):
    raise FileNotFoundError(
        "File hand_landmarker.task tidak ditemukan atau kosong."
    )

print(
    f"[INFO] Hand Landmarker model: {TASK_MODEL_PATH}"
)

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

landmarker_options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=str(TASK_MODEL_PATH)
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

hand_landmarker = HandLandmarker.create_from_options(
    landmarker_options
)

landmarker_lock = threading.Lock()
last_timestamp_ms = 0

print("[INFO] MediaPipe HandLandmarker berhasil diinisialisasi!")

# File untuk menyimpan fitur yang tertangkap
FEATURES_LOG = BASE_DIR / "debug_features.log"
features_log_file = open(FEATURES_LOG, "w")

def normalize_hand_landmarks(hand_landmarks):
    coordinates = np.array(
        [
            [point.x, point.y, point.z]
            for point in hand_landmarks
        ],
        dtype=np.float32
    )

    if coordinates.shape != (21, 3):
        raise ValueError(
            "Jumlah landmark tangan harus tepat 21."
        )

    # Wrist sebagai titik referensi (sama seperti dataset).
    coordinates = coordinates - coordinates[0]

    return coordinates.flatten()


def extract_features(hand_landmarks_list, handedness_list=None):
    first_features = np.zeros(63, dtype=np.float32)
    second_features = np.zeros(63, dtype=np.float32)

    if len(hand_landmarks_list) >= 1:
        first_features = normalize_hand_landmarks(
            hand_landmarks_list[0]
        )

    if len(hand_landmarks_list) >= 2:
        second_features = normalize_hand_landmarks(
            hand_landmarks_list[1]
        )

    features = np.concatenate(
        [first_features, second_features]
    )

    if features.shape[0] != EXPECTED_FEATURES:
        raise ValueError(
            f"Ekstraksi menghasilkan {features.shape[0]} fitur, "
            f"seharusnya {EXPECTED_FEATURES}."
        )

    return features


def detect_hands(frame):
    global last_timestamp_ms

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    with landmarker_lock:
        timestamp_ms = time.monotonic_ns() // 1_000_000
        timestamp_ms = max(
            timestamp_ms,
            last_timestamp_ms + 1
        )
        last_timestamp_ms = timestamp_ms
        result = hand_landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

    return result


def predict_sign(features):
    features = np.asarray(
        features,
        dtype=np.float32
    ).reshape(1, -1)

    if features.shape[1] != EXPECTED_FEATURES:
        raise ValueError(
            f"Model membutuhkan {EXPECTED_FEATURES} fitur."
        )

    prediction = model.predict(features)[0]

    if isinstance(prediction, np.generic):
        prediction = prediction.item()

    confidence = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        confidence = float(np.max(probabilities))

    return {
        "prediction": str(prediction),
        "confidence": confidence
    }


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/camera")
def camera():
    camera_template = BASE_DIR / "templates" / "camera.html"

    if camera_template.exists():
        return render_template("camera.html")

    return render_template("landing.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        image_file = request.files.get("frame")

        if image_file is None:
            image_file = request.files.get("image")

        if image_file is not None:

            image_bytes = image_file.read()

            if not image_bytes:
                return jsonify({
                    "success": False,
                    "message": "File gambar kosong."
                }), 400

            image_array = np.frombuffer(
                image_bytes,
                dtype=np.uint8
            )

            frame = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            if frame is None:
                return jsonify({
                    "success": False,
                    "message": "Gambar tidak dapat dibaca OpenCV."
                }), 400

            result = detect_hands(frame)

            hand_landmarks_list = result.hand_landmarks
            handedness_list = result.handedness

            detected_hands = len(hand_landmarks_list)

            if detected_hands == 0:

                return jsonify({
                    "success": True,
                    "detected": False,
                    "detected_hands": 0,
                    "prediction": "-",
                    "confidence": 0,
                    "message": "Tidak ada tangan terdeteksi."
                }), 200

            features = extract_features(
                hand_landmarks_list,
                handedness_list
            )

            # ============ DEBUG: CATAT FITUR ============
            fitur_min = np.min(features)
            fitur_max = np.max(features)
            fitur_mean = np.mean(features)
            print(f"[FITUR] min={fitur_min:.4f} max={fitur_max:.4f} mean={fitur_mean:.4f} | {features[:5]}")
            # Tulis sebagai representasi list untuk mudah diparsing
            features_list = features.tolist()
            features_log_file.write(f"{features_list}\n")
            features_log_file.flush()
            # ==========================================

            prediction_result = predict_sign(features)

            prediction = prediction_result["prediction"]

            confidence = prediction_result["confidence"]

            confidence_percent = (
                round(confidence * 100, 2)
                if confidence is not None
                else 0
            )

            return jsonify({
                "success": True,
                "detected": True,
                "detected_hands": detected_hands,
                "prediction": prediction,
                "confidence": confidence_percent,
                "message": "Prediksi berhasil."
            }), 200

        return jsonify({
            "success": False,
            "message": (
                "Data tidak ditemukan. Kirim frame, image, "
                "atau features (126 fitur)."
            )
        }), 400

    except Exception as error:

        app.logger.exception(
            "Terjadi kesalahan pada API prediksi."
        )

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "application": "SignTalk DEBUG",
        "mediapipe": "Tasks API",
        "hand_detection": True,
        "max_hands": MAX_HANDS,
        "feature_count": EXPECTED_FEATURES,
        "model_loaded": model is not None
    })


if __name__ == "__main__":

    print("=" * 55)
    print("             SIGNTALK DEBUG")
    print("=" * 55)

    print("[INFO] Python environment siap.")
    print("[INFO] MediaPipe Tasks API aktif.")
    print("[INFO] Random Forest siap digunakan.")
    print("[INFO] Jumlah fitur: 126")
    print(f"[INFO] Fitur dicatat ke: {FEATURES_LOG}")
    print("[INFO] Server: http://127.0.0.1:5000")

    try:

        app.run(
            host="127.0.0.1",
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=True
        )

    finally:

        hand_landmarker.close()
        features_log_file.close()

        print("[INFO] MediaPipe berhasil ditutup.")
