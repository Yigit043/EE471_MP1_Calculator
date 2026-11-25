"""Task 1 - Translation: French -> English with Helsinki-NLP's opus-mt-fr-en."""
from transformers import pipeline

french = "Ce cours est produit par Hugging Face."

translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")
english = translator(french)[0]["translation_text"]
print(f"French  : {french}\nEnglish : {english}")
