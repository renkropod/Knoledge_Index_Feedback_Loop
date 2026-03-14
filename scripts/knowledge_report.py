#!/usr/bin/env python3
"""Generate a knowledge base status report."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from config import Settings
from storage import KnowledgeGraph, TemporalFactStore, VectorStore


def generate_report(graph_store, vector_store, temporal_store) -> dict:
    graph_stats = graph_store.get_stats()
    vector_stats = vector_store.get_stats()
    temporal_stats = temporal_store.get_stats()

    today = date.today()
    new_entities = _count_nodes_by_date(graph_store.graph.nodes(data=True), today)
    new_relations = _count_edges_by_date(graph_store.graph.edges(data=True), today)
    invalidated_facts = sum(
        1
        for fact in temporal_store.facts
        if getattr(fact, "valid_until", None) is not None
    )

    return {
        "total_entities": int(graph_stats.get("total_nodes", 0)),
        "total_relations": int(graph_stats.get("total_edges", 0)),
        "total_documents": int(vector_stats.get("total_documents", 0)),
        "total_facts": int(temporal_stats.get("total_facts", 0)),
        "new_entities": new_entities,
        "new_relations": new_relations,
        "invalidated_facts": invalidated_facts,
    }


def print_report(report: dict):
    print("Knowledge Base Status Report")
    print("-" * 36)
    print(f"total_entities    : {report.get('total_entities', 0)}")
    print(f"total_relations   : {report.get('total_relations', 0)}")
    print(f"total_documents   : {report.get('total_documents', 0)}")
    print(f"total_facts       : {report.get('total_facts', 0)}")
    print(f"new_entities      : {report.get('new_entities', 0)}")
    print(f"new_relations     : {report.get('new_relations', 0)}")
    print(f"invalidated_facts : {report.get('invalidated_facts', 0)}")


def _count_nodes_by_date(nodes: Any, target_date: date) -> int:
    count = 0
    for _, data in nodes:
        created_at = _parse_date(data.get("created_at"))
        if created_at == target_date:
            count += 1
    return count


def _count_edges_by_date(edges: Any, target_date: date) -> int:
    count = 0
    for _, _, data in edges:
        created_at = _parse_date(data.get("created_at"))
        if created_at == target_date:
            count += 1
    return count


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


if __name__ == "__main__":
    settings = Settings.load()
    graph_store = KnowledgeGraph(settings.storage.graph_path)
    vector_store = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    temporal_store = TemporalFactStore(settings.storage.temporal_path)

    report = generate_report(graph_store, vector_store, temporal_store)
    print_report(report)
