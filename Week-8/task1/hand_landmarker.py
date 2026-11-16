"""Hand Landmarker: 21 points per hand and which hand it is (left/right)."""
import mediapipe as mp

from common import draw_points, image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-3.jpg")
options = V.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("hand_landmarker")), num_hands=2)
with V.HandLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
for hand, landmarks in zip(result.handedness, result.hand_landmarks):
    wrist = landmarks[0]
    print(f"{hand[0].category_name} hand ({hand[0].score:.2f}): {len(landmarks)} points, "
          f"wrist at x={wrist.x:.2f}, y={wrist.y:.2f}")
    draw_points(img, landmarks, V.HandLandmarksConnections.HAND_CONNECTIONS, radius=2)
label(img, f"{len(result.hand_landmarks)} hand(s)", scale=0.6)
save(img, "hand_landmarker.png")
