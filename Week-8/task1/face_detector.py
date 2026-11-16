"""Face Detector: find faces, give a box and 6 key points (eyes, nose, mouth, ears)."""
import cv2
import mediapipe as mp

from common import image, label, load_bgr, model, save

path = image("face-3.png")
options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("face_detector")))
with mp.tasks.vision.FaceDetector.create_from_options(options) as detector:
    result = detector.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
h, w = img.shape[:2]
for det in result.detections:
    b = det.bounding_box
    cv2.rectangle(img, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height), (0, 255, 0), 2)
    for k in det.keypoints:
        cv2.circle(img, (int(k.x * w), int(k.y * h)), 4, (0, 0, 255), -1)
    print(f"Face: score {det.categories[0].score:.2f}, box x={b.origin_x} y={b.origin_y} {b.width}x{b.height}")
label(img, f"{len(result.detections)} face(s)")
save(img, "face_detector.png")
