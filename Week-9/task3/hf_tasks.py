"""Task 3: one class that can do all ten Hugging Face tasks of Task 1.

    from hf_tasks import HuggingFaceTasks
    hf = HuggingFaceTasks()
    hf.sentiment("I love this course")

Every task uses a transformers pipeline. A pipeline is created the first time its task is
used (lazy loading) and then kept, so the app starts fast and only loads the models you use.
"""
import numpy as np
from transformers import pipeline

MODELS = {
    "sentiment-analysis": "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    "zero-shot-classification": "facebook/bart-large-mnli",
    "text-generation": "HuggingFaceTB/SmolLM2-360M",
    "fill-mask": "distilbert/distilroberta-base",
    "ner": "dbmdz/bert-large-cased-finetuned-conll03-english",
    "question-answering": "distilbert/distilbert-base-cased-distilled-squad",
    "summarization": "sshleifer/distilbart-cnn-12-6",
    "translation": "Helsinki-NLP/opus-mt-fr-en",
    "image-classification": "google/vit-base-patch16-224",
    "automatic-speech-recognition": "openai/whisper-large-v3",
}


class HuggingFaceTasks:
    """Ten NLP / vision / audio tasks behind simple methods."""

    def __init__(self, models=None):
        self.models = {**MODELS, **(models or {})}
        self._pipelines = {}

    def _get(self, task):
        """Create the pipeline for a task the first time, then reuse it."""
        if task not in self._pipelines:
            extra = {"aggregation_strategy": "simple"} if task == "ner" else {}
            self._pipelines[task] = pipeline(task, model=self.models[task], **extra)
        return self._pipelines[task]

    # ------------------------------------------------------------ text tasks
    def sentiment(self, text):
        """Text -> {"POSITIVE": score} or {"NEGATIVE": score}."""
        r = self._get("sentiment-analysis")(text)[0]
        return {r["label"]: r["score"]}

    def zero_shot(self, text, labels):
        """Text + candidate labels -> score for every label."""
        r = self._get("zero-shot-classification")(text, candidate_labels=labels)
        return dict(zip(r["labels"], r["scores"]))

    def generate(self, prompt, max_words=35, alternatives=2):
        """Complete a sentence; several alternatives of at most max_words words."""
        gen = self._get("text-generation")
        outs = gen(prompt, max_new_tokens=int(max_words * 1.7), num_return_sequences=alternatives,
                   do_sample=True, temperature=0.8, pad_token_id=gen.tokenizer.eos_token_id)
        return [" ".join(o["generated_text"].split()[:max_words]) for o in outs]

    def fill_mask(self, text, top_k=5):
        """Sentence with [MASK] (or <mask>) -> the most likely words for the gap."""
        unmasker = self._get("fill-mask")
        text = text.replace("[MASK]", unmasker.tokenizer.mask_token)
        return {r["token_str"].strip(): r["score"] for r in unmasker(text, top_k=top_k)}

    def ner(self, text):
        """Text -> list of (entity type, words, score)."""
        return [(e["entity_group"], e["word"], round(float(e["score"]), 4)) for e in self._get("ner")(text)]

    def answer(self, question, context):
        """Question + context text -> (answer, score)."""
        r = self._get("question-answering")(question=question, context=context)
        return r["answer"], r["score"]

    def summarize(self, text, max_length=60, min_length=20):
        return self._get("summarization")(text, max_length=max_length, min_length=min_length,
                                          do_sample=False)[0]["summary_text"]

    def translate(self, text):
        """French text -> English text."""
        return self._get("translation")(text)[0]["translation_text"]

    # ------------------------------------------------------------ image and audio
    def classify_image(self, image, top_k=5):
        """PIL image or file path -> {label: score}."""
        return {r["label"]: r["score"] for r in self._get("image-classification")(image, top_k=top_k)}

    def transcribe(self, samples, sample_rate):
        """Audio samples (numpy array) -> text. Resampled to 16 kHz, mixed to mono."""
        audio = np.asarray(samples, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if np.abs(audio).max() > 1.0:                       # int16 values from a microphone
            audio = audio / 32768.0
        if sample_rate != 16000:
            n = int(len(audio) * 16000 / sample_rate)
            audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype(np.float32)
        result = self._get("automatic-speech-recognition")(
            {"raw": audio, "sampling_rate": 16000}, generate_kwargs={"language": "english", "task": "transcribe"})
        return result["text"].strip()
