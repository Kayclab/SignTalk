
import sys
import csv
import cv2
import time
import numpy as np

from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# 1. PATH PROJECT
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from signtalk.features import (
    FEATURE_VERSION,
    MIRROR_INPUT,
    FEATURE_COLUMNS,
    create_landmarker,
    detect_bgr,
    extract_features
)

from signtalk.paths import (
    DATASET_DIR,
    TASK_MODEL_PATH
)

# ============================================================
# 2. KONFIGURASI
# ============================================================

OUTPUT_CSV = DATASET_DIR / "dataset_test_independent.csv"

PARTICIPANT_ID = "P01"
SESSION_ID = "S01"

CAMERA_INDEX = 0
AUTO_INTERVAL_SEC = 0.6

FEATURE_COUNT = 126

METADATA_COLUMNS = [
    "label",
    "participant_id",
    "session_id",
    "captured_at",
    "hand_count"
]

CSV_COLUMNS = FEATURE_COLUMNS + METADATA_COLUMNS

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

# ============================================================
# 3. PERSIAPAN CSV
# ============================================================

DATASET_DIR.mkdir(parents=True, exist_ok=True)


def prepare_csv():

    if not OUTPUT_CSV.exists() or OUTPUT_CSV.stat().st_size == 0:

        with open(
            OUTPUT_CSV,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)
            writer.writerow(CSV_COLUMNS)

    else:

        # Pastikan struktur CSV sesuai sebelum menambahkan data.
        with open(
            OUTPUT_CSV,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.reader(file)
            existing_header = next(reader, [])

        if existing_header != CSV_COLUMNS:
            raise RuntimeError(
                "Header dataset_test_independent.csv tidak sesuai "
                "dengan format collector ini. "
                "Data tidak ditambahkan agar CSV lama tidak rusak."
            )


# ============================================================
# 4. FUNGSI PENYIMPANAN
# ============================================================

def save_sample(features, label, hand_count):

    features = np.asarray(
        features,
        dtype=np.float64
    ).flatten()

    if len(features) != FEATURE_COUNT:
        print("[GAGAL] Jumlah fitur bukan 126.")
        return False

    if not np.isfinite(features).all():
        print("[GAGAL] Fitur mengandung NaN atau infinity.")
        return False

    captured_at = datetime.now(
        timezone.utc
    ).isoformat()

    row = features.tolist() + [
        label,
        PARTICIPANT_ID,
        SESSION_ID,
        captured_at,
        hand_count
    ]

    with open(
        OUTPUT_CSV,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(row)

    return True


# ============================================================
# 5. VISUALISASI LANDMARK
# ============================================================

def draw_hand_landmarks(frame, hands):

    height, width = frame.shape[:2]

    for hand_index, hand in enumerate(hands):

        if len(hand) < 21:
            continue

        points = []

        for landmark in hand:

            x = int(landmark.x * width)
            y = int(landmark.y * height)

            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))

            points.append((x, y))

        # Garis koneksi landmark
        for start_idx, end_idx in HAND_CONNECTIONS:

            cv2.line(
                frame,
                points[start_idx],
                points[end_idx],
                (0, 255, 255),
                2,
                cv2.LINE_AA
            )

        # Titik landmark
        for point in points:

            cv2.circle(
                frame,
                point,
                5,
                (255, 100, 0),
                -1,
                cv2.LINE_AA
            )

        # Wrist landmark
        cv2.circle(
            frame,
            points[0],
            8,
            (0, 255, 0),
            -1
        )

        cv2.putText(
            frame,
            f"Hand {hand_index + 1}",
            (points[0][0] + 10, points[0][1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    return frame


# ============================================================
# 6. PANEL INFORMASI
# ============================================================

def draw_panel(frame, lines):

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (10, 10),
        (430, 365),
        (20, 20, 20),
        -1
    )

    cv2.addWeighted(
        overlay,
        0.70,
        frame,
        0.30,
        0,
        frame
    )

    y = 38

    for text, color in lines:

        cv2.putText(
            frame,
            text,
            (22, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            color,
            2,
            cv2.LINE_AA
        )

        y += 30

    return frame


# ============================================================
# 7. INPUT LABEL
# ============================================================

print("=" * 60)
print("SIGNTALK - INDEPENDENT TEST DATA COLLECTOR")
print("=" * 60)

print("Partisipan :", PARTICIPANT_ID)
print("Sesi       :", SESSION_ID)

label = input(
    "Masukkan label BISINDO (A, B, 1, Belajar, dll): "
).strip()

if not label:
    print("[ERROR] Label wajib diisi.")
    sys.exit(1)

prepare_csv()

print("\nINFORMASI PENGUJIAN")
print("Label      :", label)
print("Dataset    :", OUTPUT_CSV)
print("Versi fitur:", FEATURE_VERSION)
print("Mirror     :", MIRROR_INPUT)

# ============================================================
# 8. STATUS PROGRAM
# ============================================================

landmarker = None
camera = None

auto_mode = False
last_capture_time = 0

capture_count = 0

current_features = None
current_hand_count = 0


# ============================================================
# 9. FUNGSI CAPTURE
# ============================================================

def capture_current_sample():

    global capture_count

    if current_features is None:
        print("[INFO] Fitur tangan belum valid.")
        return False

    if current_hand_count < 1:
        print("[INFO] Tangan belum terdeteksi.")
        return False

    success = save_sample(
        current_features,
        label,
        current_hand_count
    )

    if success:

        capture_count += 1

        print(
            f"[TERSIMPAN] Sampel {capture_count} | "
            f"Label: {label} | "
            f"Tangan: {current_hand_count}"
        )

    return success


# ============================================================
# 10. WEBCAM DAN MEDIAPIPE
# ============================================================

try:

    landmarker = create_landmarker(TASK_MODEL_PATH)

    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        raise RuntimeError("Webcam tidak dapat dibuka.")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nKONTROL WEBCAM")
    print("[A] AUTO ON/OFF")
    print("[S] SIMPAN MANUAL")
    print("[Q] KELUAR")
    print("=" * 60)

    while True:

        ret, frame = camera.read()

        if not ret:
            print("[ERROR] Gagal membaca webcam.")
            break

        # Orientasi harus sama dengan pipeline training
        if MIRROR_INPUT:
            frame = cv2.flip(frame, 1)

        height, width = frame.shape[:2]

        # ----------------------------------------------------
        # A. DETEKSI TANGAN
        # ----------------------------------------------------

        # PENTING:
        # Urutan parameter sesuai features.py:
        # detect_bgr(landmarker, frame)
        detected = detect_bgr(
            landmarker,
            frame
        )

        hands = detected.hand_landmarks or []

        current_hand_count = len(hands)
        current_features = None

        # ----------------------------------------------------
        # B. VISUALISASI LANDMARK
        # ----------------------------------------------------

        if current_hand_count > 0:

            frame = draw_hand_landmarks(
                frame,
                hands
            )

        # ----------------------------------------------------
        # C. EKSTRAKSI 126 FITUR
        # ----------------------------------------------------

        if current_hand_count > 0:

            extracted = extract_features(
                hands,
                width,
                height
            )

            if extracted is not None:

                extracted = np.asarray(
                    extracted,
                    dtype=np.float64
                ).flatten()

                if (
                    len(extracted) == FEATURE_COUNT
                    and np.isfinite(extracted).all()
                ):

                    current_features = extracted

        # ----------------------------------------------------
        # D. AUTO CAPTURE
        # ----------------------------------------------------

        current_time = time.time()

        if (
            auto_mode
            and current_features is not None
            and current_time - last_capture_time
            >= AUTO_INTERVAL_SEC
        ):

            if capture_current_sample():
                last_capture_time = current_time

        # ----------------------------------------------------
        # E. STATUS PIPELINE
        # ----------------------------------------------------

        if current_hand_count > 0:

            detection_status = "HAND DETECTED"
            detection_color = (0, 255, 0)

        else:

            detection_status = "NO HAND DETECTED"
            detection_color = (0, 0, 255)

        if current_features is not None:

            feature_status = "FEATURE READY"
            feature_color = (0, 255, 0)

        else:

            feature_status = "FEATURE NOT READY"
            feature_color = (0, 0, 255)

        if auto_mode:

            auto_status = "AUTO: ON"
            auto_color = (0, 255, 0)

        else:

            auto_status = "AUTO: OFF"
            auto_color = (0, 165, 255)

        panel_lines = [
            ("SIGNTALK - TEST COLLECTOR", (255, 255, 255)),
            (f"Label: {label}", (255, 255, 255)),
            (f"Hands detected: {current_hand_count}", (255, 255, 255)),
            (detection_status, detection_color),
            (feature_status, feature_color),
            (auto_status, auto_color),
            (f"Saved samples: {capture_count}", (255, 255, 255)),
            ("A: AUTO ON/OFF", (255, 255, 0)),
            ("S: MANUAL SAVE", (255, 255, 0)),
            ("Q: QUIT", (255, 255, 0))
        ]

        frame = draw_panel(
            frame,
            panel_lines
        )

        # ----------------------------------------------------
        # F. TAMPILKAN WEBCAM
        # ----------------------------------------------------

        cv2.imshow(
            "SignTalk - Hand Detection Pipeline",
            frame
        )

        # ----------------------------------------------------
        # G. INPUT KEYBOARD
        # ----------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key in (ord("a"), ord("A")):

            auto_mode = not auto_mode
            last_capture_time = 0

            print(
                "[AUTO MODE]",
                "AKTIF" if auto_mode else "NONAKTIF"
            )

        elif key in (ord("s"), ord("S")):

            capture_current_sample()

        elif key in (ord("q"), ord("Q")):

            print("[INFO] Pengujian dihentikan.")
            break

finally:

    if camera is not None:
        camera.release()

    cv2.destroyAllWindows()

    if landmarker is not None:
        landmarker.close()

    print("\n" + "=" * 60)
    print("PENGUMPULAN DATA SELESAI")
    print("=" * 60)

    print("Partisipan :", PARTICIPANT_ID)
    print("Label      :", label)
    print("Total data :", capture_count)
    print("Lokasi CSV :", OUTPUT_CSV)

    print("=" * 60)
