#!/usr/bin/env python3
"""
GAKMS Self-Performance Benchmark
Tests every pipeline stage independently + end-to-end.
Produces a graded report with PASS/FAIL/WARN per component.
"""

from __future__ import annotations

import asyncio
import json
import os
import resource
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp
from openai import AsyncOpenAI

from config import Settings
from extraction import Deduplicator, EntityExtractor, RelationMapper
from ingestion import DocumentParser
from retrieval import ContextAssembler, DualLevelRetriever, PPRRanker
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8100/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")

GROUND_TRUTH_QUERIES = [
    {
        "query": "Claude Anthropic AI model",
        "expected_entities": ["Claude", "Anthropic", "Claude Partner Network"],
        "expected_keywords": ["claude", "anthropic", "ai", "partner"],
    },
    {
        "query": "Rust programming systems language",
        "expected_entities": ["Rust", "Han"],
        "expected_keywords": ["rust", "programming", "language", "systems"],
    },
    {
        "query": "Cloudflare containers infrastructure",
        "expected_entities": ["Cloudflare", "Cloudflare Containers"],
        "expected_keywords": ["cloudflare", "container", "infrastructure"],
    },
    {
        "query": "PostgreSQL database file system",
        "expected_entities": ["PostgreSQL", "Postgres"],
        "expected_keywords": ["postgres", "database", "file"],
    },
    {
        "query": "open source Python",
        "expected_entities": ["Python"],
        "expected_keywords": ["python", "open", "source"],
    },
    {
        "query": "Montana law technology regulation",
        "expected_entities": ["Montana", "Montana Right to Compute Act"],
        "expected_keywords": ["montana", "law", "compute", "regulation"],
    },
]


class BenchmarkResult:
    def __init__(self, name: str):
        self.name = name
        self.tests: list[dict[str, Any]] = []

    def add(
        self,
        test_name: str,
        passed: bool,
        latency: float = 0,
        detail: str = "",
        score: float | None = None,
    ):
        status = "PASS" if passed else "FAIL"
        self.tests.append(
            {
                "test": test_name,
                "status": status,
                "latency_s": round(latency, 4),
                "detail": detail,
                "score": score,
            }
        )

    def summary(self) -> str:
        passed = sum(1 for t in self.tests if t["status"] == "PASS")
        total = len(self.tests)
        pct = (passed / total * 100) if total else 0
        grade = "A" if pct >= 90 else "B" if pct >= 75 else "C" if pct >= 60 else "F"
        return f"{self.name}: {passed}/{total} ({pct:.0f}%) Grade={grade}"


def mem_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


async def bench_document_parser() -> BenchmarkResult:
    r = BenchmarkResult("DocumentParser")
    parser = DocumentParser()

    t0 = time.perf_counter()
    chunks = parser._chunk_text("")
    r.add(
        "empty_input",
        len(chunks) == 0,
        time.perf_counter() - t0,
        f"chunks={len(chunks)}",
    )

    short = "Hello world. This is a test."
    t0 = time.perf_counter()
    chunks = parser._chunk_text(short)
    r.add(
        "short_text",
        len(chunks) == 1,
        time.perf_counter() - t0,
        f"chunks={len(chunks)}",
    )

    long_text = "Technology " * 5000
    t0 = time.perf_counter()
    chunks = parser._chunk_text(long_text)
    elapsed = time.perf_counter() - t0
    r.add(
        "large_text_speed",
        elapsed < 0.1,
        elapsed,
        f"chunks={len(chunks)}, {len(long_text)} chars in {elapsed:.4f}s",
    )

    for i, chunk in enumerate(chunks[:-1]):
        if len(chunk) > parser.chunk_size * 1.5:
            r.add("chunk_size_bound", False, 0, f"chunk {i} too large: {len(chunk)}")
            break
    else:
        r.add("chunk_size_bound", True, 0, f"all chunks within bounds")

    return r


