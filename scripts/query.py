#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Settings
from retrieval import ContextAssembler, DualLevelRetriever
from storage import KnowledgeGraph, TemporalFactStore, VectorStore


async def query(
    query_text: str,
    top_k: int = 10,
    mode: str = "hybrid",
    verbose: bool = False,
    at_time: str = "",
    entity_history: str = "",
):
    settings = Settings.load()
    t0 = time.perf_counter()

    kg = KnowledgeGraph(settings.storage.graph_path)
    ts = TemporalFactStore(settings.storage.temporal_path)

    hf_home = os.environ.get("HF_HOME", "")
    if not hf_home:
        cache_dir = Path(__file__).resolve().parent.parent / ".cache" / "hf"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(cache_dir)

    vs = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    t_load = time.perf_counter() - t0

    if entity_history:
        _print_entity_history(ts, entity_history)
        return

    if at_time:
        _print_temporal_query(ts, query_text, at_time)
        return

    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    assembler = ContextAssembler(max_context_tokens=4000)

    t1 = time.perf_counter()
    results = await retriever.retrieve(query=query_text, top_k=top_k, mode=mode)
    t_retrieve = time.perf_counter() - t1

    if not results:
        print(f"No results found for: '{query_text}'")
        return

    temporal_facts = []
    for r in results:
        entity = r.get("entity", "")
        if entity:
            facts = ts.query_current(entity)
            temporal_facts.extend(facts)

    context = assembler.assemble_with_temporal(
        results=results, query=query_text, temporal_facts=temporal_facts
    )

    print(f"Query: {query_text}")
    print(f"Mode: {mode} | Top-K: {top_k}")
    print(f"Load: {t_load:.2f}s | Retrieve: {t_retrieve:.3f}s")
    print("-" * 60)

    for i, r in enumerate(results, 1):
        entity = r.get("entity", "?")
        score = r.get("final_score", 0)
        ppr = r.get("ppr_score", 0)
        text = r.get("text", "")[:120]
        source = r.get("source_doc", "?")
        print(f"  {i}. [{score:.4f}] {entity}")
        print(f"     PPR: {ppr:.4f} | Source: {source}")
        if text:
            print(f"     {text}")

    if verbose:
        print("\n" + "=" * 60)
        print("ASSEMBLED CONTEXT:")
        print("=" * 60)
        print(context)

    graph_stats = kg.get_stats()
    vector_stats = vs.get_stats()
    temporal_stats = ts.get_stats()
    print(
        f"\nKB: {graph_stats['total_nodes']} entities, "
        f"{graph_stats['total_edges']} relations, "
        f"{vector_stats['total_documents']} docs, "
        f"{temporal_stats['total_facts']} facts"
    )


def _print_temporal_query(ts: TemporalFactStore, entity: str, at_time_str: str):
    try:
        at_dt = datetime.fromisoformat(at_time_str)
        if at_dt.tzinfo is None:
            at_dt = at_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"Invalid datetime format: {at_time_str}")
        print("Use ISO format: 2026-03-15 or 2026-03-15T10:00:00+00:00")
        return

    facts = ts.query_at_time(entity, at_dt)
    print(f"Temporal query: entity='{entity}' at {at_dt.isoformat()}")
    print(f"Facts valid at that time: {len(facts)}")
    print("-" * 60)
    for f in facts:
        valid_until = f.valid_until.isoformat() if f.valid_until else "present"
        print(f"  {f.entity}.{f.attribute} = {f.value}")
        print(f"    valid: {f.valid_from.isoformat()} → {valid_until}")
        print(f"    source: {f.source_doc} | confidence: {f.confidence}")


def _print_entity_history(ts: TemporalFactStore, entity: str):
    history = ts.get_entity_history(entity)
    print(f"Entity history: '{entity}'")
    print(f"Total facts: {len(history)}")
    print("-" * 60)

    current = [f for f in history if f.valid_until is None]
    past = [f for f in history if f.valid_until is not None]

    if current:
        print(f"\n  Current ({len(current)}):")
        for f in current:
            print(f"    {f.attribute} = {f.value} (since {f.valid_from.isoformat()})")

    if past:
        print(f"\n  Historical ({len(past)}):")
        for f in past:
            print(f"    {f.attribute} = {f.value}")
            print(f"      {f.valid_from.isoformat()} → {f.valid_until.isoformat()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GAKMS Knowledge Base Query Tool")
    parser.add_argument("query", nargs="+", help="search query or entity name")
    parser.add_argument("-k", "--top-k", type=int, default=10)
    parser.add_argument(
        "-m", "--mode", choices=["low", "high", "hybrid"], default="hybrid"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--at-time",
        type=str,
        default="",
        help="temporal query: show facts valid at this time (ISO format)",
    )
    parser.add_argument(
        "--entity-history",
        type=str,
        default="",
        help="show full history of an entity's facts",
    )
    args = parser.parse_args()

    query_text = " ".join(args.query)
    asyncio.run(
        query(
            query_text,
            top_k=args.top_k,
            mode=args.mode,
            verbose=args.verbose,
            at_time=args.at_time,
            entity_history=args.entity_history,
        )
    )


if __name__ == "__main__":
    main()
