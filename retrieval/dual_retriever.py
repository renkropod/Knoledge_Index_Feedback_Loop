from __future__ import annotations

# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnannotatedClassAttribute=false, reportMissingTypeArgument=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportAny=false, reportExplicitAny=false

import math
import re
from datetime import datetime, timezone
from typing import Any

from .ppr_ranker import PPRRanker


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


class DualLevelRetriever:
    def __init__(self, graph_store, vector_store, temporal_store):
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.temporal_store = temporal_store
        self.ppr_ranker = PPRRanker(graph_store=graph_store)

    async def retrieve(
        self, query: str, top_k: int = 10, mode: str = "hybrid"
    ) -> list[dict]:
        normalized_mode = mode.lower().strip()
        if normalized_mode not in {"low", "high", "hybrid"}:
            normalized_mode = "hybrid"

        query_entities = self._extract_query_entities(query)
        candidates: list[dict] = []

        if normalized_mode in {"low", "hybrid"} and query_entities:
            candidates.extend(self._graph_search(query_entities))

        if normalized_mode in {"high", "hybrid"}:
            vector_results = await self.vector_store.search(query=query, top_k=top_k)
            candidates.extend(self._normalize_vector_results(vector_results))

        merged_candidates = self._merge_candidates(candidates)
        ranked = self.ppr_ranker.rank(merged_candidates, query_entities)
        boosted = self._apply_temporal_boost(ranked)

        boosted.sort(key=lambda item: item.get("final_score", 0.0), reverse=True)
        return boosted[:top_k]

    def _extract_query_entities(self, query: str) -> list[str]:
        tokens = [token.strip() for token in re.split(r"\s+", query) if token.strip()]
        tokens = [
            token
            for token in tokens
            if token.lower() not in STOPWORDS and re.search(r"\w", token)
        ]

        entities: list[str] = []
        seen: set[str] = set()

        full_query_matches = self.graph_store.search_entities(query)
        for match in full_query_matches:
            entity = str(match.get("entity", "")).strip()
            if entity and entity not in seen and match.get("score", 0) >= 2:
                seen.add(entity)
                entities.append(entity)

        for token in tokens:
            if len(token) < 3:
                continue
            matches = self.graph_store.search_entities(token)
            for match in matches:
                entity = str(match.get("entity", "")).strip()
                if not entity or entity in seen:
                    continue
                if match.get("score", 0) < 2:
                    continue
                seen.add(entity)
                entities.append(entity)

        return entities

    def _graph_search(self, entities: list[str]) -> list[dict]:
        results: list[dict] = []

        for entity in entities:
            direct_matches = self.graph_store.search_entities(entity)
            for match in direct_matches:
                matched_entity = str(match.get("entity", "")).strip()
                if not matched_entity:
                    continue
                results.append(self._build_node_candidate(matched_entity, match))

            neighbors = self.graph_store.get_neighbors(entity, hops=1)
            for edge in neighbors:
                edge_source = str(edge.get("source", "")).strip()
                edge_target = str(edge.get("target", "")).strip()
                neighbor_entity = edge_target if edge_source == entity else edge_source
                if not neighbor_entity:
                    continue

                sources = edge.get("sources") or []
                source_doc = sources[0] if sources else "graph"
                edge_description = str(edge.get("description", "")).strip()
                relation = (
                    str(edge.get("relation", "related_to")).strip() or "related_to"
                )
                if not edge_description:
                    edge_description = f"{edge_source} {relation} {edge_target}"

                weight = self._safe_float(edge.get("weight"), default=1.0)
                hops = int(edge.get("hops", 1) or 1)
                graph_score = min(1.0, weight / max(hops, 1))
                node_ts = self._get_node_timestamp(neighbor_entity)

                results.append(
                    {
                        "entity": neighbor_entity,
                        "text": edge_description,
                        "source_doc": source_doc,
                        "score": graph_score,
                        "timestamp": node_ts,
                    }
                )

        return results

    def _apply_temporal_boost(self, results: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc)
        boosted = []

        for result in results:
            item = dict(result)
            base_score = self._safe_float(item.get("final_score"), default=0.0)
            timestamp = item.get("timestamp")

            if not timestamp:
                boost_weight = 1.0
            else:
                age_days = self._age_in_days(timestamp, now)
                boost_weight = 0.7 + 0.3 * math.exp(-0.693 * age_days / 30.0)

            item["final_score"] = base_score * boost_weight
            boosted.append(item)

        return boosted

    def _normalize_vector_results(self, vector_results: list[dict]) -> list[dict]:
        normalized = []

        for item in vector_results:
            metadata = item.get("metadata") or {}
            entity = str(
                metadata.get("entity")
                or metadata.get("title")
                or metadata.get("topic")
                or item.get("id")
                or ""
            ).strip()
            source_doc = str(metadata.get("source_doc") or item.get("id") or "unknown")
            timestamp = metadata.get("timestamp")

            normalized.append(
                {
                    "entity": entity,
                    "text": str(item.get("text") or ""),
                    "source_doc": source_doc,
                    "score": self._safe_float(item.get("score"), default=0.0),
                    "timestamp": timestamp,
                }
            )

        return normalized

    def _merge_candidates(self, candidates: list[dict]) -> list[dict]:
        merged: dict[tuple[str, str], dict] = {}

        for item in candidates:
            entity = str(item.get("entity") or "").strip()
            source_doc = str(item.get("source_doc") or "").strip()
            key = (entity, source_doc)

            if key not in merged:
                merged[key] = dict(item)
                continue

            existing = merged[key]
            existing_score = self._safe_float(existing.get("score"), default=0.0)
            incoming_score = self._safe_float(item.get("score"), default=0.0)
            if incoming_score > existing_score:
                existing["score"] = incoming_score

            if len(str(item.get("text") or "")) > len(str(existing.get("text") or "")):
                existing["text"] = item.get("text")

            if not existing.get("timestamp") and item.get("timestamp"):
                existing["timestamp"] = item.get("timestamp")

        return list(merged.values())

    def _build_node_candidate(self, entity: str, match: dict) -> dict:
        node = self.graph_store.graph.nodes.get(entity, {})
        descriptions = node.get("descriptions") or []

        if descriptions:
            latest_desc = descriptions[-1]
            text = str(latest_desc.get("text") or entity)
            source_doc = str(latest_desc.get("source") or entity)
            timestamp = latest_desc.get("timestamp") or node.get("last_updated")
        else:
            text = entity
            source_doc = entity
            timestamp = node.get("last_updated")

        base_score = self._safe_float(match.get("score"), default=0.0)
        normalized_score = min(1.0, base_score / 3.0)

        return {
            "entity": entity,
            "text": text,
            "source_doc": source_doc,
            "score": normalized_score,
            "timestamp": timestamp,
        }

    def _get_node_timestamp(self, entity: str) -> str | None:
        node = self.graph_store.graph.nodes.get(entity, {})
        descriptions = node.get("descriptions") or []
        if descriptions:
            return descriptions[-1].get("timestamp") or node.get("last_updated")
        return node.get("last_updated")

    @staticmethod
    def _age_in_days(timestamp_value: Any, now: datetime) -> float:
        parsed_ts = None
        if isinstance(timestamp_value, datetime):
            parsed_ts = timestamp_value
        elif isinstance(timestamp_value, str):
            raw = timestamp_value.strip()
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            try:
                parsed_ts = datetime.fromisoformat(raw)
            except ValueError:
                return 365.0

        if parsed_ts is None:
            return 365.0

        if parsed_ts.tzinfo is None:
            parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)

        delta = now - parsed_ts.astimezone(timezone.utc)
        return max(0.0, delta.total_seconds() / 86400.0)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
