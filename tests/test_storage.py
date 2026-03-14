from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from storage.graph_store import KnowledgeGraph
from storage.temporal_store import TemporalFact
from storage.temporal_store import TemporalFactStore


def test_knowledge_graph_create_new(graph_path, tmp_dir):
    assert Path(graph_path).parent == tmp_dir
    kg = KnowledgeGraph(graph_path=graph_path)
    stats = kg.get_stats()
    assert stats["total_nodes"] == 0
    assert stats["total_edges"] == 0
    assert stats["last_updated"] is None


def test_knowledge_graph_incremental_update_add_nodes_edges(
    sample_entities, sample_relations, graph_path
):
    kg = KnowledgeGraph(graph_path=graph_path)
    update_stats = kg.incremental_update(
        entities=sample_entities,
        relations=sample_relations,
        source_doc="doc_a",
    )
    assert update_stats["nodes_added"] == len(sample_entities)
    assert update_stats["edges_added"] == len(sample_relations)
    assert kg.graph.number_of_nodes() == len(sample_entities)
    assert kg.graph.number_of_edges() == len(sample_relations)


def test_knowledge_graph_incremental_update_existing_node_edge_updates(
    sample_entities, sample_relations, graph_path
):
    kg = KnowledgeGraph(graph_path=graph_path)
    kg.incremental_update(sample_entities, sample_relations, source_doc="doc_a")

    second_entities = [
        {"name": "Ethereum", "type": "PROTOCOL", "description": "Updated description"}
    ]
    second_relations = [
        {
            "source": "Optimism",
            "target": "Ethereum",
            "relation": "LAYER2_OF",
            "description": "Second relation detail",
            "weight": 0.95,
        }
    ]
    update_stats = kg.incremental_update(
        entities=second_entities,
        relations=second_relations,
        source_doc="doc_b",
    )

    assert update_stats["nodes_updated"] == 1
    assert update_stats["edges_updated"] == 1
    edge = kg.graph["Optimism"]["Ethereum"]
    assert edge["weight"] == 0.95
    assert "doc_a" in edge["sources"] and "doc_b" in edge["sources"]
    assert "Second relation detail" in edge["description"]


def test_knowledge_graph_neighbors_topic_search_stats_and_persistence(
    sample_entities, sample_relations, graph_path
):
    kg = KnowledgeGraph(graph_path=graph_path)
    kg.incremental_update(sample_entities, sample_relations, source_doc="doc_a")

    neighbors = kg.get_neighbors("Ethereum", hops=1)
    neighbor_pairs = {(item["source"], item["target"]) for item in neighbors}
    assert ("Optimism", "Ethereum") in neighbor_pairs
    assert ("DeFi", "Ethereum") in neighbor_pairs

    summary = kg.get_topic_summary("ethereum")
    assert "Ethereum" in summary
    assert "Optimism" in summary

    search_results = kg.search_entities("rollup")
    assert search_results
    assert search_results[0]["entity"] == "Optimism"

    stats = kg.get_stats()
    assert stats["total_nodes"] == len(sample_entities)
    assert stats["total_edges"] == len(sample_relations)
    assert stats["last_updated"] is not None

    reloaded = KnowledgeGraph(graph_path=graph_path)
    assert reloaded.graph.number_of_nodes() == len(sample_entities)
    assert reloaded.graph.number_of_edges() == len(sample_relations)
    assert reloaded.get_neighbors("Ethereum", hops=1)


def test_temporal_fact_store_add_query_history_and_persistence(temporal_path):
    store = TemporalFactStore(store_path=temporal_path)
    t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t2 = t1 + timedelta(days=10)

    fact1 = TemporalFact(
        entity="Ethereum",
        attribute="tvl",
        value="50B",
        source_doc="doc_a",
        valid_from=t1,
    )
    fact2 = TemporalFact(
        entity="Ethereum",
        attribute="tvl",
        value="60B",
        source_doc="doc_b",
        valid_from=t2,
    )

    store.add_fact(fact1)
    store.add_fact(fact2)

    assert fact1.valid_until == t2
    current = store.query_current("Ethereum", "tvl")
    assert len(current) == 1
    assert current[0].value == "60B"

    at_t1 = store.query_at_time("Ethereum", t1 + timedelta(days=1))
    at_t2 = store.query_at_time("Ethereum", t2 + timedelta(days=1))
    assert len(at_t1) == 1 and at_t1[0].value == "50B"
    assert len(at_t2) == 1 and at_t2[0].value == "60B"

    history = store.get_entity_history("Ethereum")
    assert len(history) == 2
    assert history[0].valid_from == t1
    assert history[1].valid_from == t2

    reloaded = TemporalFactStore(store_path=temporal_path)
    reloaded_current = reloaded.query_current("Ethereum", "tvl")
    assert len(reloaded_current) == 1
    assert reloaded_current[0].value == "60B"
