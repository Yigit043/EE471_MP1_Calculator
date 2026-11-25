"""Task 4.2 - Text encoding and decoding: text -> tokens -> IDs -> text."""
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("distilbert/distilbert-base-uncased-finetuned-sst-2-english")
text = "Using a Transformer network is simple"

tokens = tokenizer.tokenize(text)                 # split into word pieces
ids = tokenizer.convert_tokens_to_ids(tokens)     # each piece -> its number in the vocabulary
decoded = tokenizer.decode(ids)                   # numbers -> text again

print("Text   :", text)
print("Tokens :", tokens)
print("IDs    :", ids)
print("Decoded:", decoded)
