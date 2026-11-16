"""Text Classifier: is a sentence positive or negative? (BERT, trained on movie reviews)"""
import mediapipe as mp

from common import model

options = mp.tasks.text.TextClassifierOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("text_classifier")))
texts = ["This movie was absolutely wonderful, I loved every minute.",
         "The plot was boring and the acting was terrible.",
         "The lecture today was clear and really helpful."]
with mp.tasks.text.TextClassifier.create_from_options(options) as classifier:
    for t in texts:
        cats = classifier.classify(t).classifications[0].categories
        best = max(cats, key=lambda c: c.score)
        print(f"{best.category_name:9s} {best.score:.2f}  {t}")
