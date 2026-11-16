"""Cog runner for Task 3: image in -> "left", "right" or "straight" out."""
from cog import BaseRunner, Input, Path

from face_direction import classify, detect_face


class Runner(BaseRunner):
    def run(self, image: Path = Input(description="Photo of a face")) -> str:
        landmarks = detect_face(image)
        answer, pos = classify(landmarks)
        print(f"{image.name} -> {answer} (nose position {pos})")
        return answer