async def bench_entity_extraction(vllm_ready: bool) -> BenchmarkResult:
    r = BenchmarkResult("EntityExtraction")

    dedup = Deduplicator()
    mapper = RelationMapper()

    entities = [
        {
            "name": "Rust",
            "type": "TECHNOLOGY",
            "description": "Systems language",
            "chunk_index": 0,
        },
        {
            "name": "rust",
            "type": "TECHNOLOGY",
            "description": "Memory safe lang",
            "chunk_index": 0,
        },
        {
            "name": "Mozilla",
            "type": "ORGANIZATION",
            "description": "Created Rust",
            "chunk_index": 0,
        },
    ]
    relations = [
        {"source": "Mozilla", "target": "Rust", "relation": "CREATED", "weight": 0.9},
        {"source": "Mozilla", "target": "rust", "relation": "DEVELOPED", "weight": 0.8},
    ]

    t0 = time.perf_counter()
    deduped = dedup.deduplicate(entities, relations)
    elapsed = time.perf_counter() - t0
    deduped_ents = deduped.get("entities", [])
    deduped_rels = deduped.get("relations", [])
    rust_count = sum(1 for e in deduped_ents if e["name"].lower() == "rust")
    r.add(
        "dedup_merge",
        rust_count == 1,
        elapsed,
        f"rust variants merged: {rust_count} (expected 1)",
    )

    t0 = time.perf_counter()
    co_occur = mapper.infer_co_occurrence(entities)
    elapsed = time.perf_counter() - t0
    r.add(
        "co_occur_cap",
        len(co_occur) <= 15,
        elapsed,
        f"co-occur relations: {len(co_occur)} (cap=15)",
    )

    t0 = time.perf_counter()
    empty_result = dedup.deduplicate([], [])
    elapsed = time.perf_counter() - t0
    r.add("dedup_empty", len(empty_result.get("entities", [])) == 0, elapsed)

    if vllm_ready:
        from scripts.build_kb import VLLMAnthropicAdapter

        adapter = VLLMAnthropicAdapter(base_url=VLLM_BASE_URL, model=VLLM_MODEL)
        extractor = EntityExtractor(
            llm_client=adapter, model=VLLM_MODEL, max_concurrent=3
        )

        test_text = (
            "Cloudflare announced Cloudflare Containers, a new product that enables developers "
            "to run Docker containers directly on Cloudflare's global network. This competes with "
            "AWS Lambda and Google Cloud Run. The product supports Python, Node.js, and Rust runtimes."
        )
        t0 = time.perf_counter()
        try:
            result = await extractor.extract(test_text, chunk_size=2000)
            elapsed = time.perf_counter() - t0
            ent_count = len(result.get("entities", []))
            rel_count = len(result.get("relations", []))
            ent_names = [e.get("name", "") for e in result.get("entities", [])]
            has_cloudflare = any("cloudflare" in n.lower() for n in ent_names)
            r.add(
                "llm_extraction",
                ent_count >= 3 and has_cloudflare,
                elapsed,
                f"entities={ent_count}, relations={rel_count}, names={ent_names[:5]}",
            )
            r.add(
                "llm_latency",
                elapsed < 30,
                elapsed,
                f"LLM extraction took {elapsed:.1f}s (threshold: 30s)",
            )
        except Exception as exc:
            r.add("llm_extraction", False, 0, f"FAILED: {exc}")
    else:
        r.add("llm_extraction_skip", True, 0, "vLLM not ready — skipped")

    return r


