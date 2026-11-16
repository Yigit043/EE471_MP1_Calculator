"""Pose Landmarker: 33 body points (nose, shoulders, elbows, wrists, hips, knees, ankles ...)."""
import mediapipe as mp

from common import draw_points, image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("pose-1.jpg")
options = V.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("pose_landmarker")))
with V.PoseLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
for pose in result.pose_landmarks:
    for i in (V.PoseLandmark.NOSE, V.PoseLandmark.LEFT_WRIST, V.PoseLandmark.RIGHT_WRIST,
              V.PoseLandmark.LEFT_ANKLE, V.PoseLandmark.RIGHT_ANKLE):
        p = pose[i]
        print(f"{i.name:12s} x={p.x:.2f} y={p.y:.2f} visibility={p.visibility:.2f}")
    draw_points(img, pose, V.PoseLandmarksConnections.POSE_LANDMARKS)
label(img, f"{len(result.pose_landmarks)} person, 33 points", scale=0.5)
save(img, "pose_landmarker.png")
