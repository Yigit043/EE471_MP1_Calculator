"""Holistic Landmarker: body pose, face and both hands in ONE model run."""
import mediapipe as mp

from common import draw_points, image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-3.jpg")
options = V.HolisticLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("holistic_landmarker")))
with V.HolisticLandmarker.create_from_options(options) as landmarker:
    r = landmarker.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
parts = {"pose": r.pose_landmarks, "face": r.face_landmarks,
         "left hand": r.left_hand_landmarks, "right hand": r.right_hand_landmarks}
for name, pts in parts.items():
    print(f"{name:10s}: {len(pts) if pts else 0} points")
if r.pose_landmarks:
    draw_points(img, r.pose_landmarks, V.PoseLandmarksConnections.POSE_LANDMARKS, (0, 255, 0))
if r.face_landmarks:
    draw_points(img, r.face_landmarks, color=(255, 200, 0), radius=1)
for hand in (r.left_hand_landmarks, r.right_hand_landmarks):
    if hand:
        draw_points(img, hand, V.HandLandmarksConnections.HAND_CONNECTIONS, (0, 0, 255), 2)
label(img, "pose + face + hands", scale=0.6)
save(img, "holistic_landmarker.png")
