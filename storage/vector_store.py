from __future__ import annotations

import os
from importlib import import_module
from datetime import datetime, timezone
from typing import Callable, Protocol, cast


class CollectionLike(Protocol):
    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, object]],
    ) -> None: ...

    def query(
        self,
        *,
        query_texts: list[str],
        n_results: int,
        where: dict[str, object] | None,
        include: list[str],
    ) -> dict[str, list[list[object]]]: ...

    def delete(self, *, ids: list[str]) -> None: ...

    def count(self) -> int: ...


class ClientLike(Protocol):
    def get_or_create_collection(
        self,
        *,
        name: str,
        embedding_function: object,
        metadata: dict[str, str],
    ) -> CollectionLike: ...

    def get_collection(self, *, name: str) -> CollectionLike: ...


class VectorStore:
    def __init__(
        self,
        persist_dir: str = "knowledge_base/vectors",
        collection_name: str = "knowledge_docs",
        embedding_model: str = "BAAI/bge-m3",
    ):
        self.persist_dir: str = persist_dir
        self.collection_name: str = collection_name
        self.embedding_model: str = embedding_model
        self._collection: CollectionLike | None = None

        os.makedirs(self.persist_dir, exist_ok=True)

        chromadb_module = import_module("chromadb")
        persistent_client = cast(
            Callable[..., ClientLike],
            getattr(chromadb_module, "PersistentClient"),
        )
        self.client: ClientLike = persistent_client(path=self.persist_dir)

    def _ensure_collection(self) -> CollectionLike:
        if self._collection is None:
            embedding_functions = import_module("chromadb.utils.embedding_functions")
            embedding_fn_factory = cast(
                Callable[..., object],
                getattr(embedding_functions, "SentenceTransformerEmbeddingFunction"),
            )
            embedding_fn = embedding_fn_factory(
                model_name=self.embedding_model,
                normalize_embeddings=True,
            )
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        assert self._collection is not None
        return self._collection

    @property
    def collection(self) -> CollectionLike:
        return self._ensure_collection()

    async def upsert(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, object] | None = None,
    ):
        base_metadata = dict(metadata or {})
        if "source_doc" not in base_metadata:
            base_metadata["source_doc"] = doc_id
        if "timestamp" not in base_metadata:
            base_metadata["timestamp"] = datetime.now(tz=timezone.utc).isoformat()
        if "chunk_index" not in base_metadata:
            base_metadata["chunk_index"] = 0
        cleaned_metadata = {
            key: value for key, value in base_metadata.items() if value is not None
        }

        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[cleaned_metadata],
        )

    async def upsert_batch(
        self,
        items: list[tuple[str, str, dict[str, object] | None]],
    ):
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, object]] = []

        for doc_id, text, metadata in items:
            base_metadata = dict(metadata or {})
            if "source_doc" not in base_metadata:
                base_metadata["source_doc"] = doc_id
            if "timestamp" not in base_metadata:
                base_metadata["timestamp"] = datetime.now(tz=timezone.utc).isoformat()
            if "chunk_index" not in base_metadata:
                base_metadata["chunk_index"] = 0
            cleaned_metadata = {
                key: value for key, value in base_metadata.items() if value is not None
            }

            ids.append(doc_id)
            documents.append(text)
            metadatas.append(cleaned_metadata)

        if not ids:
            return

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        where: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        query_result = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        ids = cast(list[str], query_result.get("ids", [[]])[0])
        documents = cast(list[str], query_result.get("documents", [[]])[0])
        metadatas = cast(
            list[dict[str, object]], query_result.get("metadatas", [[]])[0]
        )
        distances = cast(list[float], query_result.get("distances", [[]])[0])

        results: list[dict[str, object]] = []
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

    def get_stats(self) -> dict[str, object]:
        try:
            total_documents = self.client.get_collection(
                name=self.collection_name
            ).count()
        except Exception:
            total_documents = 0
        return {
            "collection_name": self.collection_name,
            "persist_dir": self.persist_dir,
            "embedding_model": self.embedding_model,
            "total_documents": total_documents,
        }
