"""Text Embedder: sentences -> vectors; similar meaning gives a high cosine similarity
(Universal Sentence Encoder)."""
import itertools

import mediapipe as mp

from common import model

options = mp.tasks.text.TextEmbedderOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("text_embedder")))
sentences = ["The cat is sleeping on the sofa.", "A kitten naps on the couch.",
             "The stock market fell sharply today."]
with mp.tasks.text.TextEmbedder.create_from_options(options) as embedder:
    vecs = [embedder.embed(s).embeddings[0] for s in sentences]
    print(f"Vector length: {len(vecs[0].embedding)}")
    for (i, a), (j, b) in itertools.combinations(enumerate(vecs), 2):
        sim = mp.tasks.text.TextEmbedder.cosine_similarity(a, b)
        print(f"{sim:.3f}  '{sentences[i]}'  vs  '{sentences[j]}'")
