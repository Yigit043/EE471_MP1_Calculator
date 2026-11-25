"""Task 1 - Zero-shot classification: choose labels the model was never trained on."""
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
text = "Berkshire keeps their cash reserves at an extremely high level."
labels = ["finance", "politics", "sports", "technology", "education"]
result = classifier(text, candidate_labels=labels)

print(text)
for label, score in zip(result["labels"], result["scores"]):
    print(f"  {label:11s} {score:.4f}")
