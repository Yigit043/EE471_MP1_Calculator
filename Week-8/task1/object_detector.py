"""Object Detector: find objects with boxes and names (EfficientDet-Lite0, 80 COCO classes)."""
import cv2
import mediapipe as mp

from common import image, label, load_bgr, model, save

path = image("pose-2.jpg")
options = mp.tasks.vision.ObjectDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("object_detector")),
    max_results=5, score_threshold=0.3)
with mp.tasks.vision.ObjectDetector.create_from_options(options) as detector:
    result = detector.detect(mp.Image.create_from_file(path))

img = load_bgr(path)
for det in result.detections:
    b, c = det.bounding_box, det.categories[0]
    print(f"{c.category_name} {c.score:.2f}  box x={b.origin_x} y={b.origin_y} {b.width}x{b.height}")
    cv2.rectangle(img, (b.origin_x, b.origin_y), (b.origin_x + b.width, b.origin_y + b.height), (0, 255, 0), 2)
    label(img, f"{c.category_name} {c.score:.2f}", (b.origin_x + 4, b.origin_y + 20), 0.5)
save(img, "object_detector.png")
