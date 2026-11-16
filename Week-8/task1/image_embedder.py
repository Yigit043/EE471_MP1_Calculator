"""Image Embedder: pictures -> vectors; similar pictures give a high cosine similarity."""
import itertools

import mediapipe as mp

from common import image, model

V = mp.tasks.vision
options = V.ImageEmbedderOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("image_embedder")), l2_normalize=True)
names = ["pose-2.jpg", "pose-3.jpg", "face-1.png", "face-2.png"]
with V.ImageEmbedder.create_from_options(options) as embedder:
    vecs = {n: embedder.embed(mp.Image.create_from_file(image(n))).embeddings[0] for n in names}

print(f"Vector length: {len(vecs[names[0]].embedding)}")
for a, b in itertools.combinations(names, 2):
    print(f"{V.ImageEmbedder.cosine_similarity(vecs[a], vecs[b]):.3f}  {a} vs {b}")
