"""Task 1 - Question answering: validate the NER results by asking questions about the text."""
from transformers import pipeline

text = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
        "and working in the beautiful city İzmir in Türkiye.")
ner_result = {"person": "Nate", "organization": "Izmir Institute of Technology", "city": "İzmir"}
questions = {"person": "What is my name?",
             "organization": "Where do I work?",
             "city": "In which city do I live?"}

qa = pipeline("question-answering", model="distilbert/distilbert-base-cased-distilled-squad")
for key, question in questions.items():
    answer = qa(question=question, context=text)
    ok = ner_result[key].lower() in answer["answer"].lower() or answer["answer"].lower() in ner_result[key].lower()
    print(f"{question:26s} -> {answer['answer']:32s} ({answer['score']:.2f})  NER: {ner_result[key]}  "
          f"{'VALID' if ok else 'DIFFERENT'}")
