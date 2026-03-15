from __future__ import annotations

# pyright: reportMissingModuleSource=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnannotatedClassAttribute=false, reportMissingTypeArgument=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportAny=false, reportExplicitAny=false

from typing import Any

import networkx as nx
from networkx.exception import PowerIterationFailedConvergence


class PPRRanker:
    def __init__(self, graph_store):
        self.graph_store = graph_store

    def rank(self, candidates: list[dict], query_entities: list[str]) -> list[dict]:
        if not candidates:
            return []

        graph = getattr(self.graph_store, "graph", None)
        if graph is None or graph.number_of_nodes() == 0:
            return self._assign_scores_without_ppr(candidates)

        personalization = self._build_personalization(graph, query_entities)
        if not personalization:
            return self._assign_scores_without_ppr(candidates)

        try:
            ppr_scores = nx.pagerank(
                graph,
                alpha=0.85,
                personalization=personalization,
                weight="weight",
            )
        except PowerIterationFailedConvergence:
            return self._assign_scores_without_ppr(candidates)

        raw_ppr = {}
        for candidate in candidates:
            entity = candidate.get("entity")
            raw_ppr[entity] = self._safe_float(ppr_scores.get(entity), default=0.0)
        max_ppr = max(raw_ppr.values()) if raw_ppr else 1.0
        if max_ppr <= 0:
            max_ppr = 1.0

        ranked = []
        for candidate in candidates:
            item = dict(candidate)
            entity = item.get("entity")
            vector_score = self._safe_float(item.get("score"), default=0.0)
            ppr_raw = raw_ppr.get(entity, 0.0)
            ppr_normalized = ppr_raw / max_ppr
            item["ppr_score"] = ppr_normalized
            item["final_score"] = 0.6 * vector_score + 0.4 * ppr_normalized
            ranked.append(item)

        ranked.sort(key=lambda value: value.get("final_score", 0.0), reverse=True)
        return ranked

    def _build_personalization(
        self, graph: nx.DiGraph | nx.Graph, query_entities: list[str]
    ) -> dict[str, float]:
        seed_nodes = [entity for entity in query_entities if graph.has_node(entity)]
        if not seed_nodes:
            return {}

        uniform_weight = 1.0 / len(seed_nodes)
        return {entity: uniform_weight for entity in seed_nodes}

    def _assign_scores_without_ppr(self, candidates: list[dict]) -> list[dict]:
        ranked = []
        for candidate in candidates:
            item = dict(candidate)
            vector_score = self._safe_float(item.get("score"), default=0.0)
            item["ppr_score"] = 0.0
            item["final_score"] = 0.6 * vector_score
            ranked.append(item)

        ranked.sort(key=lambda value: value.get("final_score", 0.0), reverse=True)
        return ranked

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