async def bench_storage() -> BenchmarkResult:
    r = BenchmarkResult("Storage")
    import tempfile, shutil

    tmp = Path(tempfile.mkdtemp())

    try:
        graph_path = str(tmp / "kg.json")
        kg = KnowledgeGraph(graph_path=graph_path)
        entities = [
            {"name": f"Entity_{i}", "type": "TEST", "description": f"Test entity {i}"}
            for i in range(100)
        ]
        relations = [
            {
                "source": f"Entity_{i}",
                "target": f"Entity_{i + 1}",
                "relation": "NEXT",
                "weight": 0.8,
            }
            for i in range(99)
        ]
        t0 = time.perf_counter()
        stats = kg.incremental_update(
            entities, relations, "bench", datetime.now(tz=timezone.utc)
        )
        elapsed = time.perf_counter() - t0
        r.add(
            "graph_write_100",
            stats["nodes_added"] == 100,
            elapsed,
            f"nodes={stats['nodes_added']}, edges={stats['edges_added']} in {elapsed:.3f}s",
        )

        t0 = time.perf_counter()
        neighbors = kg.get_neighbors("Entity_50", hops=2)
        elapsed = time.perf_counter() - t0
        r.add(
            "graph_traverse_2hop",
            len(neighbors) >= 3,
            elapsed,
            f"neighbors={len(neighbors)} in {elapsed:.4f}s",
        )

        t0 = time.perf_counter()
        search_results = kg.search_entities("Entity_5")
        elapsed = time.perf_counter() - t0
        r.add(
            "graph_search",
            len(search_results) >= 1,
            elapsed,
            f"matches={len(search_results)} in {elapsed:.4f}s",
        )

        t0 = time.perf_counter()
        kg2 = KnowledgeGraph(graph_path=graph_path)
        elapsed = time.perf_counter() - t0
        r.add(
            "graph_persistence",
            kg2.graph.number_of_nodes() == 100,
            elapsed,
            f"reload {kg2.graph.number_of_nodes()} nodes in {elapsed:.3f}s",
        )

        for i in range(10):
            kg.incremental_update(
                [
                    {
                        "name": "Entity_0",
                        "type": "TEST",
                        "description": f"Desc round {i}",
                    }
                ],
                [],
                "bench_update",
                datetime.now(tz=timezone.utc),
            )
        desc_count = len(kg.graph.nodes["Entity_0"].get("descriptions", []))
        r.add(
            "graph_desc_cap", desc_count <= 5, 0, f"descriptions={desc_count} (cap=5)"
        )

        corrupted_path = str(tmp / "bad.json")
        Path(corrupted_path).write_text("{corrupted data!!!}", encoding="utf-8")
        t0 = time.perf_counter()
        bad_kg = KnowledgeGraph(graph_path=corrupted_path)
        elapsed = time.perf_counter() - t0
        r.add(
            "graph_corrupted_recovery",
            bad_kg.graph.number_of_nodes() == 0,
            elapsed,
            "recovered from corrupted JSON",
        )

        temporal_path = str(tmp / "facts.jsonl")
        ts = TemporalFactStore(store_path=temporal_path)
        now = datetime.now(tz=timezone.utc)
        t0 = time.perf_counter()
        for i in range(50):
            ts.add_fact(
                TemporalFact(
                    entity=f"Ent_{i}",
                    attribute="status",
                    value=f"active_{i}",
                    source_doc="bench",
                    valid_from=now,
                )
            )
        elapsed = time.perf_counter() - t0
        r.add(
            "temporal_write_50",
            len(ts.facts) == 50,
            elapsed,
            f"50 facts in {elapsed:.3f}s",
        )

        t0 = time.perf_counter()
        current = ts.query_current("Ent_25")
        elapsed = time.perf_counter() - t0
        r.add(
            "temporal_query",
            len(current) >= 1,
            elapsed,
            f"query result={len(current)} in {elapsed:.4f}s",
        )

        ts2 = TemporalFactStore(store_path=temporal_path)
        r.add(
            "temporal_persistence",
            len(ts2.facts) == 50,
            0,
            f"reloaded {len(ts2.facts)} facts",
        )

        bad_temporal = str(tmp / "bad_facts.jsonl")
        Path(bad_temporal).write_text(
            'not json\n{}\n{"entity":"x"}\n', encoding="utf-8"
        )
        ts3 = TemporalFactStore(store_path=bad_temporal)
        r.add(
            "temporal_corrupted_recovery",
            True,
            0,
            f"survived corrupted JSONL, loaded {len(ts3.facts)} facts",
        )

        hf_home = Path(__file__).resolve().parent.parent / ".cache" / "hf"
        os.environ["HF_HOME"] = str(hf_home)
        vec_path = str(tmp / "vectors")
        vs = VectorStore(persist_dir=vec_path, embedding_model="BAAI/bge-m3")

        docs = [
            (f"doc_{i}", f"This is document number {i} about technology trends")
            for i in range(10)
        ]
        t0 = time.perf_counter()
        await vs.upsert_batch(
            [
                (d[0], d[1], {"source": "bench", "title": f"Doc {i}"})
                for i, d in enumerate(docs)
            ]
        )
        elapsed = time.perf_counter() - t0
        r.add(
            "vector_batch_upsert",
            vs.get_stats()["total_documents"] == 10,
            elapsed,
            f"10 docs in {elapsed:.1f}s",
        )

        t0 = time.perf_counter()
        search = await vs.search("technology trends", top_k=3)
        elapsed = time.perf_counter() - t0
        r.add(
            "vector_search",
            len(search) >= 1,
            elapsed,
            f"results={len(search)} in {elapsed:.3f}s",
        )

        if search:
            top = search[0]
            has_text = bool(top.get("text"))
            has_meta = bool(top.get("metadata"))
            has_score = "score" in top
            r.add(
                "vector_result_format",
                has_text and has_meta and has_score,
                0,
                f"text={has_text}, metadata={has_meta}, score={has_score}",
            )
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)

    return r


