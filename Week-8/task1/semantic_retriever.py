"""Semantic Retriever: store documents, then find them by meaning, not by exact words
(EmbeddingGemma 2 + an on-device vector database)."""
import mediapipe as mp

from common import model

R = mp.tasks.retrieval
documents = {
    "eiffel": "The Eiffel Tower is a wrought-iron tower in Paris, completed in 1889.",
    "python": "Python is a programming language that is popular for data science.",
    "coffee": "Espresso is made by forcing hot water through finely ground coffee beans.",
    "iyte": "Izmir Institute of Technology is a public research university in Urla, Izmir.",
    "docker": "Docker packages an application and its dependencies into a container.",
}
questions = ["Which landmark is in France?", "How do I ship my app with everything it needs?",
             "Where can I study engineering near the Aegean Sea?"]

embedder_options = R.UniversalEmbedderOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("embedding_gemma")), l2_normalize=True)
with R.UniversalEmbedder.create_from_options(embedder_options) as embedder:
    retriever_options = R.SemanticRetrieverOptions(embedder=embedder, embedding_dimension=768,
                                                   chunking_mode=R.ChunkingMode.CHARACTER)
    with R.SemanticRetriever.create_from_options(retriever_options) as retriever:
        for doc_id, text in documents.items():
            retriever.insert_document(doc_id=doc_id, text=text)
        print(f"Stored {len(documents)} documents.")
        for q in questions:
            results = retriever.retrieve(query=q, limit=2, min_similarity=0.0)
            print(f"\nQ: {q}")
            for r in results:
                print(f"  {r.score:.2f}  [{r.id}] {r.content}")
