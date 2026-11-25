# Week 9 – Hugging Face Transformers

## Setup
```
pip install --only-binary=:all: "transformers==4.57.6" sentencepiece gradio
python download_hf_models.py        # all models into the Hugging Face cache (once)
```
transformers 4.57 is used because the course's `pipeline("translation")` was removed in 5.x.

## Task 1 – ten pipelines (`task1/`)
One script per task, named like its video (`python Task1_sentiment_analysis.py` ...).

| Script | Model |
|---|---|
| Task1_sentiment_analysis | distilbert-base-uncased-finetuned-sst-2-english |
| Task1_zero_shot_classification | facebook/bart-large-mnli |
| Task1_text_generation | HuggingFaceTB/SmolLM2-360M (2 alternatives, at most 35 words) |
| Task1_mask_filling | distilroberta-base |
| Task1_named_entity_recognition | dbmdz/bert-large-cased-finetuned-conll03-english |
| Task1_question_answering | distilbert-base-cased-distilled-squad (validates the NER results) |
| Task1_summarization | sshleifer/distilbart-cnn-12-6  |
| Task1_translation | Helsinki-NLP/opus-mt-fr-en ("Ce cours est produit par Hugging Face." -> English) |
| Task1_image_classification | google/vit-base-patch16-224 (Week-8 test images or any picture) |
| Task1_automatic_speech_recognition | openai/whisper-large-v3 (`samples/speech.wav` or any 16-bit WAV) |

## Task 3 – OOP module + Gradio (`task3/`)
- `hf_tasks.py`: class `HuggingFaceTasks` with one method per task; pipelines are created on first use.
- `app.py`: Gradio interface with one tab per task → `python app.py`, open http://127.0.0.1:7860

## Task 4 – tokenizers and models (`task4/`)
`Task4_load_and_save.py`, `Task4_encode_decode.py`, `Task4_padding.py`, `Task4_truncation.py`,
`Task4_special_tokens.py` (checkpoint: distilbert-base-uncased-finetuned-sst-2-english).
