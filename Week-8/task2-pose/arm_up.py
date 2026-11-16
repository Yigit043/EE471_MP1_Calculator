"""Task 2: which arm is up?  Output: "left", "right", "both" or "None".

    python arm_up.py ../images/pose-1.jpg          -> prints right
    python arm_up.py ../images/pose-1.jpg --save   -> also writes pose-1_result.jpg

"left" and "right" mean the person's own arms (the same convention MediaPipe uses
for its LEFT_/RIGHT_ landmarks). A person facing the camera raising their right arm
shows it on the left side of the image.
"""
import os
import sys
import urllib.request
from pathlib import Path

import mediapipe as mp

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")
MODEL_PATHS = [Path("/models/pose_landmarker_lite.task"),                      # inside the Cog image
               Path(__file__).parent / "models" / "pose_landmarker_lite.task"]  # on your computer

Landmark = mp.tasks.vision.PoseLandmark
MIN_VISIBILITY = 0.5   # ignore a wrist the model is not sure about


def get_model():
    """Return the model file; download it (about 5 MB) the first time."""
    for path in MODEL_PATHS:
        if path.exists():
            return str(path)
    path = MODEL_PATHS[1]
    path.parent.mkdir(exist_ok=True)
    print(f"Downloading the pose model to {path} ...", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URL, path)
    return str(path)


def detect_pose(image_path):
    """Run MediaPipe Pose Landmarker; return the 33 landmarks of one person, or None."""
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=get_model()),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_poses=1,
    )
    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp.Image.create_from_file(str(image_path)))
    return result.pose_landmarks[0] if result.pose_landmarks else None


def is_arm_up(landmarks, wrist, shoulder):
    """An arm is up when its wrist is higher than the nose (image y grows downwards)."""
    w, nose = landmarks[wrist], landmarks[Landmark.NOSE]
    return w.visibility >= MIN_VISIBILITY and w.y < nose.y and w.y < landmarks[shoulder].y


def classify(landmarks):
    """33 landmarks -> "left", "right", "both" or "None"."""
    if landmarks is None:
        return "None"
    left = is_arm_up(landmarks, Landmark.LEFT_WRIST, Landmark.LEFT_SHOULDER)
    right = is_arm_up(landmarks, Landmark.RIGHT_WRIST, Landmark.RIGHT_SHOULDER)
    if left and right:
        return "both"
    if left:
        return "left"
    if right:
        return "right"
    return "None"


def save_result(image_path, landmarks, answer):
    """Draw the points we use and the answer on a copy of the image."""
    import cv2
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    if landmarks is not None:
        for idx, color in [(Landmark.NOSE, (0, 255, 255)),
                           (Landmark.LEFT_SHOULDER, (255, 0, 0)), (Landmark.LEFT_WRIST, (255, 0, 0)),
                           (Landmark.RIGHT_SHOULDER, (0, 0, 255)), (Landmark.RIGHT_WRIST, (0, 0, 255))]:
            p = landmarks[idx]
            cv2.circle(img, (int(p.x * w), int(p.y * h)), 6, color, -1)
        nose_y = int(landmarks[Landmark.NOSE].y * h)
        cv2.line(img, (0, nose_y), (w, nose_y), (0, 255, 255), 1)      # the "higher than the nose" line
    cv2.putText(img, f"arm up: {answer}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 3)
    cv2.putText(img, f"arm up: {answer}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 0), 2)
    out = Path(image_path).with_name(Path(image_path).stem + "_result.jpg")
    cv2.imwrite(str(out), img)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python arm_up.py <image> [--save]")
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        sys.exit(f"file not found: {image_path}")
    landmarks = detect_pose(image_path)
    answer = classify(landmarks)
    print(answer)
    if "--save" in sys.argv:
        print(f"(picture with the points: {save_result(image_path, landmarks, answer)})", file=sys.stderr)


if __name__ == "__main__":
    main()
