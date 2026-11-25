"""Download every Hugging Face model Week 9 needs into the local Hugging Face cache.

    python download_hf_models.py            # all models (the 4 from class + 7 Task 1 models, ~5 GB new)
    python download_hf_models.py --test     # quick offline check of two small models

Only the files transformers needs are downloaded (config, tokenizer and ONE copy of the weights),
not the duplicate TensorFlow / Flax / fp32 copies. Already downloaded files are skipped and
interrupted downloads resume when you run it again.
"""
import os
import sys


def _allow_links_without_admin():
    """Windows only lets admins / Developer Mode create symlinks (WinError 1314).
    The Hugging Face cache links each snapshot file to its downloaded blob, so when a symlink is
    refused we create a hard link instead: no extra disk space and no special rights needed."""
    real_symlink = os.symlink

    def symlink_or_hardlink(src, dst, target_is_directory=False, **kwargs):
        try:
            real_symlink(src, dst, target_is_directory, **kwargs)
        except OSError:
            target = src if os.path.isabs(src) else os.path.join(os.path.dirname(dst), src)
            os.link(os.path.normpath(target), dst)

    os.symlink = symlink_or_hardlink


if os.name == "nt":
    _allow_links_without_admin()

from huggingface_hub import HfApi, snapshot_download  # noqa: E402  (after the patch above)

MODELS = {
    # the four models from the instructor's message
    "HuggingFaceTB/SmolLM2-360M": "text generation, ~0.7 GB",
    "Helsinki-NLP/opus-mt-fr-en": "French -> English translation, ~0.3 GB",
    "google/vit-base-patch16-224": "image classification, ~0.35 GB",
    "openai/whisper-large-v3": "speech recognition, ~3.1 GB",
    # Task 1 / Task 3 / Task 4: the course's default models for each pipeline
    "distilbert/distilbert-base-uncased-finetuned-sst-2-english": "sentiment analysis, ~0.27 GB",
    "facebook/bart-large-mnli": "zero-shot classification, ~1.6 GB",
    "distilbert/distilroberta-base": "mask filling, ~0.33 GB",
    "dbmdz/bert-large-cased-finetuned-conll03-english": "named entity recognition, ~1.3 GB",
    "distilbert/distilbert-base-cased-distilled-squad": "question answering, ~0.26 GB",
    "sshleifer/distilbart-cnn-12-6": "summarization, ~1.2 GB",
}
TEXT_FILES = ["*.json", "*.txt", "*.spm", "*.model", "vocab*", "merges*"]


def weight_file(repo):
    """Prefer model.safetensors; older repos only have pytorch_model.bin."""
    files = HfApi().list_repo_files(repo)
    return "model.safetensors" if "model.safetensors" in files else "pytorch_model.bin"


def download():
    failed = []
    for i, (repo, what) in enumerate(MODELS.items(), 1):
        print(f"\n[{i}/{len(MODELS)}] {repo}  ({what})")
        try:
            path = snapshot_download(repo, allow_patterns=TEXT_FILES + [weight_file(repo)],
                                     ignore_patterns=["*fp32*", "onnx/*", "coreml/*", "runs/*", "*.msgpack", "*.h5"])
            print(f"  ok: {path}")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failed.append(repo)
    print("\nAll models are ready." if not failed else f"\nFailed: {', '.join(failed)} - run again to resume.")


def test():
    """Load the two small models from the cache only (no internet) and run them once."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    from transformers import pipeline
    tr = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")
    print("Translation:", tr("Bonjour, je suis étudiant à Izmir.")[0]["translation_text"])
    gen = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M")
    print("Generation:", gen("Machine learning is", max_new_tokens=20)[0]["generated_text"])


if __name__ == "__main__":
    test() if "--test" in sys.argv else download()
