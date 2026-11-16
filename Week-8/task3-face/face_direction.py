"""Task 3: where is the face looking?  Output: "left", "right" or "straight".

    python face_direction.py ../images/face-1.png          -> prints left
    python face_direction.py ../images/face-1.png --save   -> also writes face-1_result.png

"left" and "right" are as seen in the picture: "left" means the face is turned
towards the left side of the image.

Idea: when a face turns, the nose tip moves towards one edge of the face.
We measure where the nose tip lies between the left and right edges of the face:
    0.0 = at the left edge, 0.5 = in the middle, 1.0 = at the right edge.
"""
import os
import sys
import urllib.request
from pathlib import Path

import mediapipe as mp

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
             "face_landmarker/float16/latest/face_landmarker.task")
MODEL_PATHS = [Path("/models/face_landmarker.task"),                       # inside the Cog image
               Path(__file__).parent / "models" / "face_landmarker.task"]  # on your computer

NOSE_TIP = 1             # Face Landmarker (478 points): tip of the nose
FACE_EDGES = (234, 454)  # the two outer edges of the face, at cheek height
STRAIGHT_ZONE = (0.40, 0.60)


def get_model():
    """Return the model file; download it (about 4 MB) the first time."""
    for path in MODEL_PATHS:
        if path.exists():
            return str(path)
    path = MODEL_PATHS[1]
    path.parent.mkdir(exist_ok=True)
    print(f"Downloading the face model to {path} ...", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URL, path)
    return str(path)


def detect_face(image_path):
    """Run MediaPipe Face Landmarker; return the 478 landmarks of one face, or None."""
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=get_model()),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        num_faces=1,
    )
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp.Image.create_from_file(str(image_path)))
    return result.face_landmarks[0] if result.face_landmarks else None


def nose_position(landmarks):
    """Where the nose tip lies between the face edges: 0 = left edge, 1 = right edge."""
    a, b = (landmarks[i].x for i in FACE_EDGES)
    left_edge, right_edge = min(a, b), max(a, b)
    return (landmarks[NOSE_TIP].x - left_edge) / (right_edge - left_edge)


def classify(landmarks):
    """478 landmarks -> "left", "right" or "straight" (and the measured position)."""
    if landmarks is None:
        return "straight", None          # no face found: the task allows only these three answers
    pos = nose_position(landmarks)
    if pos < STRAIGHT_ZONE[0]:
        return "left", pos
    if pos > STRAIGHT_ZONE[1]:
        return "right", pos
    return "straight", pos


def save_result(image_path, landmarks, answer, pos):
    """Draw the nose tip, the face edges and the answer on a copy of the image."""
    import cv2
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    if landmarks is not None:
        for i, color in [(FACE_EDGES[0], (255, 0, 0)), (FACE_EDGES[1], (255, 0, 0)), (NOSE_TIP, (0, 0, 255))]:
            p = landmarks[i]
            cv2.circle(img, (int(p.x * w), int(p.y * h)), 5, color, -1)
    text = f"looking: {answer}" + (f" ({pos:.2f})" if pos is not None else "")
    cv2.putText(img, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
    cv2.putText(img, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
    out = Path(image_path).with_name(Path(image_path).stem + "_result.png")
    cv2.imwrite(str(out), img)
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python face_direction.py <image> [--save]")
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        sys.exit(f"file not found: {image_path}")
    landmarks = detect_face(image_path)
    answer, pos = classify(landmarks)
    print(answer)
    if "--save" in sys.argv:
        print(f"(nose position {pos}; picture: {save_result(image_path, landmarks, answer, pos)})",
              file=sys.stderr)


if __name__ == "__main__":
    main()
