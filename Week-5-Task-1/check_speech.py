"""Quick check that the Azure Speech key in .env works: the computer says a sentence."""
import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # reads SPEECH_KEY and SPEECH_REGION from the .env file in the repo root

key = os.getenv("SPEECH_KEY")
region = os.getenv("SPEECH_REGION")
if not key or not region:
    raise SystemExit("SPEECH_KEY or SPEECH_REGION missing in .env")

speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
speech_config.speech_synthesis_voice_name = "en-US-AvaMultilingualNeural"

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)  # plays on speakers
result = synthesizer.speak_text_async("Hello, EE471 class. The Azure key works.").get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("OK - you should have heard the sentence.")
else:
    details = result.cancellation_details
    print("FAILED:", details.reason, details.error_details)