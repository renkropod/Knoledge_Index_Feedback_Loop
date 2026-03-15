#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from config import Settings
from extraction import Deduplicator, EntityExtractor, RelationMapper
from ingestion import DocumentParser
from retrieval import ContextAssembler, DualLevelRetriever, PPRRanker
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact


VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8100/v1")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")


class VLLMAnthropicAdapter:
    def __init__(self, base_url: str, model: str):
        self._client = AsyncOpenAI(base_url=base_url, api_key="not-needed")
        self._model = model

    @property
    def messages(self):
        return self

    async def create(
        self,
        model: str = "",
        max_tokens: int = 1024,
        system: str = "",
        messages: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> Any:
        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        for m in messages or []:
            oai_messages.append({"role": m["role"], "content": m["content"]})

        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=oai_messages,
            max_tokens=max_tokens,
            temperature=0.1,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )

        class ContentBlock:
            def __init__(self, text: str):
                self.text = text

        class Usage:
            def __init__(self, inp: int, out: int):
                self.input_tokens = inp
                self.output_tokens = out

        class FakeResponse:
            def __init__(self, content_text: str, usage_obj: Usage, model_name: str):
                self.content = [ContentBlock(content_text)]
                self.usage = usage_obj
                self.model = model_name

        content_text = resp.choices[0].message.content or ""
        usage = resp.usage
        return FakeResponse(
            content_text,
            Usage(
                getattr(usage, "prompt_tokens", 0),
                getattr(usage, "completion_tokens", 0),
            ),
            resp.model,
        )


HN_API = "https://hacker-news.firebaseio.com/v0"
TECH_FEEDS = [
    "https://news.ycombinator.com/",
    "https://lobste.rs/",
    "https://www.reddit.com/r/programming/.json",
]

KNOWN_TECH_ENTITIES: dict[str, str] = {
    "python": "TECHNOLOGY",
    "rust": "TECHNOLOGY",
    "go": "TECHNOLOGY",
    "javascript": "TECHNOLOGY",
    "typescript": "TECHNOLOGY",
    "java": "TECHNOLOGY",
    "c++": "TECHNOLOGY",
    "ruby": "TECHNOLOGY",
    "swift": "TECHNOLOGY",
    "kotlin": "TECHNOLOGY",
    "scala": "TECHNOLOGY",
    "elixir": "TECHNOLOGY",
    "haskell": "TECHNOLOGY",
    "zig": "TECHNOLOGY",
    "julia": "TECHNOLOGY",
    "react": "FRAMEWORK",
    "next.js": "FRAMEWORK",
    "vue": "FRAMEWORK",
    "django": "FRAMEWORK",
    "flask": "FRAMEWORK",
    "fastapi": "FRAMEWORK",
    "spring": "FRAMEWORK",
    "rails": "FRAMEWORK",
    "svelte": "FRAMEWORK",
    "pytorch": "FRAMEWORK",
    "tensorflow": "FRAMEWORK",
    "jax": "FRAMEWORK",
    "linux": "TECHNOLOGY",
    "docker": "TECHNOLOGY",
    "kubernetes": "TECHNOLOGY",
    "postgresql": "TECHNOLOGY",
    "redis": "TECHNOLOGY",
    "sqlite": "TECHNOLOGY",
    "mongodb": "TECHNOLOGY",
    "mysql": "TECHNOLOGY",
    "nginx": "TECHNOLOGY",
    "git": "TECHNOLOGY",
    "wasm": "TECHNOLOGY",
    "webassembly": "TECHNOLOGY",
    "aws": "PLATFORM",
    "gcp": "PLATFORM",
    "azure": "PLATFORM",
    "github": "PLATFORM",
    "gitlab": "PLATFORM",
    "vercel": "PLATFORM",
    "heroku": "PLATFORM",
    "cloudflare": "PLATFORM",
    "supabase": "PLATFORM",
    "openai": "ORGANIZATION",
    "google": "ORGANIZATION",
    "meta": "ORGANIZATION",
    "microsoft": "ORGANIZATION",
    "apple": "ORGANIZATION",
    "amazon": "ORGANIZATION",
    "nvidia": "ORGANIZATION",
    "anthropic": "ORGANIZATION",
    "deepmind": "ORGANIZATION",
    "stripe": "ORGANIZATION",
    "spotify": "ORGANIZATION",
    "netflix": "ORGANIZATION",
    "tesla": "ORGANIZATION",
    "spacex": "ORGANIZATION",
    "intel": "ORGANIZATION",
    "amd": "ORGANIZATION",
    "arm": "ORGANIZATION",
    "oracle": "ORGANIZATION",
    "y combinator": "ORGANIZATION",
    "a16z": "ORGANIZATION",
    "gpt": "MODEL",
    "gpt-4": "MODEL",
    "gpt-4o": "MODEL",
    "claude": "MODEL",
    "llama": "MODEL",
    "gemini": "MODEL",
    "mistral": "MODEL",
    "stable diffusion": "MODEL",
    "midjourney": "MODEL",
    "dall-e": "MODEL",
    "llm": "CONCEPT",
    "rag": "CONCEPT",
    "transformer": "CONCEPT",
    "diffusion model": "CONCEPT",
    "fine-tuning": "CONCEPT",
    "reinforcement learning": "CONCEPT",
    "machine learning": "CONCEPT",
    "deep learning": "CONCEPT",
    "neural network": "CONCEPT",
    "artificial intelligence": "CONCEPT",
    "ai": "CONCEPT",
    "open source": "CONCEPT",
    "api": "CONCEPT",
    "microservices": "CONCEPT",
    "devops": "CONCEPT",
    "ci/cd": "CONCEPT",
    "graphql": "CONCEPT",
    "rest": "CONCEPT",
    "grpc": "CONCEPT",
    "websocket": "CONCEPT",
    "blockchain": "CONCEPT",
    "web3": "CONCEPT",
    "defi": "CONCEPT",
    "cryptocurrency": "CONCEPT",
    "bitcoin": "CONCEPT",
    "ethereum": "CONCEPT",
    "startup": "CONCEPT",
    "saas": "CONCEPT",
    "ipo": "CONCEPT",
    "silicon valley": "LOCATION",
    "san francisco": "LOCATION",
    "new york": "LOCATION",
    "seattle": "LOCATION",
    "austin": "LOCATION",
}

