from __future__ import annotations

import json
from datetime import datetime
from typing import Any


class OutputIndexer:
    def __init__(self, graph_store, vector_store, temporal_store, entity_extractor):
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.temporal_store = temporal_store
        self.entity_extractor = entity_extractor

    async def index_output(self, output_text: str, metadata: dict) -> dict:
        metadata = dict(metadata or {})
        timestamp = self._resolve_timestamp(metadata.get("timestamp"))
        output_id = f"agent_output_{timestamp}"

        extraction = await self.entity_extractor.extract_with_insight_filter(
            output_text
        )
        entities = (
            extraction.get("entities", []) if isinstance(extraction, dict) else []
        )
        relations = (
            extraction.get("relations", []) if isinstance(extraction, dict) else []
        )

        graph_stats = self.graph_store.incremental_update(
            entities=entities,
            relations=relations,
            source_doc=output_id,
            timestamp=datetime.fromisoformat(timestamp),
        )

        referenced_docs = metadata.get("referenced_docs", [])
        if not isinstance(referenced_docs, list):
            referenced_docs = []

        vector_metadata = self._build_vector_metadata(metadata, output_id)
        await self.vector_store.upsert(output_id, output_text, vector_metadata)

        await self._add_derivation_links(
            output_id=output_id, referenced_docs=referenced_docs
        )

        return {
            "entities_added": int(graph_stats.get("nodes_added", 0)),
            "relations_added": int(graph_stats.get("edges_added", 0)),
            "vector_updated": True,
        }

    async def _add_derivation_links(self, output_id: str, referenced_docs: list[str]):
        seen: set[str] = set()
        for doc_id in referenced_docs:
            if not isinstance(doc_id, str):
                continue

            clean_doc_id = doc_id.strip()
            if not clean_doc_id or clean_doc_id == output_id or clean_doc_id in seen:
                continue

            seen.add(clean_doc_id)
            self.graph_store.add_meta_relation(
                source=output_id,
                target=clean_doc_id,
                relation="DERIVED_FROM",
            )

    @staticmethod
    def _resolve_timestamp(timestamp_value: Any) -> str:
        if isinstance(timestamp_value, str):
            normalized = timestamp_value.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized).isoformat()
            except ValueError:
                pass

        return datetime.utcnow().isoformat()

    @staticmethod
    def _build_vector_metadata(metadata: dict, output_id: str) -> dict:
        merged = {
            **metadata,
            "source_doc": output_id,
            "source_type": "agent_analysis",
        }

        cleaned: dict[str, Any] = {}
        for key, value in merged.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
                continue
            cleaned[key] = json.dumps(value, ensure_ascii=False)

        return cleaned
