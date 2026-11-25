"""Task 1 - Named entity recognition: find the person, the organization and the location."""
from transformers import pipeline

ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english",
               aggregation_strategy="simple")          # join word pieces into whole names
text = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
        "and working in the beautiful city İzmir in Türkiye.")
entities = ner(text)

for e in entities:
    print(f"{e['entity_group']:4s} {e['score']:.4f}  {e['word']}")
first = {g: next((e["word"] for e in entities if e["entity_group"] == g), None) for g in ("PER", "ORG", "LOC")}
print(f"\nName: {first['PER']} | Works for: {first['ORG']} | Lives in: {first['LOC']}")