ENTITY_PATTERNS = [
    re.compile(
        r"\b("
        + "|".join(
            re.escape(k)
            for k in sorted(KNOWN_TECH_ENTITIES.keys(), key=len, reverse=True)
        )
        + r")\b",
        re.IGNORECASE,
    ),
]


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


def extract_entities_rule_based(
    text: str, chunk_index: int = 0
) -> dict[str, list[dict[str, Any]]]:
    entities: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    seen_entities: set[str] = set()

    text_lower = text.lower()
    for pattern in ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            name_raw = match.group(1)
            name_lower = name_raw.lower()
            entity_type = KNOWN_TECH_ENTITIES.get(name_lower, "CONCEPT")

            canonical = name_raw
            for known_name in KNOWN_TECH_ENTITIES:
                if known_name.lower() == name_lower:
                    canonical = (
                        known_name.title()
                        if len(known_name) > 3
                        else known_name.upper()
                    )
                    break

            if canonical.lower() in seen_entities:
                continue
            seen_entities.add(canonical.lower())

            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context_snippet = text[start:end].strip().replace("\n", " ")

            entities.append(
                {
                    "name": canonical,
                    "type": entity_type,
                    "description": context_snippet,
                    "chunk_index": chunk_index,
                }
            )

    entity_names = [e["name"] for e in entities]
    for i, src in enumerate(entity_names):
        for tgt in entity_names[i + 1 :]:
            src_pos = text_lower.find(src.lower())
            tgt_pos = text_lower.find(tgt.lower())
            if src_pos >= 0 and tgt_pos >= 0 and abs(src_pos - tgt_pos) < 300:
                relations.append(
                    {
                        "source": src,
                        "target": tgt,
                        "relation": "CO_MENTIONED",
                        "description": f"{src} and {tgt} mentioned together",
                        "weight": 0.6,
                        "chunk_index": chunk_index,
                    }
                )

    return {"entities": entities, "relations": relations}


async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception:
        pass
    return ""


async def fetch_hn_stories(
    session: aiohttp.ClientSession, max_stories: int = 30
) -> list[dict[str, Any]]:
    top_ids_text = await fetch_url(session, f"{HN_API}/topstories.json")
    if not top_ids_text:
        return []

    story_ids = json.loads(top_ids_text)[:max_stories]
    tasks = [fetch_url(session, f"{HN_API}/item/{sid}.json") for sid in story_ids]
    responses = await asyncio.gather(*tasks)

    stories = []
    for raw in responses:
        if not raw:
            continue
        try:
            item = json.loads(raw)
            if item.get("type") == "story" and item.get("title"):
                stories.append(
                    {
                        "title": item["title"],
                        "url": item.get("url", ""),
                        "score": item.get("score", 0),
                        "by": item.get("by", ""),
                        "text": item.get("text", ""),
                        "time": item.get("time", 0),
                        "descendants": item.get("descendants", 0),
                    }
                )
        except (json.JSONDecodeError, KeyError):
            continue
    return stories


