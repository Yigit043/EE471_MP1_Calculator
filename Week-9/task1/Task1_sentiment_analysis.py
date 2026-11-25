"""Task 1 - Sentiment analysis: is a sentence positive or negative?"""
from transformers import pipeline

classifier = pipeline("sentiment-analysis",
                      model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
sentences = ["I've been waiting for a modern software practices course my whole life.",
             "I hate software courses"]
for sentence, result in zip(sentences, classifier(sentences)):
    print(f"{result['label']:8s} {result['score']:.4f}  {sentence}")