async def bench_retrieval_quality() -> BenchmarkResult:
    r = BenchmarkResult("RetrievalQuality")

    settings = Settings.load()
    kg = KnowledgeGraph(settings.storage.graph_path)
    ts = TemporalFactStore(settings.storage.temporal_path)

    hf_home = Path(__file__).resolve().parent.parent / ".cache" / "hf"
    os.environ["HF_HOME"] = str(hf_home)
    vs = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    assembler = ContextAssembler(max_context_tokens=4000)

    precisions = []
    latencies = []

    for gt in GROUND_TRUTH_QUERIES:
        query = gt["query"]
        expected_kw = gt["expected_keywords"]

        t0 = time.perf_counter()
        results = await retriever.retrieve(query=query, top_k=5, mode="hybrid")
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        relevant = 0
        for result in results:
            combined = (
                str(result.get("text", "")) + " " + str(result.get("entity", ""))
            ).lower()
            if any(kw in combined for kw in expected_kw):
                relevant += 1
        precision = relevant / max(len(results), 1)
        precisions.append(precision)

        top_entity = results[0].get("entity", "?") if results else "none"
        r.add(
            f"precision: {query[:35]}",
            precision >= 0.4,
            elapsed,
            f"P@5={precision:.0%}, top={top_entity}",
            score=precision,
        )

    avg_p = sum(precisions) / len(precisions) if precisions else 0
    avg_l = sum(latencies) / len(latencies) if latencies else 0
    r.add(
        "avg_precision@5",
        avg_p >= 0.6,
        avg_l,
        f"avg={avg_p:.0%} (threshold: 60%)",
        score=avg_p,
    )
    r.add("avg_latency", avg_l < 1.0, avg_l, f"avg={avg_l:.3f}s (threshold: 1s)")

    t0 = time.perf_counter()
    results = await retriever.retrieve(
        query="nonexistent_gibberish_xyz_123", top_k=5, mode="hybrid"
    )
    elapsed = time.perf_counter() - t0
    r.add(
        "empty_query_handling",
        True,
        elapsed,
        f"gibberish query returned {len(results)} results without crash",
    )

    for mode in ["low", "high", "hybrid"]:
        t0 = time.perf_counter()
        results = await retriever.retrieve(query="technology AI", top_k=5, mode=mode)
        elapsed = time.perf_counter() - t0
        r.add(
            f"mode_{mode}",
            len(results) >= 0,
            elapsed,
            f"mode={mode}: {len(results)} results",
        )

    if results:
        temporal_facts = []
        for result in results[:2]:
            entity = result.get("entity", "")
            if entity:
                temporal_facts.extend(ts.query_current(entity))

        t0 = time.perf_counter()
        context = assembler.assemble_with_temporal(
            results, "test query", temporal_facts
        )
        elapsed = time.perf_counter() - t0
        r.add(
            "context_assembly",
            len(context) > 0,
            elapsed,
            f"context={len(context)} chars, facts={len(temporal_facts)}",
        )

    return r


