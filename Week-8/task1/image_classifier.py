"""Image Classifier: what is in the picture? (EfficientNet-Lite0, 1000 ImageNet classes)"""
import mediapipe as mp

from common import image, model

options = mp.tasks.vision.ImageClassifierOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("image_classifier")), max_results=3)
with mp.tasks.vision.ImageClassifier.create_from_options(options) as classifier:
    for name in ["pose-2.jpg", "pose-1.jpg", "face-1.png"]:
        cats = classifier.classify(mp.Image.create_from_file(image(name))).classifications[0].categories
        print(f"{name:11s} -> " + ", ".join(f"{c.category_name} {c.score:.2f}" for c in cats))
