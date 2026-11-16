"""Text Summarizer: long text -> short summary (Summarization 200M, two modes)"""
import mediapipe as mp

from common import model

article = """MediaPipe is an open-source framework from Google for building machine learning
pipelines that run on the device instead of in the cloud. It offers ready-made solutions for
vision, text and audio, such as face detection, hand tracking, object detection, text
classification and speech recognition. Because the models run locally, applications keep user
data private, work without an internet connection and respond with very low latency. The same
solutions are available for Android, iOS, the web and Python, so a developer can prototype on
a laptop and then ship the same model to a phone. Recent versions add on-device generative
features like summarization and proofreading using small language models."""

T = mp.tasks.text
for mode in (T.TextSummarizerMode.TLDR, T.TextSummarizerMode.KEYPOINTS):
    options = T.TextSummarizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model("text_summarizer")), mode=mode)
    with T.TextSummarizer.create_from_options(options) as summarizer:
        print(f"--- {mode.name} ---\n{summarizer.summarize(article).summary}\n")
