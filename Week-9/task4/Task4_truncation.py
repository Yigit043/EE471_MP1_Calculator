"""Task 4.4 - Truncation: cut sequences that are longer than a maximum length."""
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")
text = "This sentence is much too long for our tiny limit, so the tokenizer has to cut it off."

full = tokenizer(text)["input_ids"]
short = tokenizer(text, max_length=8, truncation=True)["input_ids"]
print(f"Model maximum length: {tokenizer.model_max_length} tokens")
print(f"Full     ({len(full)} tokens):", tokenizer.decode(full))
print(f"Truncated ({len(short)} tokens):", tokenizer.decode(short))
