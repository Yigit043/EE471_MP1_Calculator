"""Task 4.5 - Special tokens: [CLS] at the start and [SEP] at the end, plus adding a new token."""
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")
text = "I love EE471."

plain = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(text))
with_special = tokenizer(text)["input_ids"]                   # the tokenizer adds them automatically
print("Without special tokens:", tokenizer.decode(plain))
print("With special tokens   :", tokenizer.decode(with_special))
print("Special tokens:", tokenizer.all_special_tokens)

tokenizer.add_special_tokens({"additional_special_tokens": ["[COURSE]"]})   # our own special token
ids = tokenizer("[COURSE] is fun")["input_ids"]
print("\nAfter adding [COURSE]:", tokenizer.convert_ids_to_tokens(ids))
