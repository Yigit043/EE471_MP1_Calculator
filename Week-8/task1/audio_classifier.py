"""Audio Classifier: what kind of sound is this? (YAMNet, 521 sound classes)

    python audio_classifier.py            # outputs/speech.wav from text_to_speech.py
    python audio_classifier.py --mic 5    # record 5 seconds from the microphone
"""
import mediapipe as mp

from common import audio_input, model

samples, rate = audio_input()
options = mp.tasks.audio.AudioClassifierOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("audio_classifier")),
    max_results=3,
)
with mp.tasks.audio.AudioClassifier.create_from_options(options) as classifier:
    clip = mp.tasks.components.containers.AudioData.create_from_array(samples, rate)
    results = classifier.classify(clip)          # one result per ~1 second window

for r in results:
    top = r.classifications[0].categories
    t = r.timestamp_ms / 1000
    print(f"{t:5.1f} s: " + ", ".join(f"{c.category_name} {c.score:.2f}" for c in top))
