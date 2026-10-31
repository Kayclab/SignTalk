import os
import cv2
import joblib
import numpy as np
import pandas as pd
import mediapipe as mp

from flask import Flask, render_template, request, jsonify

# 1. INISIALISASI APLIKASI

app = Flask(__name__)

MODEL_PATH = "model/random_forest.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "Model tidak ditemukan. "
        "Pastikan model/random_forest.pkl tersedia."
    )

model = joblib.load(MODEL_PATH)

print("Model Random Forest berhasil dimuat!")
print("Jumlah kelas:", len(model.classes_))


# 2. INISIALISASI MEDIAPIPE

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)


# 3. EKSTRAKSI FITUR LANDMARK

def extract_hand_features(hand_landmarks):
    """
    Mengambil 21 landmark dengan koordinat x, y, z.
    Koordinat dibuat relatif terhadap wrist.
    """

    features = []

    wrist = hand_landmarks.landmark[0]

    for landmark in hand_landmarks.landmark:
        x = landmark.x - wrist.x
        y = landmark.y - wrist.y
        z = landmark.z - wrist.z

        features.extend([x, y, z])

    return features


def extract_features(results):
    """
    Menghasilkan 126 fitur:
    63 fitur tangan pertama dan
    63 fitur tangan kedua.
    """

    features = [0.0] * 126

    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(
            results.multi_hand_landmarks[:2]
        ):
            hand_features = extract_hand_features(
                hand_landmarks
            )

            start = i * 63
            features[start:start + 63] = hand_features

    return features


# 4. HALAMAN UTAMA

@app.route("/")
def index():
    return render_template("index.html")


# 5. API PREDIKSI

@app.route("/api/predict", methods=["POST"])
def predict():

    try:
        # Memastikan gambar dikirim
        if "frame" not in request.files:
            return jsonify({
                "success": False,
                "message": "Gambar tidak ditemukan."
            }), 400

        file = request.files["frame"]

        # Membaca gambar
        image_bytes = np.frombuffer(
            file.read(),
            np.uint8
        )

        frame = cv2.imdecode(
            image_bytes,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            return jsonify({
                "success": False,
                "message": "Gambar tidak dapat dibaca."
            }), 400

        # Mengubah BGR menjadi RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Deteksi landmark tangan
        results = hands_detector.process(rgb_frame)

        # Memeriksa apakah tangan terdeteksi
        if not results.multi_hand_landmarks:
            return jsonify({
                "success": True,
                "detected": False,
                "message": "Tangan tidak terdeteksi."
            })

        # Ekstraksi 126 fitur
        features = extract_features(results)

        # Menyiapkan fitur sesuai nama kolom dataset
        columns = [f"x{i}" for i in range(126)]

        input_data = pd.DataFrame(
            [features],
            columns=columns
        )

        # Prediksi menggunakan Random Forest
        prediction = model.predict(input_data)[0]

        # Mengambil probabilitas prediksi tertinggi
        probabilities = model.predict_proba(input_data)[0]

        confidence = float(np.max(probabilities)) * 100

        return jsonify({
            "success": True,
            "detected": True,
            "prediction": str(prediction),
            "confidence": round(confidence, 2),
            "detected_hands": len(
                results.multi_hand_landmarks
            )
        })

    except Exception as e:
        print("Prediction error:", str(e))

        return jsonify({
            "success": False,
            "message": "Terjadi kesalahan saat melakukan prediksi."
        }), 500


# 6. MENJALANKAN SERVER

if __name__ == "__main__":
    print("\nSignTalk Flask Server berjalan...")
    print("Buka browser: http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
