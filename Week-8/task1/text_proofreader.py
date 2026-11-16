"""Text Proofreader: fix spelling and grammar mistakes (Proofread 200M, on-device)"""
import sys

import mediapipe as mp

from common import model

text = " ".join(sys.argv[1:]) or "Their are severel typos in this sentance, and it dont sound rite."
options = mp.tasks.text.TextProofreaderOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("text_proofreader")), max_num_tokens=1024)
with mp.tasks.text.TextProofreader.create_from_options(options) as proofreader:
    result = proofreader.proofread(text)

print("Original :", text)
print("Corrected:", result.proofread_text)
changes = [c for c in result.corrections if c.type.name != "SAME"]
print(f"{len(changes)} character edits:")
for c in changes:
    print(f"  {c.type.name.lower():9s} '{c.text}'")
