import base64
import json
import os
import threading
from pathlib import Path

import cv2
import joblib
import numpy as np

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

from signtalk.features import (
    EXPECTED_FEATURES,
    FEATURE_VERSION,
    MIRROR_INPUT,
    create_landmarker,
    detect_bgr,
    extract_features,
)
from signtalk.paths import (
    META_PATH,
    MODEL_PATH as DEFAULT_MODEL_PATH,
    ROOT_DIR as BASE_DIR,
    STATIC_DIR,
    TASK_MODEL_PATH,
    TEMPLATES_DIR,
)

# ============================================================
# 1. KONFIGURASI
# ============================================================

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
)

CAMERA_INDEX = 0
MAX_HANDS = 2


# ============================================================
# 2. LOAD MODEL (v3 augmented preferred; falls back to v2)
# ============================================================


def load_random_forest():

    env_path = os.getenv("RF_MODEL_PATH")
    model_dir = Path(DEFAULT_MODEL_PATH).parent

    # Default: gunakan V4.
    # Jika RF_MODEL_PATH ditentukan, gunakan model tersebut.
    if env_path:
        model_path = Path(env_path)

        if not model_path.is_absolute():
            model_path = BASE_DIR / model_path
    else:
        # Urutan: V7 ringan (.npz, numpy murni) -> V4 penuh (.pkl)
        candidates = [
            model_dir / "random_forest_v7_lite.npz",
            model_dir / "random_forest_v4.pkl",
        ]
        model_path = next((c for c in candidates if c.exists()), candidates[-1])

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model tidak ditemukan: {model_path}"
        )

    # Pilih metadata sesuai model yang digunakan.
    metadata_files = {
        "random_forest_v4": model_dir / "model_v4_meta.json",
        "random_forest_v7_lite": model_dir / "model_v7_meta.json",
        "random_forest_v3_augmented": model_dir / "model_v3_augmented_meta.json",
        "random_forest_v2": META_PATH,
        "random_forest": META_PATH,
    }

    meta_path = metadata_files.get(model_path.stem)

    if meta_path and meta_path.exists():
        meta = json.loads(
            meta_path.read_text(encoding="utf-8")
        )

        if meta.get("feature_version") != FEATURE_VERSION:
            raise RuntimeError(
                "Versi fitur model berbeda dengan kode aplikasi. "
                f"Model: {meta.get('feature_version')}, "
                f"Aplikasi: {FEATURE_VERSION}"
            )

    if model_path.suffix == ".npz":
        from signtalk.numpy_forest import NumpyForest

        loaded = NumpyForest(model_path)
    else:
        loaded = joblib.load(model_path)

    if not hasattr(loaded, "predict"):
        raise TypeError(
            "File model tidak memiliki method predict()."
        )

    if getattr(
        loaded, "n_features_in_", EXPECTED_FEATURES
    ) != EXPECTED_FEATURES:
        raise ValueError(
            f"Model memakai {loaded.n_features_in_} fitur, "
            f"aplikasi menghasilkan {EXPECTED_FEATURES}."
        )

    # Optimasi prediksi webcam.
    if hasattr(loaded, "n_jobs"):
        loaded.n_jobs = 1

    print("=" * 50)
    print("[INFO] MODEL SIGNTALK BERHASIL DIMUAT")
    print(f"[INFO] Model       : {model_path.name}")
    print(f"[INFO] Metadata    : {meta_path}")
    print(f"[INFO] Versi fitur : {FEATURE_VERSION}")
    print(f"[INFO] Jumlah kelas: {len(loaded.classes_)}")
    print("=" * 50)

    return loaded


model = load_random_forest()


# ============================================================
# 3. MEDIAPIPE (konfigurasi sama dengan collector)
# ============================================================

hand_landmarker = create_landmarker(TASK_MODEL_PATH)
landmarker_lock = threading.Lock()
print("[INFO] MediaPipe HandLandmarker siap.")


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


def draw_hand_landmarks(frame, hand_landmarks):

    height, width, _ = frame.shape
    points = [(int(p.x * width), int(p.y * height)) for p in hand_landmarks]

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (253, 181, 196), 1)  # ungu muda #C4B5FD (BGR)

    for point in points:
        cv2.circle(frame, point, 3, (79, 209, 249), -1)  # kuning #F9D14F (BGR)

    return frame


# ============================================================
# 4. DETEKSI & PREDIKSI (satu jalur untuk semua sumber frame)
# ============================================================

