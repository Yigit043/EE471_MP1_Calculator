"""Text-to-Speech: text -> audio file (PocketTTS 100M English, runs on the CPU)

    python text_to_speech.py
    python text_to_speech.py "Any sentence you like."
Writes outputs/speech.wav; the audio classifier and transcriber demos use this file.
"""
import sys

import mediapipe as mp

from common import model, output, save_wav

text = " ".join(sys.argv[1:]) or "Hello! This is MediaPipe text to speech, running on my laptop."
options = mp.tasks.audio.TextToSpeechOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("text_to_speech"),
                                      delegate=mp.tasks.BaseOptions.Delegate.CPU),
)
with mp.tasks.audio.TextToSpeech.create_from_options(options) as tts:
    print("Voices:", ", ".join(v.voice_id for v in tts.list_voices()))
    result = tts.synthesize(text)

path = output("speech.wav")
save_wav(path, result.samples, result.sample_rate_hz)
print(f"Text: {text}")
print(f"Audio: {len(result.samples) / result.sample_rate_hz:.1f} s at {result.sample_rate_hz} Hz -> {path}")
