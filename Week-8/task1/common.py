"""Shared helpers for the Task 1 demos: model files, images, audio files and drawing."""
import os
import sys
import urllib.request
import wave
from pathlib import Path

import numpy as np


def _hide_native_logs():
    """MediaPipe's C++ code prints many INFO/WARNING lines to the console.
    Send those to nowhere, but keep Python's own messages and errors visible.
    Set MP_VERBOSE=1 to see everything again."""
    if os.getenv("MP_VERBOSE"):
        return
    os.environ.setdefault("GLOG_minloglevel", "2")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    sys.stderr.flush()
    python_stderr = os.dup(2)                      # keep a handle to the real console
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)                            # native code writes here -> discarded
    sys.stderr = os.fdopen(python_stderr, "w", buffering=1)


_hide_native_logs()

HERE = Path(__file__).parent
MODELS_DIR = HERE / "models"
OUTPUT_DIR = HERE / "outputs"
IMAGES = HERE.parent / "images"

GCS = "https://storage.googleapis.com/mediapipe-models"
HF = "https://huggingface.co/litert-community"

# name -> download URL (the file keeps its original name; the new tasks need it)
MODELS = {
    # audio
    "audio_classifier": f"{GCS}/audio_classifier/yamnet/float32/latest/yamnet.tflite",
    "audio_transcriber": f"{HF}/parakeet-tdt-0.6b-v3/resolve/main/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm",
    "text_to_speech": f"{HF}/pocket-tts/resolve/main/pocket_tts_en_int8.litertlm",
    # decision + retrieval (one EmbeddingGemma 2 model shared by all three)
    "embedding_gemma": f"{HF}/embeddinggemma-2-text-vision-440m-litert-lm/resolve/main/embeddinggemma-2-text-vision-440m.litertlm",
    # text
    "language_detector": f"{GCS}/language_detector/language_detector/float32/latest/language_detector.tflite",
    "text_classifier": f"{GCS}/text_classifier/bert_classifier/float32/latest/bert_classifier.tflite",
    "text_embedder": f"{GCS}/text_embedder/universal_sentence_encoder/float32/latest/universal_sentence_encoder.tflite",
    "text_proofreader": f"{GCS}/text_proofreader/200m/latest/proofread_quant_200m.litertlm",
    "text_summarizer": f"{GCS}/text_summarizer/200m/latest/summarization_quant_200m_2modes.litertlm",
    # vision
    "face_detector": f"{GCS}/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "face_landmarker": f"{GCS}/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
    "gesture_recognizer": f"{GCS}/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task",
    "hand_landmarker": f"{GCS}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "holistic_landmarker": f"{GCS}/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task",
    "image_classifier": f"{GCS}/image_classifier/efficientnet_lite0/float32/latest/efficientnet_lite0.tflite",
    "image_embedder": f"{GCS}/image_embedder/mobilenet_v3_small/float32/latest/mobilenet_v3_small.tflite",
    "image_segmenter": f"{GCS}/image_segmenter/deeplab_v3/float32/latest/deeplab_v3.tflite",
    "interactive_segmenter": f"{GCS}/interactive_segmenter_v2/magic_touch/int8/latest/interactive_segmentation.task",
    "object_detector": f"{GCS}/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite",
    "pose_landmarker": f"{GCS}/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
}


def model(name):
    """Path of a model file; downloads it into models/ the first time."""
    url = MODELS[name]
    path = MODELS_DIR / url.rsplit("/", 1)[-1]
    if not path.exists():
        MODELS_DIR.mkdir(exist_ok=True)
        print(f"Downloading {path.name} ...", file=sys.stderr)
        tmp = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(url, tmp, _progress)
        tmp.rename(path)
        print(file=sys.stderr)
    return str(path)


def _progress(blocks, block_size, total):
    if total > 0:
        done = min(blocks * block_size, total)
        print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB", end="", file=sys.stderr)


def image(name):
    """Path of a test image in Week-8/images."""
    return str(IMAGES / name)


def output(name):
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR / name


# ---------------------------------------------------------------- audio files
def save_wav(path, samples, sample_rate):
    """Float samples in [-1, 1] -> 16-bit mono WAV file."""
    pcm = (np.clip(np.asarray(samples, dtype=np.float32), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(int(sample_rate))
        f.writeframes(pcm.tobytes())


def load_wav(path):
    """16-bit WAV file -> (float samples in [-1, 1], sample rate). Stereo is mixed to mono."""
    with wave.open(str(path), "rb") as f:
        rate, channels = f.getframerate(), f.getnchannels()
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def record(seconds, rate=16000):
    """Record from the microphone (sounddevice comes with mediapipe)."""
    import sounddevice as sd
    print(f"Recording {seconds} s ... speak now", file=sys.stderr)
    data = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="float32")
    sd.wait()
    return data[:, 0], rate


def audio_input(default="speech.wav"):
    """Audio for the audio demos: `--mic 5` records 5 s, a path uses that file,
    otherwise outputs/speech.wav made by text_to_speech.py."""
    args = sys.argv[1:]
    if args and args[0] == "--mic":
        return record(float(args[1]) if len(args) > 1 else 5)
    path = Path(args[0]) if args else output(default)
    if not path.exists():
        sys.exit(f"{path} not found - run text_to_speech.py first, or use --mic 5")
    print(f"Audio file: {path}", file=sys.stderr)
    return load_wav(path)


# ---------------------------------------------------------------- drawing
def load_bgr(path):
    import cv2
    return cv2.imread(str(path))


def draw_points(img, landmarks, connections=(), color=(0, 255, 0), radius=3):
    """Draw normalized landmarks (x, y in 0..1) and the lines between them."""
    import cv2
    h, w = img.shape[:2]
    pts = [(int(p.x * w), int(p.y * h)) for p in landmarks]
    for c in connections:
        cv2.line(img, pts[c.start], pts[c.end], (255, 255, 255), 1)
    for p in pts:
        cv2.circle(img, p, radius, color, -1)


def label(img, text, xy=(10, 25), scale=0.7):
    import cv2
    cv2.putText(img, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3)
    cv2.putText(img, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 230, 0), 2)


def save(img, name):
    import cv2
    path = output(name)
    cv2.imwrite(str(path), img)
    print(f"Result picture: {path}")
    return path

