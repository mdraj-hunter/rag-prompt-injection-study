"""
Local retrieval: loads documents, chunks them, embeds with a CPU-friendly
sentence-transformers model, and indexes with FAISS for similarity search.
"""
import os
import glob
from dataclasses import dataclass

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings


@dataclass
class Chunk:
    id: str
    source_file: str
    text: str


def load_documents(documents_dir: str = "data/documents") -> list[Chunk]:
    """Load all .txt files and split each into paragraph-level chunks."""
    chunks: list[Chunk] = []
    filepaths = sorted(glob.glob(os.path.join(documents_dir, "*.txt")))

    if not filepaths:
        raise FileNotFoundError(
            f"No .txt files found in {documents_dir}. Add the sample documents first."
        )

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # simple paragraph-based chunking — good enough for a small toy corpus
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for i, para in enumerate(paragraphs):
            chunk_id = f"{filename}::chunk{i}"
            chunks.append(Chunk(id=chunk_id, source_file=filename, text=para))

    return chunks


class Retriever:
    def __init__(self, documents_dir: str = "data/documents"):
        self.model = SentenceTransformer(settings.embedding_model)
        self.chunks = load_documents(documents_dir)
        self.index = self._build_index()

    def _build_index(self) -> faiss.IndexFlatL2:
        texts = [c.text for c in self.chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings = embeddings.astype("float32")

        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        return index

    def retrieve(self, query: str, top_k: int = 3) -> list[Chunk]:
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = self.index.search(query_embedding, top_k)
        return [self.chunks[i] for i in indices[0] if i < len(self.chunks)]


if __name__ == "__main__":
    # quick manual smoke test
    retriever = Retriever()
    results = retriever.retrieve("What is the return policy?", top_k=2)
    for r in results:
        print(f"[{r.source_file}] {r.text[:100]}...")