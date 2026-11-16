"""Face Landmarker: 478 points on the face + 52 expression scores (blendshapes)."""
import mediapipe as mp

from common import draw_points, image, label, load_bgr, model, save

V = mp.tasks.vision
path = image("face-3.png")
options = V.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("face_landmarker")),
    output_face_blendshapes=True, num_faces=1)
with V.FaceLandmarker.create_from_options(options) as landmarker:
    result = landmarker.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
for face in result.face_landmarks:
    print(f"Face with {len(face)} landmarks")
    draw_points(img, face, V.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS, radius=1)
for shapes in result.face_blendshapes:
    top = sorted(shapes, key=lambda c: c.score, reverse=True)[:5]
    print("Strongest expressions:", ", ".join(f"{c.category_name} {c.score:.2f}" for c in top))
label(img, f"{len(result.face_landmarks)} face(s), 478 points")
save(img, "face_landmarker.png")
