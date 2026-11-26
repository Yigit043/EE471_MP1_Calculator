"""Download every model Mini Project 3 needs into the local Hugging Face cache (run once).

    python download_models.py

- HuggingFaceTB/SmolLM2-360M-Instruct : the chatbot (recommended in the PDF), ~0.7 GB
- openai/whisper-small                : speech -> text for the mic button, ~1 GB
                                        (faster than whisper-large-v3, which is already in the cache)
- stabilityai/sd-turbo                : text -> image (Stable Diffusion, 1-4 steps, CPU friendly), ~2.6 GB

Only the files the libraries need are downloaded (half-precision copy for sd-turbo).
Already downloaded files are skipped; if the internet drops, run it again to resume.
"""
import fnmatch
import os


def _allow_links_without_admin():
    """Windows refuses symlinks without admin / Developer Mode (WinError 1314);
    use a hard link instead (no extra disk space, no special rights)."""
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

TEXT_FILES = ["*.json", "*.txt", "*.model", "vocab*", "merges*"]
MODELS = {
    "HuggingFaceTB/SmolLM2-360M-Instruct": "chatbot, ~0.7 GB",
    "openai/whisper-small": "speech recognition, ~1 GB",
    "stabilityai/sd-turbo": "image generation, ~2.6 GB",
}


def weight_patterns(repo):
    """Pick ONE copy of the weights: the fp16 files of a diffusers repo, else model.safetensors."""
    files = HfApi().list_repo_files(repo)
    if "model_index.json" in files:                          # a diffusers pipeline (sd-turbo)
        fp16 = [f for f in files if fnmatch.fnmatch(f, "*/*.fp16.safetensors")]
        return ["*/*.fp16.safetensors"] if fp16 else ["*/*.safetensors"]
    return ["model.safetensors"] if "model.safetensors" in files else ["pytorch_model.bin"]


def main():
    failed = []
    for i, (repo, what) in enumerate(MODELS.items(), 1):
        print(f"\n[{i}/{len(MODELS)}] {repo}  ({what})")
        try:
            path = snapshot_download(repo, allow_patterns=TEXT_FILES + weight_patterns(repo),
                                     ignore_patterns=["*fp32*", "onnx/*", "*.msgpack", "*.h5", "*.ckpt"])
            size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(path) for f in fs)
            print(f"  ok: {path}  ({size / 1e9:.2f} GB)")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failed.append(repo)
    print("\nAll models are ready." if not failed else f"\nFailed: {', '.join(failed)} - run again to resume.")


if __name__ == "__main__":
    main()
