"""Language Detector: which language is this text written in?"""
import mediapipe as mp

from common import model

options = mp.tasks.text.LanguageDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("language_detector")), max_results=2)
texts = ["Bugün hava çok güzel, denize gidelim.", "Machine learning is fun.",
         "Je voudrais un café, s'il vous plaît.", "Wo ist der Bahnhof?", "¿Dónde está la biblioteca?"]
with mp.tasks.text.LanguageDetector.create_from_options(options) as detector:
    for t in texts:
        result = detector.detect(t)
        langs = ", ".join(f"{d.language_code} {d.probability:.2f}" for d in result.languages)
        print(f"{t:42s} -> {langs}")
