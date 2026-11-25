"""Task 1 - Text generation: complete a sentence, two alternatives, at most 35 words each."""
from transformers import pipeline, set_seed

MAX_WORDS = 35
set_seed(42)                                   # same alternatives every run
generator = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M")
prompt = "If I continue to complete all in-class exercises in this modern software practices course,"
outputs = generator(prompt, max_new_tokens=60, num_return_sequences=2, do_sample=True,
                    temperature=0.8, pad_token_id=generator.tokenizer.eos_token_id)

for i, out in enumerate(outputs, 1):
    words = out["generated_text"].split()[:MAX_WORDS]          # keep at most 35 words
    print(f"Alternative {i} ({len(words)} words):\n  {' '.join(words)}\n")
