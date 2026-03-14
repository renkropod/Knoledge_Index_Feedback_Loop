#!/usr/bin/env python3
"""
End-to-end pipeline test using Hacker News front page.
Measures performance at each stage:
  1. Fetch HN HTML
  2. Parse to structured text
  3. Extract entities/relations (LLM)
  4. Deduplicate
  5. Store in KG + Vector + Temporal
  6. Retrieve by query
  7. Assemble context
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp
from bs4 import BeautifulSoup

from config import Settings
from extraction import Deduplicator, EntityExtractor, RelationMapper
from ingestion import DocumentParser
from retrieval import ContextAssembler, DualLevelRetriever
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact


class PerfTimer:
    def __init__(self, label: str):
        self.label = label
        self.elapsed: float = 0.0
        self._start: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start
        print(f"  [{self.label}] {self.elapsed:.3f}s")


async def fetch_hn_html() -> str:
    timeout = aiohttp.ClientTimeout(total=15)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0"
    }
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get("https://news.ycombinator.com/") as resp:
            return await resp.text()


def parse_hn_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    items: list[str] = []
    for row in soup.select("tr.athing"):
        rank_el = row.select_one("span.rank")
        title_el = row.select_one("span.titleline > a")
        if not title_el:
            continue

        rank = rank_el.get_text(strip=True) if rank_el else ""
        title = title_el.get_text(strip=True)
        href = title_el.get("href", "")

        subtext_row = row.find_next_sibling("tr")
        score = ""
        author = ""
        age = ""
        comments = ""
        if subtext_row:
            score_el = subtext_row.select_one("span.score")
            user_el = subtext_row.select_one("a.hnuser")
            age_el = subtext_row.select_one("span.age")
            comment_links = subtext_row.select("a")
            if score_el:
                score = score_el.get_text(strip=True)
            if user_el:
                author = user_el.get_text(strip=True)
            if age_el:
                age = age_el.get_text(strip=True)
            for link in comment_links:
                text = link.get_text(strip=True)
                if "comment" in text.lower():
                    comments = text
                    break

        entry = f"{rank} {title}"
        if href and not href.startswith("item?"):
            entry += f" ({href})"
        meta_parts = [p for p in [score, author, age, comments] if p]
        if meta_parts:
            entry += f" - {', '.join(meta_parts)}"
        items.append(entry)

    header = (
        f"Hacker News Front Page - {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Total items: {len(items)}\n"
    )
    return header + "\n".join(items)


async def run_pipeline():
    print("=" * 60)
    print("GAKMS End-to-End Pipeline Test — Hacker News")
    print("=" * 60)

    timers: dict[str, float] = {}

    test_dir = Path("knowledge_base/_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    graph_path = str(test_dir / "test_kg.json")
    vector_path = str(test_dir / "test_vectors")
    temporal_path = str(test_dir / "test_facts.jsonl")

    with PerfTimer("1. Fetch HN") as t:
        html = await fetch_hn_html()
    timers["fetch"] = t.elapsed
    print(f"     HTML size: {len(html):,} bytes")

    with PerfTimer("2. Parse HTML → text") as t:
        hn_text = parse_hn_to_text(html)
    timers["parse"] = t.elapsed
    print(f"     Text size: {len(hn_text):,} chars, lines: {hn_text.count(chr(10))}")

    with PerfTimer("2b. DocumentParser chunk") as t:
        parser = DocumentParser(chunk_size=2000, chunk_overlap=200)
        chunks = parser._chunk_text(hn_text)
    timers["chunk"] = t.elapsed
    print(f"     Chunks: {len(chunks)}")

    settings = Settings.load()
    api_key = settings.llm_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n  ⚠ ANTHROPIC_API_KEY not set — skipping LLM extraction.")
        print("     Testing storage + retrieval with synthetic entities.\n")
        entities = [
            {
                "name": "Hacker News",
                "type": "PLATFORM",
                "description": "Y Combinator tech news aggregator",
            },
            {
                "name": "Y Combinator",
                "type": "ORGANIZATION",
                "description": "Silicon Valley startup accelerator",
            },
            {
                "name": "Paul Graham",
                "type": "PERSON",
                "description": "Co-founder of Y Combinator and Hacker News",
            },
            {
                "name": "Rust",
                "type": "TECHNOLOGY",
                "description": "Systems programming language",
            },
            {
                "name": "Python",
                "type": "TECHNOLOGY",
                "description": "High-level programming language",
            },
            {
                "name": "LLM",
                "type": "CONCEPT",
                "description": "Large Language Model for AI text generation",
            },
            {
                "name": "GPT",
                "type": "TECHNOLOGY",
                "description": "Generative Pre-trained Transformer by OpenAI",
            },
            {
                "name": "Open Source",
                "type": "CONCEPT",
                "description": "Software with publicly available source code",
            },
            {
                "name": "Startup",
                "type": "CONCEPT",
                "description": "Early-stage technology company",
            },
            {
                "name": "Silicon Valley",
                "type": "LOCATION",
                "description": "Tech industry hub in California",
            },
        ]
        relations = [
            {
                "source": "Y Combinator",
                "target": "Hacker News",
                "relation": "OPERATES",
                "description": "YC runs HN",
                "weight": 0.95,
            },
            {
                "source": "Paul Graham",
                "target": "Y Combinator",
                "relation": "FOUNDED",
                "description": "PG co-founded YC",
                "weight": 0.95,
            },
            {
                "source": "Y Combinator",
                "target": "Silicon Valley",
                "relation": "LOCATED_IN",
                "description": "YC is in SV",
                "weight": 0.9,
            },
            {
                "source": "Y Combinator",
                "target": "Startup",
                "relation": "ACCELERATES",
                "description": "YC funds startups",
                "weight": 0.9,
            },
            {
                "source": "GPT",
                "target": "LLM",
                "relation": "IS_A",
                "description": "GPT is a type of LLM",
                "weight": 0.95,
            },
            {
                "source": "Rust",
                "target": "Open Source",
                "relation": "IS",
                "description": "Rust is open source",
                "weight": 0.8,
            },
            {
                "source": "Python",
                "target": "Open Source",
                "relation": "IS",
                "description": "Python is open source",
                "weight": 0.8,
            },
        ]
        timers["extraction"] = 0.0
    else:
        import anthropic

        llm_client = anthropic.AsyncAnthropic(api_key=api_key)
        extractor = EntityExtractor(
            llm_client=llm_client, model=settings.llm.extraction_model
        )

        with PerfTimer("3. Entity/Relation extraction (LLM)") as t:
            raw_extraction = await extractor.extract(hn_text, chunk_size=2000)
        timers["extraction"] = t.elapsed
        entities = raw_extraction.get("entities", [])
        relations = raw_extraction.get("relations", [])
        print(f"     Raw entities: {len(entities)}, relations: {len(relations)}")

    with PerfTimer("4. RelationMapper infer") as t:
        mapper = RelationMapper()
        co_occur = mapper.infer_co_occurrence(entities)
        hierarchical = mapper.infer_hierarchical(entities)
        relations.extend(co_occur)
        relations.extend(hierarchical)
    timers["relation_map"] = t.elapsed
    print(
        f"     After inference: +{len(co_occur)} co-occur, +{len(hierarchical)} hierarchical"
    )

    with PerfTimer("5. Deduplication") as t:
        deduplicator = Deduplicator()
        deduped = deduplicator.deduplicate(entities, relations)
    timers["dedup"] = t.elapsed
    deduped_entities = deduped.get("entities", [])
    deduped_relations = deduped.get("relations", [])
    print(
        f"     After dedup: {len(deduped_entities)} entities, {len(deduped_relations)} relations"
    )

    with PerfTimer("6a. KnowledgeGraph store") as t:
        kg = KnowledgeGraph(graph_path=graph_path)
        graph_stats = kg.incremental_update(
            entities=deduped_entities,
            relations=deduped_relations,
            source_doc="hn_frontpage",
            timestamp=datetime.now(tz=timezone.utc),
        )
    timers["graph_store"] = t.elapsed
    print(
        f"     Graph: +{graph_stats['nodes_added']} nodes, +{graph_stats['edges_added']} edges"
    )

    with PerfTimer("6b-init. VectorStore init (lazy)") as t:
        vs = VectorStore(persist_dir=vector_path, embedding_model="BAAI/bge-m3")
    timers["vector_init"] = t.elapsed

    with PerfTimer("6b. VectorStore batch upsert") as t:
        batch_items = [
            (f"hn_chunk_{i}", chunk, {"source_doc": "hn_frontpage", "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]
        await vs.upsert_batch(batch_items)
    timers["vector_store"] = t.elapsed
    print(f"     Vectors: {len(chunks)} chunks upserted (batch)")

    with PerfTimer("6c. TemporalFactStore") as t:
        ts = TemporalFactStore(store_path=temporal_path)
        now = datetime.now(tz=timezone.utc)
        for ent in deduped_entities[:20]:
            name = ent.get("name", "")
            etype = ent.get("type", "unknown")
            if name:
                ts.add_fact(
                    TemporalFact(
                        entity=name,
                        attribute="entity_type",
                        value=etype,
                        source_doc="hn_frontpage",
                        valid_from=now,
                    )
                )
    timers["temporal_store"] = t.elapsed
    print(f"     Facts stored: {len(ts.facts)}")

    test_queries = [
        "technology trends on Hacker News",
        "Y Combinator startups",
        "open source programming languages",
    ]

    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    assembler = ContextAssembler(max_context_tokens=4000)

    for query in test_queries:
        with PerfTimer(f"7. Retrieve: '{query}'") as t:
            results = await retriever.retrieve(query=query, top_k=5, mode="hybrid")
        timers[f"retrieve_{query[:20]}"] = t.elapsed
        print(f"     Results: {len(results)}")

        if results:
            with PerfTimer(f"8. Assemble context") as t:
                context = assembler.assemble(results, query)
            timers[f"assemble_{query[:20]}"] = t.elapsed
            print(f"     Context length: {len(context)} chars")

            top = results[0]
            print(
                f"     Top result: entity='{top.get('entity', '?')}' score={top.get('final_score', 0):.4f}"
            )

    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    total = sum(timers.values())
    for label, elapsed in timers.items():
        pct = (elapsed / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {label:30s} {elapsed:8.3f}s  {pct:5.1f}% {bar}")
    print(f"  {'TOTAL':30s} {total:8.3f}s")

    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE STATS")
    print("=" * 60)
    print(f"  Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"  Graph edges: {kg.graph.number_of_edges()}")
    print(f"  Vector docs: {vs.get_stats()['total_documents']}")
    print(f"  Temporal facts: {len(ts.facts)}")

    import shutil

    shutil.rmtree(str(test_dir), ignore_errors=True)
    print(f"\n  Cleaned up test data at {test_dir}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
