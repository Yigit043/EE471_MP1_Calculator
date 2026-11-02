"""Week 5 - Task 1: Flask backend for the Azure Speech website.

Part 1  POST /api/tts                  text  -> WAV
Part 2  POST /api/stt                  WAV   -> text
Part 4  POST /api/diarize              WAV   -> [{"speaker", "text"}]   (who said what)
        POST /api/translate            WAV   -> original text + translation
        POST /api/pronunciation        WAV + reference text -> scores per sentence and word
        POST /api/sample-conversation  -> WAV of a two-person dialogue (to demo diarization)

The browser always sends audio as a 16 kHz mono WAV (it converts recordings and uploads).
"""
import os
import tempfile
import threading
from xml.sax.saxutils import escape

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # finds the .env file in the repo root (walks up from this folder)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024   # 20 MB upload limit

VOICES = {
    "en-US-AvaMultilingualNeural": "English (US) - Ava",
    "en-US-AndrewMultilingualNeural": "English (US) - Andrew",
    "en-GB-SoniaNeural": "English (UK) - Sonia",
    "tr-TR-EmelNeural": "Turkish - Emel",
    "tr-TR-AhmetNeural": "Turkish - Ahmet",
    "de-DE-KatjaNeural": "German - Katja",
    "fr-FR-DeniseNeural": "French - Denise",
    "es-ES-ElviraNeural": "Spanish - Elvira",
}
LANGUAGES = {                 # spoken languages we can recognise
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "tr-TR": "Turkish",
}
TRANSLATION_TARGETS = {       # translation target -> voice used to read the translation aloud
    "tr": ("Turkish", "tr-TR-EmelNeural"),
    "en": ("English", "en-US-AvaMultilingualNeural"),
    "de": ("German", "de-DE-KatjaNeural"),
    "fr": ("French", "fr-FR-DeniseNeural"),
    "es": ("Spanish", "es-ES-ElviraNeural"),
}
PRONUNCIATION_LANGUAGES = {"en-US": "English (US)", "en-GB": "English (UK)"}
MAX_CHARS = 1000


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------
class NoSpeechError(Exception):
    """Azure heard nothing it could recognise."""


def error(message, status):
    return jsonify({"error": message}), status


def check_keys():
    if not SPEECH_KEY or not SPEECH_REGION:
        raise RuntimeError("SPEECH_KEY / SPEECH_REGION missing in .env")


def speech_config(language=None):
    """Build the Azure config from the .env values."""
    check_keys()
    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    if language:
        config.speech_recognition_language = language
    return config


def save_wav_upload():
    """Validate the uploaded WAV ("audio" field) and store it in a temp file. Returns the path."""
    upload = request.files.get("audio")
    if upload is None:
        raise ValueError("No audio received.")
    data = upload.read()
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Audio must be a WAV file.")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(data)
    tmp.close()
    return tmp.name


def remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass   # Windows may still hold the file for a moment; it is a temp file anyway


def run_until_done(start, stop, recognizer, timeout=120):
    """Start a continuous recogniser, wait until the file ends (or an error), stop it.

    Returns the list of Azure error messages (empty when everything went fine).
    """
    problems = []
    finished = threading.Event()

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            problems.append(evt.cancellation_details.error_details)
        finished.set()

    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda _evt: finished.set())
    start()
    finished.wait(timeout=timeout)
    stop()
    return problems


def audio_endpoint(work):
    """Common flow for every endpoint that receives a WAV: save -> work(path) -> clean up."""
    try:
        path = save_wav_upload()
    except ValueError as exc:
        return error(str(exc), 400)
    try:
        return jsonify(work(path))
    except ValueError as exc:
        return error(str(exc), 400)
    except NoSpeechError as exc:
        return error(str(exc), 422)
    except RuntimeError as exc:
        return error(f"Azure error: {exc}", 502)
    finally:
        remove_file(path)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/options")
