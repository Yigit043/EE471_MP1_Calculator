"""Task 1 - Mask filling: guess the missing word."""
from transformers import pipeline

unmasker = pipeline("fill-mask", model="distilbert/distilroberta-base")
sentence = f"To understand generative AI, one must study {unmasker.tokenizer.mask_token} well."
print(sentence)
for r in unmasker(sentence, top_k=3):
    print(f"  {r['score']:.4f}  {r['sequence']}")
