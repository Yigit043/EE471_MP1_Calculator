"""Download every Task 1 model into models/ (about 1.5 GB). Already downloaded files are skipped.

    python download_models.py               # all models
    python download_models.py face_detector object_detector   # only these
"""
import sys

from common import MODELS, model

names = sys.argv[1:] or list(MODELS)
failed = []
for i, name in enumerate(names, 1):
    print(f"[{i}/{len(names)}] {name}")
    try:
        print("  ok:", model(name))
    except Exception as exc:          # keep going; report at the end
        print("  FAILED:", exc)
        failed.append(name)
print("\nAll models are ready." if not failed else f"\nFailed: {', '.join(failed)} - run again to retry.")
