"""Task 1 - Automatic speech recognition with OpenAI's Whisper large-v3.

    python Task1_automatic_speech_recognition.py              # ../samples/speech.wav
    python Task1_automatic_speech_recognition.py my_voice.wav # any 16-bit WAV file
The WAV file is read with Python's wave module, so ffmpeg is not needed.
"""
import sys
import wave
from pathlib import Path

import numpy as np
from transformers import pipeline


def load_wav_16k(path):
    """16-bit WAV -> mono float32 samples at 16 kHz (the rate Whisper expects)."""
    with wave.open(str(path), "rb") as f:
        rate, channels = f.getframerate(), f.getnchannels()
        audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if rate != 16000:                                    # simple resampling by interpolation
        n = int(len(audio) * 16000 / rate)
        audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype(np.float32)
    return audio


path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parents[1] / "samples" / "speech.wav"
asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")
result = asr({"raw": load_wav_16k(path), "sampling_rate": 16000},
             generate_kwargs={"language": "english", "task": "transcribe"})
print(f"Audio: {Path(path).name}\nText : {result['text'].strip()}")