def detect_hands(frame):

    with landmarker_lock:
        return detect_bgr(hand_landmarker, frame)


def predict_sign(features):

    features = np.asarray(features, dtype=np.float32).reshape(1, -1)

    if features.shape[1] != EXPECTED_FEATURES:
        raise ValueError(f"Model membutuhkan {EXPECTED_FEATURES} fitur.")

    probabilities = model.predict_proba(features)[0]
    best = int(np.argmax(probabilities))
    conf = float(probabilities[best])

    # Ambang batas minimal agar AI tidak menebak-nebak saat tangan diam/santai
    is_confident = conf >= 0.55

    return {
        "prediction": str(model.classes_[best]),
        "confidence": conf,
        "is_confident": is_confident,
    }


def predict_from_frame(frame):
    """
    Frame BGR mentah (belum dicerminkan) ->
    (frame_tercermin, hasil_mediapipe, prediksi, jumlah_tangan).
    Pencerminan dilakukan SATU kali di sini.
    """

    if MIRROR_INPUT:
        frame = cv2.flip(frame, 1)

    height, width = frame.shape[:2]

    result = detect_hands(frame)
    hands = result.hand_landmarks

    if not hands:
        return frame, result, None, 0

    features = extract_features(hands, width, height)

    return frame, result, predict_sign(features), len(hands)


def detect_hands_only(frame):
    """Seperti predict_from_frame tetapi tanpa ekstraksi fitur/prediksi (lebih ringan)."""

    if MIRROR_INPUT:
        frame = cv2.flip(frame, 1)

    result = detect_hands(frame)
    return frame, result, len(result.hand_landmarks or [])


def build_response(prediction, hand_count, result=None):
    # Ekstrak koordinat landmark sendi tangan untuk pipeline skeleton frontend
    landmarks = []
    if result is not None and getattr(result, "hand_landmarks", None):
        for hand in result.hand_landmarks:
            landmarks.append([
                {"x": round(float(lm.x), 4), "y": round(float(lm.y), 4)}
                for lm in hand
            ])

    if prediction is None:
        return {
            "success": True,
            "detected": bool(landmarks),
            "detected_hands": len(landmarks),
            "prediction": "-",
            "confidence": 0,
            "message": "Tidak ada tangan terdeteksi." if not landmarks else "Tangan terdeteksi.",
            "landmarks": landmarks,
        }

    conf_pct = round(prediction["confidence"] * 100, 1)

    # Jika tangan terlihat tapi belum membentuk isyarat dengan yakin (tangan diam/santai)
    if not prediction.get("is_confident", True):
        return {
            "success": True,
            "detected": True,
            "detected_hands": hand_count,
            "prediction": "-",
            "confidence": conf_pct,
            "message": f"{hand_count} tangan terdeteksi, isyarat belum jelas.",
            "landmarks": landmarks,
        }

    return {
        "success": True,
        "detected": True,
        "detected_hands": hand_count,
        "prediction": prediction["prediction"],
        "confidence": conf_pct,
        "message": "Prediksi berhasil.",
        "landmarks": landmarks,
    }


# ============================================================
# 5. ROUTING HALAMAN
# ============================================================

@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/penerjemah")
def penerjemah():
    return render_template("penerjemah.html")


@app.route("/latihan")
def latihan():
    return render_template("latihan.html")


@app.route("/kuis")
def kuis():
    return render_template("kuis.html")


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/camera")
def camera():
    return redirect(url_for("penerjemah"))


# ============================================================
# 6. STREAMING WEBCAM SERVER-SIDE (/video_feed)
# ============================================================

def generate_frames():

    camera_device = cv2.VideoCapture(CAMERA_INDEX)

    if not camera_device.isOpened():
        print("[ERROR] Kamera tidak dapat dibuka.")
        camera_device.release()
        return

    camera_device.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:

            success, raw = camera_device.read()

            if not success:
                break

            frame = raw

            try:
                frame, result, prediction, hand_count = predict_from_frame(raw)

                if prediction is not None:

                    for hand in result.hand_landmarks:
                        draw_hand_landmarks(frame, hand)

                    cv2.putText(
                        frame,
                        f"Prediction: {prediction['prediction']}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2,
                    )
                    cv2.putText(
                        frame,
                        f"Confidence: {prediction['confidence'] * 100:.2f}%",
                        (20, 75), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 0), 2,
                    )
                else:
                    cv2.putText(
                        frame, "No hand detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
                    )

            except Exception as error:

                print(f"[ERROR] Pemrosesan frame: {error}")
                cv2.putText(
                    frame, "Detection error", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
                )

            success, buffer = cv2.imencode(".jpg", frame)

            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

    finally:
        camera_device.release()


