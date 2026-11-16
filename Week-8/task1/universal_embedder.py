"""Universal Embedder: text AND images become vectors in the same space,
so a sentence can be compared with a picture (EmbeddingGemma 2 text-vision)."""
import mediapipe as mp

from common import image, model

R = mp.tasks.retrieval
options = R.UniversalEmbedderOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("embedding_gemma")), l2_normalize=True)
pictures = ["pose-3.jpg", "face-3.png"]
sentences = ["a man cheering with both arms raised", "a close-up portrait of a woman's face"]

with R.UniversalEmbedder.create_from_options(options) as embedder:
    img_vecs = {p: embedder.embed_image(open(image(p), "rb").read()).embeddings[0] for p in pictures}
    txt_vecs = {s: embedder.embed_text(s).embeddings[0] for s in sentences}

print(f"Vector length: {len(next(iter(txt_vecs.values())).embedding)}")
print("Cosine similarity (text vs. picture):")
for s, tv in txt_vecs.items():
    scores = "  ".join(f"{p}: {R.UniversalEmbedder.cosine_similarity(tv, iv):.3f}" for p, iv in img_vecs.items())
    print(f"  '{s}'\n      {scores}")
