from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from typing import Mapping
from typing import Protocol
from typing import cast


class GraphStoreLike(Protocol):
    def incremental_update(
        self,
        entities: list[dict[str, object]],
        relations: list[dict[str, object]],
        source_doc: str,
        timestamp: datetime | None = None,
    ) -> dict[str, int]: ...

    def add_meta_relation(self, source: str, target: str, relation: str) -> None: ...


class VectorStoreLike(Protocol):
    async def upsert(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, str | int | float | bool] | None = None,
    ) -> None: ...


class EntityExtractorLike(Protocol):
    async def extract_with_insight_filter(
        self,
        text: str,
        prompt_modifier: str = "",
    ) -> dict[str, list[dict[str, object]]]: ...


class OutputIndexer:
    graph_store: GraphStoreLike
    vector_store: VectorStoreLike
    temporal_store: object
    entity_extractor: EntityExtractorLike

    def __init__(
        self,
        graph_store: GraphStoreLike,
        vector_store: VectorStoreLike,
        temporal_store: object,
        entity_extractor: EntityExtractorLike,
    ):
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.temporal_store = temporal_store
        self.entity_extractor = entity_extractor

    async def index_output(
        self, output_text: str, metadata: dict[str, object] | None
    ) -> dict[str, int | bool]:
        metadata_payload: dict[str, object] = dict(metadata or {})
        timestamp = self._resolve_timestamp(metadata_payload.get("timestamp"))
        output_id = f"agent_output_{timestamp}"

        extraction = await self.entity_extractor.extract_with_insight_filter(
            output_text
        )
        entities = extraction.get("entities", [])
        relations = extraction.get("relations", [])

        graph_stats = self.graph_store.incremental_update(
            entities=entities,
            relations=relations,
            source_doc=output_id,
            timestamp=datetime.fromisoformat(timestamp),
        )

        referenced_docs = self._normalize_referenced_docs(
            metadata_payload.get("referenced_docs")
        )

        vector_metadata = self._build_vector_metadata(metadata_payload, output_id)
        await self.vector_store.upsert(output_id, output_text, vector_metadata)

        await self._add_derivation_links(
            output_id=output_id, referenced_docs=referenced_docs
        )

        return {
            "entities_added": int(graph_stats.get("nodes_added", 0)),
            "relations_added": int(graph_stats.get("edges_added", 0)),
            "vector_updated": True,
        }

    async def _add_derivation_links(
        self, output_id: str, referenced_docs: list[str]
    ) -> None:
        seen: set[str] = set()
        for doc_id in referenced_docs:
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
    def _resolve_timestamp(timestamp_value: object) -> str:
        if isinstance(timestamp_value, str):
            normalized = timestamp_value.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized).isoformat()
            except ValueError:
                pass

        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _build_vector_metadata(
        metadata: Mapping[str, object], output_id: str
    ) -> dict[str, str | int | float | bool]:
        merged = {
            **metadata,
            "source_doc": output_id,
            "source_type": "agent_analysis",
        }

        cleaned: dict[str, str | int | float | bool] = {}
        for key, value in merged.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                cleaned[str(key)] = value
                continue
            cleaned[str(key)] = json.dumps(value, ensure_ascii=False)

        return cleaned

    @staticmethod
    def _normalize_referenced_docs(referenced_docs: object) -> list[str]:
        if not isinstance(referenced_docs, list):
            return []

        items = cast(list[object], referenced_docs)
        normalized: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            clean_item = item.strip()
            if clean_item:
                normalized.append(clean_item)
        return normalized
