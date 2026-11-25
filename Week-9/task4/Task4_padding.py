"""Task 4.3 - Padding: make sentences of different lengths the same length for one batch."""
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")
sentences = ["I love this course.", "Padding makes every sentence in a batch the same length."]

batch = tokenizer(sentences, padding=True)        # pad to the longest sentence
print(f"Pad token: {tokenizer.pad_token!r} (id {tokenizer.pad_token_id})")
for ids, mask in zip(batch["input_ids"], batch["attention_mask"]):
    print("input_ids     :", ids)
    print("attention_mask:", mask, "<- 0 = padding, ignored by the model\n")