def options():
    """All dropdown contents in one call (lists keep their order)."""
    return jsonify({
        "voices": [[k, v] for k, v in VOICES.items()],
        "languages": [[k, v] for k, v in LANGUAGES.items()],
        "targets": [[k, v[0]] for k, v in TRANSLATION_TARGETS.items()],
        "pronunciation": [[k, v] for k, v in PRONUNCIATION_LANGUAGES.items()],
    })


# --------------------------------------------------------------------------
# Part 1 - Text to speech
# --------------------------------------------------------------------------
def synthesize(ssml=None, text=None, voice=None, output=None):
    """Run Azure text-to-speech and return the WAV bytes."""
    config = speech_config()
    if voice:
        config.speech_synthesis_voice_name = voice
    config.set_speech_synthesis_output_format(
        output or speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    # audio_config=None -> keep the audio in memory instead of playing it on the server
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = (synthesizer.speak_ssml_async(ssml) if ssml else synthesizer.speak_text_async(text)).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    details = result.cancellation_details
    raise RuntimeError(f"{details.reason} {details.error_details or ''}".strip())


def wav_response(data, filename):
    return Response(data, mimetype="audio/wav",
                    headers={"Content-Disposition": f"inline; filename={filename}"})


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    """Convert text to a WAV file with Azure and send the bytes back."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    voice = data.get("voice", "en-US-AvaMultilingualNeural")

    if not text:
        return error("Please enter some text.", 400)
    if len(text) > MAX_CHARS:
        return error(f"Text is too long (max {MAX_CHARS} characters).", 400)
    if voice not in VOICES:
        return error("Unknown voice.", 400)
    try:
        return wav_response(synthesize(text=text, voice=voice), "speech.wav")
    except RuntimeError as exc:
        return error(f"Azure error: {exc}", 502)


# --------------------------------------------------------------------------
# Part 2 - Speech to text
# --------------------------------------------------------------------------
@app.route("/api/stt", methods=["POST"])
def speech_to_text():
    """Receive a WAV file, transcribe it with Azure, return the text."""
    language = request.form.get("language", "en-US")
    if language not in LANGUAGES:
        return error("Unknown language.", 400)

    def work(path):
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config(language),
            audio_config=speechsdk.audio.AudioConfig(filename=path),
        )
        pieces = []
        recognizer.recognized.connect(
            lambda evt: pieces.append(evt.result.text)
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text
            else None
        )
        problems = run_until_done(recognizer.start_continuous_recognition,
                                  recognizer.stop_continuous_recognition, recognizer)
        if problems and not pieces:
            raise RuntimeError(problems[0])
        if not pieces:
            raise NoSpeechError("No speech could be recognised in the audio.")
        return {"text": " ".join(pieces), "language": language}

    return audio_endpoint(work)


# --------------------------------------------------------------------------
# Part 4a - Real-time diarization (who said what)
# --------------------------------------------------------------------------
@app.route("/api/diarize", methods=["POST"])
def diarize():
    """ConversationTranscriber labels every sentence with a speaker id (Guest-1, Guest-2 ...)."""
    language = request.form.get("language", "en-US")
    if language not in LANGUAGES:
        return error("Unknown language.", 400)

    def work(path):
        transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=speech_config(language),
            audio_config=speechsdk.audio.AudioConfig(filename=path),
        )
        segments = []

        def on_transcribed(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
                segments.append({"speaker": evt.result.speaker_id or "Unknown",
                                 "text": evt.result.text})

        transcriber.transcribed.connect(on_transcribed)
        problems = run_until_done(lambda: transcriber.start_transcribing_async().get(),
                                  lambda: transcriber.stop_transcribing_async().get(),
                                  transcriber)
        if problems and not segments:
            raise RuntimeError(problems[0])
        if not segments:
            raise NoSpeechError("No speech could be recognised in the audio.")
        return {"segments": segments}

    return audio_endpoint(work)


@app.route("/api/sample-conversation", methods=["POST"])
def sample_conversation():
    """A short two-voice dialogue made with Azure TTS, so diarization can be demoed alone."""
    lines = [
        ("en-US-AvaMultilingualNeural", "Hi Andrew. Did you finish the EE471 homework?"),
        ("en-US-AndrewMultilingualNeural", "Almost. I still have to resolve a merge conflict."),
        ("en-US-AvaMultilingualNeural", "Keep both features, then commit the merge."),
        ("en-US-AndrewMultilingualNeural", "Good idea. After that I will add speech translation."),
    ]
    body = "".join(
        f"<voice name='{voice}'>{escape(text)}<break time='800ms'/></voice>" for voice, text in lines
    )
    ssml = ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' "
            f"xml:lang='en-US'>{body}</speak>")
    try:
        audio = synthesize(ssml=ssml,
                           output=speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    except RuntimeError as exc:
        return error(f"Azure error: {exc}", 502)
    return wav_response(audio, "conversation.wav")


# --------------------------------------------------------------------------
# Part 4b - Speech translation
# --------------------------------------------------------------------------
@app.route("/api/translate", methods=["POST"])
def translate():
    """TranslationRecognizer: recognises the speech and translates it in one step."""
    source = request.form.get("source", "en-US")
    target = request.form.get("target", "tr")
    if source not in LANGUAGES:
        return error("Unknown source language.", 400)
    if target not in TRANSLATION_TARGETS:
        return error("Unknown target language.", 400)

    def work(path):
        check_keys()
        config = speechsdk.translation.SpeechTranslationConfig(
            subscription=SPEECH_KEY, region=SPEECH_REGION)
        config.speech_recognition_language = source
        config.add_target_language(target)
        recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=config,
            audio_config=speechsdk.audio.AudioConfig(filename=path),
        )
        originals, translations = [], []

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech and evt.result.text:
                originals.append(evt.result.text)
                translations.append(evt.result.translations.get(target, ""))

        recognizer.recognized.connect(on_recognized)
        problems = run_until_done(recognizer.start_continuous_recognition,
                                  recognizer.stop_continuous_recognition, recognizer)
        if problems and not originals:
            raise RuntimeError(problems[0])
        if not originals:
            raise NoSpeechError("No speech could be recognised in the audio.")
        return {
            "original": " ".join(originals),
            "translation": " ".join(translations),
            "voice": TRANSLATION_TARGETS[target][1],   # the page uses it to read the translation
        }

    return audio_endpoint(work)


# --------------------------------------------------------------------------
# Part 4c - Pronunciation assessment
# --------------------------------------------------------------------------
@app.route("/api/pronunciation", methods=["POST"])
def pronunciation():
    """Compare what the user said with a reference sentence and score it (0-100)."""
    language = request.form.get("language", "en-US")
    reference = request.form.get("reference", "").strip()
    if language not in PRONUNCIATION_LANGUAGES:
        return error("Unknown language.", 400)
    if not reference:
        return error("Please enter the sentence you will read.", 400)
    if len(reference) > 300:
        return error("Reference sentence is too long (max 300 characters).", 400)

    def work(path):
        assessment = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,          # detect omitted / inserted words
        )
        if language == "en-US":
            assessment.enable_prosody_assessment()   # intonation / rhythm score (en-US only)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config(language),
            audio_config=speechsdk.audio.AudioConfig(filename=path),
        )
        assessment.apply_to(recognizer)
        result = recognizer.recognize_once_async().get()   # one sentence (max ~30 s)

        if result.reason == speechsdk.ResultReason.NoMatch:
            raise NoSpeechError("No speech could be recognised in the audio.")
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise RuntimeError(result.cancellation_details.error_details)

        scores = speechsdk.PronunciationAssessmentResult(result)
        return {
            "recognized": result.text,
            "pronunciation": scores.pronunciation_score,
            "accuracy": scores.accuracy_score,
            "fluency": scores.fluency_score,
            "completeness": scores.completeness_score,
            "prosody": scores.prosody_score,
            "words": [
                {"word": w.word, "accuracy": w.accuracy_score, "error": w.error_type}
                for w in scores.words
            ],
        }

    return audio_endpoint(work)


if __name__ == "__main__":
    app.run(debug=True)   # macOS: app.run(debug=True, port=5001)
