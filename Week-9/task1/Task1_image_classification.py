"""Task 1 - Image classification with Google's ViT (1000 ImageNet classes).

    python Task1_image_classification.py                 # the Week 8 test pictures
    python Task1_image_classification.py my_photo.jpg    # any picture
"""
import sys
from pathlib import Path

from transformers import pipeline

images = sys.argv[1:] or [str(p) for p in sorted((Path(__file__).parents[2] / "Week-8" / "images").glob("pose-*.jpg"))]
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
for path in images:
    top = classifier(path, top_k=3)
    print(f"{Path(path).name:12s} -> " + ", ".join(f"{r['label']} {r['score']:.2f}" for r in top))
