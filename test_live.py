"""
test_live.py - Uji prediksi AKTUAL dengan webcam, memakai jalur yang sama
dengan aplikasi web (flip, MediaPipe mode IMAGE, kompresi JPEG 80%, fitur v2).

Cara pakai:
    python test_live.py
Ketik huruf/kata yang akan Anda peragakan (mis. A), tekan Enter, bentuk
isyaratnya saat hitung mundur selesai. Rekaman 5 detik. Ulangi untuk label
lain; kosongkan label lalu Enter untuk selesai.
Hasil ringkas dicetak dan disimpan di model/hasil_uji_live.csv
"""

import csv
import time
from collections import Counter
from pathlib import Path

import cv2
import joblib
import numpy as np

from features import (
    MIRROR_INPUT,
    create_landmarker,
    detect_bgr,
    extract_features,
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "random_forest_v2.pkl"
TASK_PATH = BASE_DIR / "hand_landmarker.task"
OUT_PATH = BASE_DIR / "model" / "hasil_uji_live.csv"

COUNTDOWN_SEC = 3
RECORD_SEC = 5

if not MODEL_PATH.exists():
    raise SystemExit("Model v2 belum ada. Jalankan train_model.py dulu.")

model = joblib.load(MODEL_PATH)
landmarker = create_landmarker(TASK_PATH)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Webcam tidak dapat dibuka.")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


def predict_frame(raw):
    # meniru browser: JPEG 80% lalu didekode lagi
    ok, buf = cv2.imencode(".jpg", raw, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if MIRROR_INPUT:
        frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    hands = detect_bgr(landmarker, frame).hand_landmarks
    if not hands:
        return frame, None, 0
    feats = extract_features(hands, w, h).reshape(1, -1)
    proba = model.predict_proba(feats)[0]
    best = int(np.argmax(proba))
    return frame, (str(model.classes_[best]), float(proba[best])), len(hands)


def show(frame, text, color=(0, 255, 0)):
    cv2.putText(frame, text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    cv2.imshow("SignTalk Uji Live", frame)
    cv2.waitKey(1)


results = []
print("=" * 58)
print("   UJI LIVE SIGNTALK  (kosongkan label untuk selesai)")
print("=" * 58)
try:
    while True:
        target = input("\nLabel yang akan diuji: ").strip()
        if not target:
            break
        known = {c.lower(): c for c in model.classes_}
        if target.lower() not in known:
            print("Label tidak dikenal model. Pilihan:", ", ".join(model.classes_))
            continue
        target = known[target.lower()]

        end = time.time() + COUNTDOWN_SEC
        while time.time() < end:
            ok, raw = cap.read()
            if ok:
                frame, _, _ = predict_frame(raw)
                show(frame, f"Bersiap: {target}  ({end - time.time():.0f})", (0, 255, 255))

        total = detected = correct = 0
        wrong = Counter()
        end = time.time() + RECORD_SEC
        while time.time() < end:
            ok, raw = cap.read()
            if not ok:
                continue
            frame, pred, hands = predict_frame(raw)
            total += 1
            if pred is None:
                show(frame, "TIDAK TERDETEKSI", (0, 0, 255))
                continue
            detected += 1
            label, conf = pred
            if label == target:
                correct += 1
            else:
                wrong[label] += 1
            color = (0, 255, 0) if label == target else (0, 0, 255)
            show(frame, f"{label} ({conf * 100:.0f}%)  tangan:{hands}", color)

        det_pct = detected / total * 100 if total else 0
        acc_pct = correct / detected * 100 if detected else 0
        top_wrong = ", ".join(f"{k} x{v}" for k, v in wrong.most_common(3)) or "-"
        print(f"  {target}: frame={total} | terdeteksi={det_pct:.0f}% | "
              f"benar (dari yang terdeteksi)={acc_pct:.0f}% | salah jadi: {top_wrong}")
        results.append([target, total, round(det_pct, 1), round(acc_pct, 1), top_wrong])
finally:
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()

if results:
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "frame", "persen_terdeteksi", "persen_benar", "salah_jadi"])
        w.writerows(results)
    mean_det = np.mean([r[2] for r in results])
    mean_acc = np.mean([r[3] for r in results])
    print(f"\nRata-rata: terdeteksi {mean_det:.0f}% | benar {mean_acc:.0f}%")
    print("Disimpan:", OUT_PATH)