async def fetch_article_text(session: aiohttp.ClientSession, url: str) -> str:
    if not url or "pdf" in url.lower():
        return ""
    html = await fetch_url(session, url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.find("body")
    if not article:
        return ""

    text = article.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 30]
    return "\n".join(lines[:100])


async def fetch_lobsters(session: aiohttp.ClientSession) -> list[dict[str, str]]:
    html = await fetch_url(session, "https://lobste.rs/")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for link in soup.select("a.u-url"):
        title = link.get_text(strip=True)
        href = link.get("href", "")
        if title and href:
            items.append({"title": title, "url": href})
    return items[:20]


async def build_knowledge_base():
    print("=" * 70)
    print("GAKMS Knowledge Base Builder — Real Data Pipeline")
    print(f"Started: {datetime.now(tz=timezone.utc).isoformat()}")
    print("=" * 70)

    timers: dict[str, float] = {}

    settings = Settings.load()
    kg = KnowledgeGraph(settings.storage.graph_path)
    ts = TemporalFactStore(settings.storage.temporal_path)

    hf_home = Path(__file__).resolve().parent.parent / ".cache" / "hf"
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home)

    vs = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    parser = DocumentParser()
    deduplicator = Deduplicator()
    relation_mapper = RelationMapper()

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) GAKMS-Bot/1.0"}
    timeout = aiohttp.ClientTimeout(total=15)

    all_documents: list[dict[str, Any]] = []
    total_stats = {
        "sources_fetched": 0,
        "articles_fetched": 0,
        "entities_total": 0,
        "relations_total": 0,
        "docs_indexed": 0,
        "facts_added": 0,
    }

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        with PerfTimer("1. Fetch HN stories (API)") as t:
            hn_stories = await fetch_hn_stories(session, max_stories=30)
        timers["hn_fetch"] = t.elapsed
        total_stats["sources_fetched"] += len(hn_stories)
        print(f"     HN stories: {len(hn_stories)}")

        with PerfTimer("2. Fetch article content (top 15)") as t:
            article_urls = [s["url"] for s in hn_stories if s.get("url")][:15]
            article_tasks = [fetch_article_text(session, url) for url in article_urls]
            article_texts = await asyncio.gather(*article_tasks)
        timers["article_fetch"] = t.elapsed

        for i, story in enumerate(hn_stories):
            doc_text = f"Title: {story['title']}\n"
            doc_text += f"Score: {story['score']} points by {story['by']}\n"
            doc_text += f"Comments: {story['descendants']}\n"
            if story.get("text"):
                doc_text += f"\n{story['text']}\n"
            if i < len(article_texts) and article_texts[i]:
                doc_text += f"\nArticle content:\n{article_texts[i][:3000]}\n"
                total_stats["articles_fetched"] += 1

            all_documents.append(
                {
                    "id": f"hn_{story.get('time', i)}_{i}",
                    "text": doc_text,
                    "source": "hacker_news",
                    "title": story["title"],
                    "url": story.get("url", ""),
                    "timestamp": datetime.fromtimestamp(
                        story.get("time", 0), tz=timezone.utc
                    ),
                }
            )

        print(f"     Articles with content: {total_stats['articles_fetched']}")

        with PerfTimer("3. Fetch Lobsters") as t:
            lobster_items = await fetch_lobsters(session)
        timers["lobsters_fetch"] = t.elapsed
        total_stats["sources_fetched"] += len(lobster_items)
        print(f"     Lobsters items: {len(lobster_items)}")

        for i, item in enumerate(lobster_items):
            all_documents.append(
                {
                    "id": f"lobsters_{i}",
                    "text": f"Title: {item['title']}\nSource: lobste.rs\nURL: {item['url']}",
                    "source": "lobsters",
                    "title": item["title"],
                    "url": item["url"],
                    "timestamp": datetime.now(tz=timezone.utc),
                }
            )

    print(f"\n  Total documents collected: {len(all_documents)}")

    all_entities: list[dict[str, Any]] = []
    all_relations: list[dict[str, Any]] = []

    llm_adapter = VLLMAnthropicAdapter(base_url=VLLM_BASE_URL, model=VLLM_MODEL)
    extractor = EntityExtractor(
        llm_client=llm_adapter,
        model=VLLM_MODEL,
        max_concurrent=5,
    )

    with PerfTimer("4. Entity extraction (LLM — vLLM local)") as t:
        for doc_idx, doc in enumerate(all_documents):
            doc_text = doc["text"][:4000]
            if len(doc_text.strip()) < 50:
                continue
            try:
                result = await extractor.extract(doc_text, chunk_size=2000)
                for ent in result.get("entities", []):
                    ent["source_doc"] = doc["id"]
                all_entities.extend(result.get("entities", []))
                all_relations.extend(result.get("relations", []))
                if (doc_idx + 1) % 10 == 0:
                    print(f"     ... extracted {doc_idx + 1}/{len(all_documents)} docs")
            except Exception as exc:
                print(f"     ⚠ Doc {doc['id']}: extraction failed: {exc}")
                result = extract_entities_rule_based(doc_text)
                for ent in result.get("entities", []):
                    ent["source_doc"] = doc["id"]
                all_entities.extend(result.get("entities", []))
                all_relations.extend(result.get("relations", []))
    timers["extraction"] = t.elapsed
    print(f"     Raw entities: {len(all_entities)}, relations: {len(all_relations)}")

    with PerfTimer("5. Relation inference") as t:
        co_occur = relation_mapper.infer_co_occurrence(all_entities)
        hierarchical = relation_mapper.infer_hierarchical(all_entities)
        all_relations.extend(co_occur)
        all_relations.extend(hierarchical)
    timers["relation_infer"] = t.elapsed
    print(f"     +{len(co_occur)} co-occur, +{len(hierarchical)} hierarchical")

    with PerfTimer("6. Deduplication") as t:
        deduped = deduplicator.deduplicate(all_entities, all_relations)
    timers["dedup"] = t.elapsed
    deduped_entities = deduped.get("entities", [])
    deduped_relations = deduped.get("relations", [])
    total_stats["entities_total"] = len(deduped_entities)
    total_stats["relations_total"] = len(deduped_relations)
    print(
        f"     Deduped: {len(deduped_entities)} entities, {len(deduped_relations)} relations"
    )

    with PerfTimer("7. KnowledgeGraph update") as t:
        graph_stats = kg.incremental_update(
            entities=deduped_entities,
            relations=deduped_relations,
            source_doc="build_kb_run",
            timestamp=datetime.now(tz=timezone.utc),
        )
    timers["graph_store"] = t.elapsed
    print(
        f"     Graph: +{graph_stats['nodes_added']} nodes, +{graph_stats['edges_added']} edges"
    )

    with PerfTimer("8. VectorStore batch upsert") as t:
        batch_items = []
        for doc in all_documents:
            chunks = parser._chunk_text(doc["text"])
            for ci, chunk in enumerate(chunks):
                doc_id = f"{doc['id']}_chunk_{ci}"
                metadata = {
                    "source": doc["source"],
                    "title": doc["title"],
                    "url": doc.get("url", ""),
                    "timestamp": doc["timestamp"].isoformat(),
                    "chunk_index": ci,
                }
                batch_items.append((doc_id, chunk, metadata))
        await vs.upsert_batch(batch_items)
    timers["vector_store"] = t.elapsed
    total_stats["docs_indexed"] = len(batch_items)
    print(f"     Vectors: {len(batch_items)} chunks indexed")

    with PerfTimer("9. TemporalFactStore") as t:
        now = datetime.now(tz=timezone.utc)
        for ent in deduped_entities:
            name = ent.get("name", "")
            etype = ent.get("type", "UNKNOWN")
            if name:
                ts.add_fact(
                    TemporalFact(
                        entity=name,
                        attribute="entity_type",
                        value=etype,
                        source_doc="build_kb_run",
                        valid_from=now,
                    )
                )
                total_stats["facts_added"] += 1
    timers["temporal_store"] = t.elapsed
    print(f"     Facts: {total_stats['facts_added']}")

    doc_dir = Path("knowledge_base/documents")
    doc_dir.mkdir(parents=True, exist_ok=True)
    for doc in all_documents:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", doc["title"][:50].lower()).strip("-")
        ts_str = doc["timestamp"].strftime("%Y%m%d_%H%M%S")
        filepath = doc_dir / f"{ts_str}_{slug}.md"
        body = f"---\ntitle: {doc['title']}\nsource: {doc['source']}\nurl: {doc.get('url', '')}\n---\n\n{doc['text']}"
        filepath.write_text(body, encoding="utf-8")

    print(f"\n  Saved {len(all_documents)} documents to {doc_dir}")

    print("\n" + "=" * 70)
    print("RETRIEVAL QUALITY VALIDATION")
    print("=" * 70)

    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    assembler = ContextAssembler(max_context_tokens=4000)

    test_queries = [
        "latest AI and machine learning trends",
        "Rust programming language",
        "open source projects",
        "cloud infrastructure and DevOps",
        "startup funding and Y Combinator",
        "Python web frameworks",
        "large language models GPT Claude",
    ]

    retrieval_results = []
    for query in test_queries:
        with PerfTimer(f"Query: '{query}'") as t:
            results = await retriever.retrieve(query=query, top_k=5, mode="hybrid")
        timers[f"q_{query[:20]}"] = t.elapsed

        hit_count = len(results)
        top_score = results[0]["final_score"] if results else 0
        top_entity = results[0].get("entity", "?") if results else "none"

        relevance_hits = 0
        query_tokens = set(query.lower().split())
        for r in results:
            r_text = (str(r.get("text", "")) + str(r.get("entity", ""))).lower()
            if any(tok in r_text for tok in query_tokens):
                relevance_hits += 1

        precision = relevance_hits / max(hit_count, 1)
        retrieval_results.append(
            {
                "query": query,
                "hits": hit_count,
                "top_score": top_score,
                "top_entity": top_entity,
                "precision": precision,
                "latency": t.elapsed,
            }
        )

        print(
            f"     Hits: {hit_count} | Top: {top_entity} ({top_score:.4f}) | Precision@5: {precision:.0%} | {t.elapsed:.3f}s"
        )

    avg_precision = sum(r["precision"] for r in retrieval_results) / len(
        retrieval_results
    )
    avg_latency = sum(r["latency"] for r in retrieval_results) / len(retrieval_results)

    print("\n" + "=" * 70)
    print("SELF-CRITIQUE & PERFORMANCE ANALYSIS")
    print("=" * 70)

    graph_stats_final = kg.get_stats()
    vector_stats_final = vs.get_stats()
    temporal_stats_final = ts.get_stats()

    print(f"\n  Knowledge Base Stats:")
    print(
        f"    Graph: {graph_stats_final['total_nodes']} entities, {graph_stats_final['total_edges']} relations"
    )
    print(f"    Vectors: {vector_stats_final['total_documents']} chunks")
    print(f"    Temporal: {temporal_stats_final['total_facts']} facts")

    print(f"\n  Retrieval Quality:")
    print(f"    Avg Precision@5: {avg_precision:.0%}")
    print(f"    Avg Latency: {avg_latency:.3f}s")

    print(f"\n  Pipeline Performance:")
    total_time = sum(v for k, v in timers.items() if not k.startswith("q_"))
    for label, elapsed in timers.items():
        if label.startswith("q_"):
            continue
        pct = (elapsed / total_time * 100) if total_time > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"    {label:25s} {elapsed:8.3f}s  {pct:5.1f}% {bar}")
    print(f"    {'TOTAL':25s} {total_time:8.3f}s")

    issues: list[str] = []
    if avg_precision < 0.5:
        issues.append(
            f"LOW PRECISION ({avg_precision:.0%}): Rule-based extraction misses semantic context. LLM extraction needed for production."
        )
    if avg_latency > 1.0:
        issues.append(
            f"HIGH LATENCY ({avg_latency:.3f}s): Retrieval too slow. Consider caching or index optimization."
        )
    if graph_stats_final["total_nodes"] < 20:
        issues.append(
            f"LOW ENTITY COUNT ({graph_stats_final['total_nodes']}): Dictionary too small or text extraction failing."
        )
    if total_stats["articles_fetched"] < 5:
        issues.append(
            f"LOW ARTICLE FETCH ({total_stats['articles_fetched']}): Many URLs failed. Add retry logic or proxy support."
        )

    print(f"\n  Issues Found: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")

    if not issues:
        print("    No critical issues found.")

    print(f"\n  Completed: {datetime.now(tz=timezone.utc).isoformat()}")
    return {
        "timers": timers,
        "stats": total_stats,
        "retrieval": retrieval_results,
        "issues": issues,
    }


if __name__ == "__main__":
    asyncio.run(build_knowledge_base())
