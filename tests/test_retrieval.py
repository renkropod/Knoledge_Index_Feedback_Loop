from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from types import SimpleNamespace

from retrieval.context_assembler import ContextAssembler
from retrieval import ppr_ranker as ppr_module
from retrieval.ppr_ranker import PPRRanker


def test_ppr_rank_empty_candidates():
    ranker = PPRRanker(graph_store=SimpleNamespace(graph=ppr_module.nx.DiGraph()))
    assert ranker.rank([], ["Ethereum"]) == []


def test_ppr_rank_no_graph():
    ranker = PPRRanker(graph_store=SimpleNamespace(graph=None))
    candidates = [
        {"entity": "Ethereum", "score": 1.0},
        {"entity": "Bitcoin", "score": 0.5},
    ]
    ranked = ranker.rank(candidates, ["Ethereum"])
    assert ranked[0]["entity"] == "Ethereum"
    assert ranked[0]["ppr_score"] == 0.0
    assert ranked[0]["final_score"] == 0.6


def test_ppr_rank_with_graph_and_personalization(sample_entities):
    graph = ppr_module.nx.DiGraph()
    graph.add_edge("Ethereum", "Optimism", weight=1.0)
    graph.add_edge("Optimism", "DeFi", weight=0.8)
    graph.add_node("Bitcoin")
    ranker = PPRRanker(graph_store=SimpleNamespace(graph=graph))

    candidates = [
        {"entity": sample_entities[1]["name"], "score": 0.7},
        {"entity": sample_entities[4]["name"], "score": 0.65},
        {"entity": sample_entities[2]["name"], "score": 0.9},
    ]
    ranked = ranker.rank(candidates, ["Ethereum"])
    assert all("ppr_score" in item and "final_score" in item for item in ranked)
    optimism = next(item for item in ranked if item["entity"] == "Optimism")
    bitcoin = next(item for item in ranked if item["entity"] == "Bitcoin")
    assert optimism["ppr_score"] > bitcoin["ppr_score"]
    assert ranked == sorted(ranked, key=lambda item: item["final_score"], reverse=True)


def test_context_assemble_empty_results():
    assembler = ContextAssembler(max_context_tokens=4000)
    context = assembler.assemble(results=[], query="eth updates")
    assert context == "Query: eth updates\n\nRetrieved Context:"


def test_context_assemble_normal_results(sample_text):
    assembler = ContextAssembler(max_context_tokens=4000)
    results = [
        {
            "text": sample_text[:40],
            "source_doc": "doc_a",
            "final_score": 0.923,
            "timestamp": "2024-01-01T00:00:00+00:00",
        },
        {
            "entity": "Optimism",
            "source_doc": "doc_b",
            "final_score": 0.7,
        },
    ]
    context = assembler.assemble(results=results, query="layer2")
    assert "Query: layer2" in context
    assert "1." in context and "2." in context
    assert "Source: doc_a, Score: 0.92, Time: 2024-01-01T00:00:00+00:00" in context
    assert "Optimism" in context


def test_context_assemble_max_token_truncation():
    assembler = ContextAssembler(max_context_tokens=5)
    long_text = "X" * 200
    results = [
        {"text": long_text, "source_doc": "doc_a", "final_score": 1.0},
        {"text": "B" * 60, "source_doc": "doc_b", "final_score": 0.9},
    ]
    context = assembler.assemble(results=results, query="q")
    assert long_text not in context
    assert "B" * 60 not in context
