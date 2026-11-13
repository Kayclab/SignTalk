"""
scripts/collect_data.py  (versi diperbaiki)

Pemakaian (dari root proyek):  python scripts/collect_data.py

Perbedaan penting dari versi lama:
  - Frame DICERMINKAN sebelum deteksi (sama dengan app.py)
  - Memakai signtalk/features.py (standar fitur yang sama dengan training & app)
  - Menyimpan ke dataset/dataset_v2.csv (kolom f_0..f_125, label di akhir)
  - Bisa menetapkan jumlah tangan yang diharapkan, sehingga frame dengan
    tangan kedua yang gagal terdeteksi TIDAK ikut tersimpan (data bersih)
  - Mode rekam otomatis (tekan A) untuk mengumpulkan banyak variasi

Kontrol:  S = simpan 1 sampel | A = rekam otomatis ON/OFF | Q = keluar
"""

import csv
import sys
import time
from pathlib import Path

# root proyek -> agar `import signtalk` berfungsi saat dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2

from signtalk.features import (
    FEATURE_COLUMNS,
    MIRROR_INPUT,
    create_landmarker,
    detect_bgr,
    extract_features,
)

from signtalk.paths import (
    DATASET_DIR as DATA_DIR,
    DATASET_PATH as CSV_PATH,
    TASK_MODEL_PATH,
)

DATA_DIR.mkdir(exist_ok=True)

CAMERA_INDEX = 0
AUTO_INTERVAL_SEC = 0.15   # jeda rekam otomatis

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


def draw_landmarks(frame, hand_landmarks):
    height, width, _ = frame.shape
    points = [(int(p.x * width), int(p.y * height)) for p in hand_landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, points[a], points[b], (0, 255, 0), 2)
    for point in points:
        cv2.circle(frame, point, 4, (0, 0, 255), -1)


def existing_labels():
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        return sorted({row[-1] for row in reader if row})


def check_header():
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(FEATURE_COLUMNS + ["label"])
        return
    with open(CSV_PATH, newline="", encoding="utf-8") as file:
        header = next(csv.reader(file), [])
    if header != FEATURE_COLUMNS + ["label"]:
        raise SystemExit(
            "[ERROR] dataset_v2.csv tidak berformat v2. "
            "Jalankan: python scripts/prepare_dataset.py"
        )


# ------------------------------------------------------------
# Input label dan jumlah tangan
# ------------------------------------------------------------
print("=" * 58)
print("          SIGNTALK DATASET COLLECTOR (v2)")
print("=" * 58)

labels_known = existing_labels()
if labels_known:
    print("Label yang sudah ada:", ", ".join(labels_known))

label = input("Label yang ingin direkam: ").strip()
if not label:
    raise SystemExit("[ERROR] Label tidak boleh kosong.")

# samakan penulisan dengan label yang sudah ada (mis. 'bisa' -> 'Bisa')
lookup = {name.lower(): name for name in labels_known}
if label.lower() in lookup:
    label = lookup[label.lower()]
elif len(label) == 1:
    label = label.upper()

hands_answer = input(
    "Jumlah tangan untuk isyarat ini (1 atau 2, Enter = bebas): "
).strip()
required_hands = int(hands_answer) if hands_answer in ("1", "2") else None

print(f"\n[INFO] Label aktif   : {label}")
print(f"[INFO] Jumlah tangan : {required_hands or 'bebas'}")

check_header()
landmarker = create_landmarker(TASK_MODEL_PATH)

cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    landmarker.close()
    raise SystemExit("[ERROR] Webcam tidak dapat dibuka.")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

saved = 0
auto_mode = False
last_auto = 0.0
message = ""
message_until = 0.0


def save_sample(features):
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(
            [f"{v:.6f}" for v in features.tolist()] + [label]
        )


try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] Gagal membaca kamera.")
            break

        if MIRROR_INPUT:
            frame = cv2.flip(frame, 1)

        height, width = frame.shape[:2]
        result = detect_bgr(landmarker, frame)
        hands = result.hand_landmarks
        hand_count = len(hands)

        for hand in hands:
            draw_landmarks(frame, hand)

        features = extract_features(hands, width, height) if hand_count else None
        hands_ok = features is not None and (
            required_hands is None or hand_count == required_hands
        )

        wants_save = False
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("a"):
            auto_mode = not auto_mode
        if key == ord("s"):
            wants_save = True
        if auto_mode and time.time() - last_auto >= AUTO_INTERVAL_SEC:
            wants_save = True
            last_auto = time.time()

        if wants_save:
            if hands_ok:
                save_sample(features)
                saved += 1
            elif not auto_mode:
                message = (
                    f"Tidak disimpan: terdeteksi {hand_count} tangan, "
                    f"butuh {required_hands or '>=1'}"
                )
                message_until = time.time() + 1.5

        if hands_ok:
            status, color = f"OK ({hand_count} tangan)", (0, 255, 0)
        elif hand_count:
            status, color = f"{hand_count} tangan - BELUM SESUAI", (0, 165, 255)
        else:
            status, color = "TANGAN TIDAK TERDETEKSI", (0, 0, 255)

        cv2.putText(frame, f"Label: {label}   Tersimpan: {saved}", (15, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, status, (15, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, "REKAM OTOMATIS: " + ("ON" if auto_mode else "OFF"),
                    (15, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 255) if auto_mode else (200, 200, 200), 2)
        if time.time() < message_until:
            cv2.putText(frame, message, (15, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)
        cv2.putText(frame, "S: simpan | A: otomatis | Q: keluar",
                    (15, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (255, 255, 255), 2)
        cv2.imshow("SignTalk Dataset Collector", frame)

finally:
    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("\n" + "=" * 58)
    print(f"Label       : {label}")
    print(f"Data baru   : {saved}")
    print(f"Lokasi CSV  : {CSV_PATH}")
    print("=" * 58)