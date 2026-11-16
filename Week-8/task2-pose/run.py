"""Cog runner for Task 2: image in -> "left", "right", "both" or "None" out."""
from cog import BaseRunner, Input, Path

from arm_up import classify, detect_pose


class Runner(BaseRunner):
    def run(self, image: Path = Input(description="Photo of a person")) -> str:
        landmarks = detect_pose(image)
        answer = classify(landmarks)
        print(f"{image.name} -> {answer}")
        return answer