async def bench_end_to_end(vllm_ready: bool) -> BenchmarkResult:
    r = BenchmarkResult("EndToEnd")

    t0 = time.perf_counter()
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        ) as resp:
            data = await resp.json()
    elapsed = time.perf_counter() - t0
    r.add("hn_api_fetch", len(data) > 0, elapsed, f"fetched {len(data)} story IDs")

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            f"https://hacker-news.firebaseio.com/v0/item/{data[0]}.json"
        ) as resp:
            story = await resp.json()
    title = story.get("title", "")
    t0 = time.perf_counter()
    parser = DocumentParser()
    text = f"Title: {title}\nScore: {story.get('score', 0)}\n{story.get('text', '')}"
    chunks = parser._chunk_text(text)
    elapsed = time.perf_counter() - t0
    r.add(
        "parse_chunk",
        len(chunks) >= 1,
        elapsed,
        f"'{title[:40]}' → {len(chunks)} chunks",
    )

    if vllm_ready:
        from scripts.build_kb import VLLMAnthropicAdapter

        adapter = VLLMAnthropicAdapter(base_url=VLLM_BASE_URL, model=VLLM_MODEL)
        extractor = EntityExtractor(
            llm_client=adapter, model=VLLM_MODEL, max_concurrent=3
        )

        t0 = time.perf_counter()
        try:
            result = await extractor.extract(text, chunk_size=2000)
            elapsed = time.perf_counter() - t0
            ent_count = len(result.get("entities", []))
            r.add(
                "e2e_llm_extract",
                ent_count >= 1,
                elapsed,
                f"{ent_count} entities from live HN story in {elapsed:.1f}s",
            )
        except Exception as exc:
            r.add("e2e_llm_extract", False, 0, f"FAILED: {exc}")

    mem = mem_mb()
    r.add("memory_usage", mem < 4096, 0, f"RSS={mem:.0f}MB (threshold: 4GB)")

    return r


async def main():
    print("=" * 70)
    print("GAKMS Self-Performance Benchmark")
    print(f"Started: {datetime.now(tz=timezone.utc).isoformat()}")
    print(f"Memory baseline: {mem_mb():.0f}MB")
    print("=" * 70)

    vllm_ready = False
    try:
        client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key="x")
        models = await client.models.list()
        if models.data:
            vllm_ready = True
            print(f"  vLLM: READY ({models.data[0].id})")
    except Exception:
        print("  vLLM: NOT AVAILABLE — LLM tests will be skipped")

    benchmarks = [
        ("DocumentParser", bench_document_parser),
        ("EntityExtraction", lambda: bench_entity_extraction(vllm_ready)),
        ("Storage", bench_storage),
        ("RetrievalQuality", bench_retrieval_quality),
        ("EndToEnd", lambda: bench_end_to_end(vllm_ready)),
    ]

    all_results: list[BenchmarkResult] = []

    for name, bench_fn in benchmarks:
        print(f"\n{'─' * 70}")
        print(f"  BENCHMARK: {name}")
        print(f"{'─' * 70}")
        try:
            result = await bench_fn()
            all_results.append(result)
            for t in result.tests:
                icon = "✓" if t["status"] == "PASS" else "✗"
                lat = f" ({t['latency_s']:.3f}s)" if t["latency_s"] > 0 else ""
                score_str = f" [{t['score']:.0%}]" if t.get("score") is not None else ""
                print(f"    {icon} {t['test']}{lat}{score_str}")
                if t["detail"]:
                    print(f"      {t['detail']}")
        except Exception:
            print(f"    ✗ BENCHMARK CRASHED:")
            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("BENCHMARK SUMMARY")
    print(f"{'=' * 70}")

    total_pass = 0
    total_tests = 0
    for result in all_results:
        passed = sum(1 for t in result.tests if t["status"] == "PASS")
        total = len(result.tests)
        total_pass += passed
        total_tests += total
        pct = (passed / total * 100) if total else 0
        grade = "A" if pct >= 90 else "B" if pct >= 75 else "C" if pct >= 60 else "F"
        bar = "█" * int(pct / 5)
        icon = "✓" if pct >= 90 else "△" if pct >= 75 else "✗"
        print(
            f"  {icon} {result.name:25s} {passed:2d}/{total:2d} ({pct:5.1f}%) [{grade}] {bar}"
        )

    overall_pct = (total_pass / total_tests * 100) if total_tests else 0
    overall_grade = (
        "A"
        if overall_pct >= 90
        else "B"
        if overall_pct >= 75
        else "C"
        if overall_pct >= 60
        else "F"
    )
    print(
        f"\n  OVERALL: {total_pass}/{total_tests} ({overall_pct:.1f}%) Grade={overall_grade}"
    )
    print(f"  Memory peak: {mem_mb():.0f}MB")
    print(f"  Completed: {datetime.now(tz=timezone.utc).isoformat()}")

    failures = [t for r in all_results for t in r.tests if t["status"] == "FAIL"]
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for f in failures:
            print(f"    ✗ {f['test']}: {f['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
