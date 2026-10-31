
import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def extract_hand_features(hand_landmarks):
    """
    Mengambil 21 landmark (x, y, z).
    Koordinat dibuat relatif terhadap wrist.
    """

    landmarks = []

    wrist = hand_landmarks.landmark[0]

    for landmark in hand_landmarks.landmark:
        x = landmark.x - wrist.x
        y = landmark.y - wrist.y
        z = landmark.z - wrist.z

        landmarks.extend([x, y, z])

    return landmarks


def extract_features(results):
    """
    Menghasilkan 126 fitur:
    63 fitur tangan pertama + 63 fitur tangan kedua.
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


cap = cv2.VideoCapture(0)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

print("Tekan Q untuk keluar.")

while cap.isOpened():
    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

        features = extract_features(results)

        print(
            "Jumlah fitur:",
            len(features),
            "| Jumlah nilai bukan nol:",
            np.count_nonzero(features)
        )

    cv2.imshow("SignTalk - Feature Extraction", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()