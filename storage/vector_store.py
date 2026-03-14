from __future__ import annotations

import os
from datetime import datetime

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


class VectorStore:
    def __init__(
        self,
        persist_dir: str = "knowledge_base/vectors",
        collection_name: str = "knowledge_docs",
        embedding_model: str = "BAAI/bge-m3",
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model,
            normalize_embeddings=True,
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, doc_id: str, text: str, metadata: dict | None = None):
        base_metadata = dict(metadata or {})
        base_metadata.setdefault("source_doc", doc_id)
        base_metadata.setdefault("timestamp", datetime.utcnow().isoformat())
        base_metadata.setdefault("chunk_index", 0)
        cleaned_metadata = {
            key: value for key, value in base_metadata.items() if value is not None
        }

        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[cleaned_metadata],
        )

    async def search(
        self, query: str, top_k: int = 10, where: dict | None = None
    ) -> list[dict]:
        query_result = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        ids = query_result.get("ids", [[]])[0]
        documents = query_result.get("documents", [[]])[0]
        metadatas = query_result.get("metadatas", [[]])[0]
        distances = query_result.get("distances", [[]])[0]

        results = []
        for idx, item_id in enumerate(ids):
            distance = distances[idx] if idx < len(distances) else None
            score = None if distance is None else 1.0 - float(distance)
            results.append(
                {
                    "id": item_id,
                    "text": documents[idx] if idx < len(documents) else "",
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                    "score": score,
                }
            )

        return results

    async def delete(self, doc_id: str):
        self.collection.delete(ids=[doc_id])

    def get_stats(self) -> dict:
        return {
            "collection_name": self.collection_name,
            "persist_dir": self.persist_dir,
            "embedding_model": self.embedding_model,
            "total_documents": self.collection.count(),
        }
