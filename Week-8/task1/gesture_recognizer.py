"""Gesture Recognizer: hand gestures like Closed_Fist, Open_Palm, Thumb_Up, Victory."""
import mediapipe as mp

from common import draw_points, image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-3.jpg")                   # both fists raised
options = V.GestureRecognizerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("gesture_recognizer")), num_hands=2)
with V.GestureRecognizer.create_from_options(options) as recognizer:
    result = recognizer.recognize(mp.Image.create_from_file(path))

img = load_bgr(path)
texts = []
for gestures, hand, landmarks in zip(result.gestures, result.handedness, result.hand_landmarks):
    g, side = gestures[0], hand[0]
    texts.append(f"{side.category_name}: {g.category_name}")
    print(f"{side.category_name} hand: {g.category_name} ({g.score:.2f})")
    draw_points(img, landmarks, V.HandLandmarksConnections.HAND_CONNECTIONS, radius=2)
for i, t in enumerate(texts or ["no hands"]):              # one line per hand, so it fits
    label(img, t, (10, 25 + 25 * i), 0.55)
save(img, "gesture_recognizer.png")
