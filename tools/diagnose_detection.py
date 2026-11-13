"""
tools/diagnose_detection.py
Mengukur seberapa sering tangan TERDETEKSI untuk satu isyarat, dengan 4
konfigurasi MediaPipe pada frame yang SAMA (meniru browser: JPEG 80%, flip,
1 frame tiap 200 ms). Tujuannya membuktikan apakah masalah "tidak terdeteksi"
bisa diperbaiki lewat mode tracking atau ambang yang lebih rendah.

Pemakaian (dari root proyek):  python tools/diagnose_detection.py
Ketik label (mis. C), Enter, lalu peragakan isyarat selama 8 detik.
Kosongkan label lalu Enter untuk selesai.
Hasil: model/diagnosa_deteksi.csv
"""

import csv
import sys
import time
from pathlib import Path

# root proyek -> agar `import signtalk` berfungsi saat dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import mediapipe as mp

from signtalk.features import MIRROR_INPUT, ensure_hand_model
from signtalk.paths import DETECTION_DIAGNOSIS_PATH as OUT_PATH
from signtalk.paths import TASK_MODEL_PATH

TASK_PATH = ensure_hand_model(TASK_MODEL_PATH)

SEND_INTERVAL = 0.1     # ~frame rate browser (MIN_FRAME_GAP_MS + waktu proses server)
COUNTDOWN_SEC = 3
RECORD_SEC = 8

vision = mp.tasks.vision
IMAGE = vision.RunningMode.IMAGE
VIDEO = vision.RunningMode.VIDEO


def make(mode, threshold):
    options = vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(TASK_PATH)),
        running_mode=mode,
        num_hands=2,
        min_hand_detection_confidence=threshold,
        min_hand_presence_confidence=threshold,
        min_tracking_confidence=threshold,
    )
    return vision.HandLandmarker.create_from_options(options)


CONFIGS = [
    ("A. IMAGE 0.4 (app sekarang)", IMAGE, 0.4),
    ("B. IMAGE 0.2", IMAGE, 0.2),
    ("C. VIDEO 0.4 (tracking)", VIDEO, 0.4),
    ("D. VIDEO 0.2 (tracking)", VIDEO, 0.2),
]
landmarkers = [make(mode, thr) for _, mode, thr in CONFIGS]
clock_ms = 0


def detect_all(frame_bgr):
    """Mengembalikan jumlah tangan terdeteksi untuk tiap konfigurasi."""
    global clock_ms
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    clock_ms += int(SEND_INTERVAL * 1000)
    counts = []
    for (_, mode, _), landmarker in zip(CONFIGS, landmarkers):
        if mode == VIDEO:
            result = landmarker.detect_for_video(image, clock_ms)
        else:
            result = landmarker.detect(image)
        counts.append(len(result.hand_landmarks))
    return counts


def prepare(raw):
    ok, buf = cv2.imencode(".jpg", raw, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return cv2.flip(frame, 1) if MIRROR_INPUT else frame


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Webcam tidak dapat dibuka.")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

rows = []
print("=" * 64)
print("  DIAGNOSA DETEKSI TANGAN  (kosongkan label untuk selesai)")
print("=" * 64)

try:
    while True:
        label = input("\nIsyarat yang diuji (mis. C): ").strip()
        if not label:
            break

        end = time.time() + COUNTDOWN_SEC
        while time.time() < end:
            ok, raw = cap.read()
            if ok:
                view = prepare(raw)
                cv2.putText(view, f"Bersiap: {label} ({end - time.time():.0f})",
                            (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                            (0, 255, 255), 2)
                cv2.imshow("Diagnosa deteksi", view)
                cv2.waitKey(1)

        total = 0
        hits = [0] * len(CONFIGS)
        last = 0.0
        end = time.time() + RECORD_SEC
        while time.time() < end:
            ok, raw = cap.read()
            if not ok:
                continue
            view = prepare(raw)
            if time.time() - last >= SEND_INTERVAL:
                last = time.time()
                counts = detect_all(view)
                total += 1
                for i, c in enumerate(counts):
                    hits[i] += 1 if c > 0 else 0
            cv2.putText(view, f"Rekam: {label}", (15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.imshow("Diagnosa deteksi", view)
            cv2.waitKey(1)

        pct = [h / total * 100 if total else 0 for h in hits]
        print(f"\n  {label}  ({total} frame)")
        for (name, _, _), p in zip(CONFIGS, pct):
            print(f"    {name:<30s} terdeteksi {p:5.1f}%")
        rows.append([label, total] + [round(p, 1) for p in pct])
finally:
    cap.release()
    cv2.destroyAllWindows()
    for landmarker in landmarkers:
        landmarker.close()

if rows:
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["label", "frame"] + [c[0] for c in CONFIGS])
        writer.writerows(rows)
    print("\nDisimpan:", OUT_PATH)