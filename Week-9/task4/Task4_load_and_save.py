"""Task 4.1 - Load a model and save it to a folder, then load it again from that folder."""
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer

CHECKPOINT = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
folder = Path(__file__).parent / "saved_model"

model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT)   # from the Hugging Face cache
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
model.save_pretrained(folder)                                            # config.json + model.safetensors
tokenizer.save_pretrained(folder)                                        # tokenizer files
print("Saved files:", ", ".join(sorted(p.name for p in folder.iterdir())))

reloaded = AutoModelForSequenceClassification.from_pretrained(folder)    # load from our own folder
print(f"Reloaded {type(reloaded).__name__} with {reloaded.num_parameters():,} parameters")
print("Labels:", reloaded.config.id2label)
