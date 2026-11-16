"""Audio Transcriber: speech -> text (Parakeet TDT 0.6B, 25 European languages)

    python audio_transcriber.py            # outputs/speech.wav from text_to_speech.py
    python audio_transcriber.py --mic 5    # record 5 seconds from the microphone
"""
import mediapipe as mp

from common import audio_input, model

samples, rate = audio_input()
options = mp.tasks.audio.AudioTranscriberOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("audio_transcriber"),
                                      delegate=mp.tasks.BaseOptions.Delegate.CPU),
    sample_rate_hz=rate,                         # other rates are resampled to 16 kHz
)
with mp.tasks.audio.AudioTranscriber.create_from_options(options) as transcriber:
    result = transcriber.transcribe(samples, end_of_stream=True)

print("Transcript:", result.text)
for s in result.segments:
    print(f"  {s.from_timestamp_ms / 1000:5.1f}-{s.to_timestamp_ms / 1000:5.1f} s  {s.transcript}")