@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ============================================================
# 7. API PREDIKSI
# ============================================================

def decode_image(image_bytes):

    array = np.frombuffer(image_bytes, dtype=np.uint8)

    return cv2.imdecode(array, cv2.IMREAD_COLOR)


@app.route("/predict", methods=["POST"])
@app.route("/api/predict", methods=["POST"])
def api_predict():

    try:

        # MODE 1: multipart (field "frame" atau "image") dari browser
        image_file = request.files.get("frame")

        if image_file is None:
            image_file = request.files.get("image")

        if image_file is not None:

            image_bytes = image_file.read()

            if not image_bytes:
                return jsonify({
                    "success": False,
                    "message": "File gambar kosong.",
                }), 400

            frame = decode_image(image_bytes)

            if frame is None:
                return jsonify({
                    "success": False,
                    "message": "Gambar tidak dapat dibaca OpenCV.",
                }), 400

            # Optimasi performa: resize jika frame terlalu besar agar tidak lag/delay
            if frame.shape[1] > 480:
                h, w = frame.shape[:2]
                new_w = 360
                new_h = int(h * (new_w / w))
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Mode "track" (dipakai Game): hanya deteksi tangan, tanpa prediksi huruf,
            # supaya respons lebih cepat dan gerakan tangan lebih mulus.
            if request.form.get("mode") == "track":
                _, result, hand_count = detect_hands_only(frame)
                return jsonify(build_response(None, hand_count, result)), 200

            _, result, prediction, hand_count = predict_from_frame(frame)

            return jsonify(build_response(prediction, hand_count, result)), 200

        data = request.get_json(silent=True)

        # MODE 2: 126 fitur v2 dalam JSON
        if data is not None and "features" in data:

            features = data["features"]

            if not isinstance(features, (list, tuple)):
                return jsonify({
                    "success": False,
                    "message": "Format features harus berupa array.",
                }), 400

            if len(features) != EXPECTED_FEATURES:
                return jsonify({
                    "success": False,
                    "message": "Jumlah fitur harus tepat 126.",
                }), 400

            features = np.asarray(features, dtype=np.float32)

            if not np.all(np.isfinite(features)):
                return jsonify({
                    "success": False,
                    "message": "Fitur mengandung nilai tidak valid.",
                }), 400

            prediction = predict_sign(features)
            payload = build_response(prediction, 0)
            payload.pop("detected_hands", None)

            return jsonify(payload), 200

        # MODE 3: gambar base64 dalam JSON
        if data is not None and data.get("image"):

            image_data = data["image"]

            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            frame = decode_image(base64.b64decode(image_data, validate=True))

            if frame is None:
                return jsonify({
                    "success": False,
                    "message": "Gambar Base64 tidak valid.",
                }), 400

            if frame.shape[1] > 480:
                h, w = frame.shape[:2]
                new_w = 360
                new_h = int(h * (new_w / w))
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            _, result, prediction, hand_count = predict_from_frame(frame)

            return jsonify(build_response(prediction, hand_count, result)), 200

        return jsonify({
            "success": False,
            "message": (
                "Data tidak ditemukan. Kirim frame, image, "
                "atau features (126 fitur)."
            ),
        }), 400

    except Exception as error:

        app.logger.exception("Terjadi kesalahan pada API prediksi.")

        return jsonify({"success": False, "message": str(error)}), 500


# ============================================================
# 8. STATUS APLIKASI
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "application": "SignTalk",
        "mediapipe": "Tasks API",
        "hand_detection": True,
        "max_hands": MAX_HANDS,
        "feature_count": EXPECTED_FEATURES,
        "feature_version": FEATURE_VERSION,
        "model_loaded": model is not None,
    })


# ============================================================
# 9. MENJALANKAN FLASK
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("             SIGNTALK APPLICATION")
    print("=" * 55)
    print("[INFO] Server: http://127.0.0.1:5000")

    try:

        app.run(
            host="127.0.0.1",
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=True,
        )

    finally:

        hand_landmarker.close()
        print("[INFO] MediaPipe berhasil ditutup.")