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

from config import Settings
from config.llm_client import create_llm_client, get_model_name
from extraction import Deduplicator, EntityExtractor, RelationMapper
from ingestion import DocumentParser
from retrieval import ContextAssembler, DualLevelRetriever
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact

ALGOLIA_SEARCH = "http://hn.algolia.com/api/v1/search"
ALGOLIA_ITEM = "http://hn.algolia.com/api/v1/items"

KOREAN_EXTRACTION_PROMPT_TPL = (
    "아래 텍스트에서 엔티티(개체)와 관계를 추출하세요.\n\n"
    "## 규칙\n"
    "1. 반드시 텍스트에 실제로 등장하는 엔티티만 추출하세요. 텍스트에 없는 엔티티를 만들지 마세요.\n"
    "2. 엔티티의 description은 반드시 한국어로 작성하세요.\n"
    "3. 관계의 description도 한국어로 작성하세요.\n"
    "4. 엔티티 이름(name)은 원문 그대로 유지하세요 (영어면 영어, 한국어면 한국어).\n"
    "5. 엔티티는 최대 15개, 관계는 최대 10개까지만 추출하세요.\n\n"
    "## 출력 형식 (JSON만 출력)\n"
    '{"entities": [{"name": "엔티티명", "type": "유형", "description": "한국어 설명"}], '
    '"relations": [{"source": "소스", "target": "타겟", "relation": "관계유형", "description": "한국어 설명", "weight": 0.9}]}\n\n'
    "## 텍스트\n"
)


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
        print(f"  [{self.label}] {self.elapsed:.1f}s")


async def fetch_algolia_stories(
    session: aiohttp.ClientSession,
    days: int = 30,
    min_points: int = 10,
    max_stories: int = 4000,
) -> list[dict[str, Any]]:
    now = int(time.time())
    stories: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    chunk_days = 5
    for start_offset in range(0, days, chunk_days):
        end_offset = start_offset + chunk_days
        ts_start = now - end_offset * 86400
        ts_end = now - start_offset * 86400
        page = 0

        while len(stories) < max_stories:
            params = {
                "tags": "story",
                "numericFilters": f"created_at_i>{ts_start},created_at_i<{ts_end},points>{min_points}",
                "hitsPerPage": 100,
                "page": page,
            }
            try:
                async with session.get(ALGOLIA_SEARCH, params=params) as resp:
                    data = await resp.json()
            except Exception:
                break

            hits = data.get("hits", [])
            if not hits:
                break

            for hit in hits:
                oid = hit.get("objectID", "")
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)
                stories.append(
                    {
                        "title": hit.get("title", ""),
                        "url": hit.get("url", ""),
                        "points": hit.get("points", 0),
                        "author": hit.get("author", ""),
                        "created_at": hit.get("created_at_i", 0),
                        "num_comments": hit.get("num_comments", 0),
                        "objectID": oid,
                        "source": "hacker_news",
                    }
                )

            page += 1
            nb_pages = data.get("nbPages", 0)
            if page >= nb_pages:
                break
            await asyncio.sleep(0.15)

        if len(stories) >= max_stories:
            break

    stories.sort(key=lambda s: s.get("points", 0), reverse=True)
    return stories[:max_stories]


async def fetch_lobsters(
    session: aiohttp.ClientSession, pages: int = 10
) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        try:
            async with session.get(f"https://lobste.rs/page/{page}.json") as resp:
                if resp.status != 200:
                    break
                items = await resp.json()
        except Exception:
            break
        for item in items:
            stories.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "points": item.get("score", 0),
                    "author": item.get("submitter_user", "")
                    if isinstance(item.get("submitter_user"), str)
                    else (item.get("submitter_user") or {}).get("username", ""),
                    "created_at": 0,
                    "num_comments": item.get("comment_count", 0),
                    "objectID": f"lob_{item.get('short_id', '')}",
                    "source": "lobsters",
                }
            )
        await asyncio.sleep(0.3)
    return stories


async def fetch_devto(
    session: aiohttp.ClientSession, pages: int = 5
) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        try:
            async with session.get(
                "https://dev.to/api/articles",
                params={"top": "30", "per_page": "100", "page": str(page)},
            ) as resp:
                if resp.status != 200:
                    break
                items = await resp.json()
        except Exception:
            break
        for item in items:
            stories.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "points": item.get("positive_reactions_count", 0),
                    "author": item.get("user", {}).get("username", ""),
                    "created_at": 0,
                    "num_comments": item.get("comments_count", 0),
                    "objectID": f"devto_{item.get('id', '')}",
                    "source": "dev.to",
                }
            )
        await asyncio.sleep(0.3)
    return stories


async def fetch_rss(
    session: aiohttp.ClientSession, feeds: list[tuple[str, str]]
) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    for feed_name, feed_url in feeds:
        try:
            async with session.get(feed_url) as resp:
                if resp.status != 200:
                    continue
                xml = await resp.text()
        except Exception:
            continue
        soup = BeautifulSoup(xml, "html.parser")
        for item in soup.find_all("item")[:30]:
            title_el = item.find("title")
            link_el = item.find("link")
            if not title_el:
                continue
            stories.append(
                {
                    "title": title_el.get_text(strip=True),
                    "url": link_el.get_text(strip=True) if link_el else "",
                    "points": 0,
                    "author": feed_name,
                    "created_at": 0,
                    "num_comments": 0,
                    "objectID": f"rss_{feed_name}_{len(stories)}",
                    "source": feed_name,
                }
            )
    return stories


async def fetch_article_text(session: aiohttp.ClientSession, url: str) -> str:
    if not url or "pdf" in url.lower() or "youtube.com" in url.lower():
        return ""
    try:
        async with session.get(url) as resp:
            if resp.status >= 400:
                return ""
            html = await resp.text(errors="ignore")
    except Exception:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.find("body")
    if not article:
        return ""

    text = article.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 30]
    return "\n".join(lines[:80])


async def build_monthly_kb():
    print("=" * 70)
    print("HN Monthly KB Builder (Korean)")
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

    llm_client = create_llm_client()
    model_name = get_model_name()
    extractor = EntityExtractor(
        llm_client=llm_client,
        model=model_name,
        max_concurrent=5,
    )
    deduplicator = Deduplicator()
    relation_mapper = RelationMapper()
    parser = DocumentParser()

    print(f"  LLM: {model_name}")
    print(f"  KB before: {kg.get_stats()['total_nodes']} entities")

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) GAKMS-Bot/1.0"}
    timeout = aiohttp.ClientTimeout()

    stats = {
        "stories_fetched": 0,
        "articles_fetched": 0,
        "entities_total": 0,
        "relations_total": 0,
        "docs_indexed": 0,
        "facts_added": 0,
    }

    rss_feeds = [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("ArsTechnica", "https://feeds.arstechnica.com/arstechnica/index"),
        ("TheVerge", "https://www.theverge.com/rss/index.xml"),
    ]

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        with PerfTimer("1a. Fetch HN stories (Algolia, 30d, 10+ pts)") as t:
            stories = await fetch_algolia_stories(
                session, days=30, min_points=10, max_stories=4000
            )
        timers["fetch_hn"] = t.elapsed
        print(f"     HN stories: {len(stories)}")

        with PerfTimer("1b. Fetch Lobsters") as t:
            lob_stories = await fetch_lobsters(session, pages=10)
        timers["fetch_lobsters"] = t.elapsed
        print(f"     Lobsters: {len(lob_stories)}")

        with PerfTimer("1c. Fetch Dev.to") as t:
            devto_stories = await fetch_devto(session, pages=5)
        timers["fetch_devto"] = t.elapsed
        print(f"     Dev.to: {len(devto_stories)}")

        with PerfTimer("1d. Fetch RSS feeds") as t:
            rss_stories = await fetch_rss(session, rss_feeds)
        timers["fetch_rss"] = t.elapsed
        print(f"     RSS: {len(rss_stories)}")

        seen_titles: set[str] = set()
        all_stories: list[dict[str, Any]] = []
        for s in stories + lob_stories + devto_stories + rss_stories:
            title_key = s["title"].lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            all_stories.append(s)

        stats["stories_fetched"] = len(all_stories)
        print(f"     Total unique: {len(all_stories)}")

        with PerfTimer("2. Fetch article content (top 300)") as t:
            article_urls = [s["url"] for s in all_stories if s.get("url")][:300]
            sem = asyncio.Semaphore(10)

            async def fetch_with_sem(url):
                async with sem:
                    return await fetch_article_text(session, url)

            tasks = [fetch_with_sem(url) for url in article_urls]
            article_texts = await asyncio.gather(*tasks)
            url_to_text = dict(zip(article_urls, article_texts))
        timers["fetch_articles"] = t.elapsed
        fetched_count = sum(1 for t in article_texts if t)
        stats["articles_fetched"] = fetched_count
        print(f"     Articles with content: {fetched_count}/{len(article_urls)}")

    all_documents: list[dict[str, Any]] = []
    for story in all_stories:
        doc_text = f"Title: {story['title']}\n"
        doc_text += f"Points: {story['points']}, Author: {story['author']}, Comments: {story['num_comments']}\n"
        article_text = url_to_text.get(story.get("url", ""), "")
        if article_text:
            doc_text += f"\n{article_text[:3000]}\n"

        ts_val = story.get("created_at", 0)
        created = (
            datetime.fromtimestamp(ts_val, tz=timezone.utc)
            if ts_val
            else datetime.now(tz=timezone.utc)
        )

        all_documents.append(
            {
                "id": f"hn_{story['objectID']}",
                "text": doc_text,
                "source": "hacker_news",
                "title": story["title"],
                "url": story.get("url", ""),
                "points": story["points"],
                "timestamp": created,
            }
        )

    print(f"\n  Total documents: {len(all_documents)}")

    all_entities: list[dict[str, Any]] = []
    all_relations: list[dict[str, Any]] = []

    extraction_sem = asyncio.Semaphore(5)

    async def _extract_korean(
        doc_info: dict[str, Any], text: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            prompt_text = KOREAN_EXTRACTION_PROMPT_TPL + text
            async with extraction_sem:
                resp = await llm_client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt_text}],
                )
            raw = resp.content[0].text
            json_match = re.search(r"\{[\s\S]*\}", raw)
            if not json_match:
                return doc_info, {"entities": [], "relations": []}
            parsed = json.loads(json_match.group())
            entities = parsed.get("entities", [])
            relations = parsed.get("relations", [])
            parsed["entities"] = [
                ent
                for ent in entities
                if isinstance(ent, dict)
                and isinstance(ent.get("name"), str)
                and ent.get("name", "").strip()
            ]
            parsed["relations"] = [
                rel
                for rel in relations
                if isinstance(rel, dict)
                and isinstance(rel.get("source"), str)
                and rel.get("source", "").strip()
                and isinstance(rel.get("target"), str)
                and rel.get("target", "").strip()
            ]
            return doc_info, parsed
        except Exception:
            return doc_info, {"entities": [], "relations": []}

    with PerfTimer("3. Entity extraction (Korean, vLLM)") as t:
        batch_size = 20
        for batch_start in range(0, len(all_documents), batch_size):
            batch = all_documents[batch_start : batch_start + batch_size]
            batch_tasks = []

            for doc in batch:
                doc_text = doc["text"][:4000]
                if len(doc_text.strip()) < 50:
                    continue
                batch_tasks.append((doc, doc_text))

            if not batch_tasks:
                done = min(batch_start + batch_size, len(all_documents))
                continue

            results = await asyncio.gather(
                *[_extract_korean(d, txt) for d, txt in batch_tasks]
            )

            for doc_info, result in results:
                text_lower = doc_info["text"].lower()
                for ent in result.get("entities", []):
                    if isinstance(ent, str):
                        ent = {"name": ent, "type": "CONCEPT", "description": ent}
                    if not isinstance(ent, dict):
                        continue
                    name = str(ent.get("name", "")).strip()
                    if not name:
                        continue
                    if name.lower() not in text_lower:
                        tokens = name.lower().split()
                        if len(tokens) < 2 or sum(
                            1 for tk in tokens if tk in text_lower and len(tk) > 2
                        ) < max(2, len(tokens) // 2):
                            continue
                    ent["source_doc"] = doc_info["id"]
                    all_entities.append(ent)

                grounded_names = {
                    e.get("name", "")
                    for e in all_entities
                    if e.get("source_doc") == doc_info["id"]
                }
                for rel in result.get("relations", []):
                    if not isinstance(rel, dict):
                        continue
                    src = str(rel.get("source", ""))
                    tgt = str(rel.get("target", ""))
                    if src in grounded_names and tgt in grounded_names:
                        rel["source_doc"] = doc_info["id"]
                        all_relations.append(rel)

            done = min(batch_start + batch_size, len(all_documents))
            print(
                f"     ... {done}/{len(all_documents)} docs (batch={len(batch_tasks)}), {len(all_entities)} entities, {len(all_relations)} relations"
            )

    timers["extraction"] = t.elapsed
    stats["entities_total"] = len(all_entities)
    stats["relations_total"] = len(all_relations)

    with PerfTimer("4. Relation inference + Dedup") as t:
        co_occur = relation_mapper.infer_co_occurrence(all_entities)
        hierarchical = relation_mapper.infer_hierarchical(all_entities)
        all_relations.extend(co_occur)
        all_relations.extend(hierarchical)
        deduped = deduplicator.deduplicate(all_entities, all_relations)
    timers["dedup"] = t.elapsed
    deduped_entities = deduped.get("entities", [])
    deduped_relations = deduped.get("relations", [])
    print(
        f"     Deduped: {len(deduped_entities)} entities, {len(deduped_relations)} relations"
    )

    with PerfTimer("5. Graph update") as t:
        graph_stats = kg.incremental_update(
            entities=deduped_entities,
            relations=deduped_relations,
            source_doc="hn_monthly_build",
            timestamp=datetime.now(tz=timezone.utc),
        )
    timers["graph"] = t.elapsed
    print(
        f"     +{graph_stats['nodes_added']} nodes, +{graph_stats['edges_added']} edges"
    )

    with PerfTimer("6. Vector batch upsert") as t:
        batch_items = []
        for doc in all_documents:
            chunks = parser._chunk_text(doc["text"])
            for ci, chunk in enumerate(chunks):
                doc_id = f"{doc['id']}_chunk_{ci}"
                metadata = {
                    "source": "hacker_news",
                    "title": doc["title"],
                    "url": doc.get("url", ""),
                    "points": str(doc["points"]),
                    "timestamp": doc["timestamp"].isoformat(),
                }
                batch_items.append((doc_id, chunk, metadata))
        await vs.upsert_batch(batch_items)
    timers["vector"] = t.elapsed
    stats["docs_indexed"] = len(batch_items)
    print(f"     {len(batch_items)} chunks indexed")

    with PerfTimer("7. Temporal facts") as t:
        now = datetime.now(tz=timezone.utc)
        for ent in deduped_entities:
            name = ent.get("name", "")
            etype = ent.get("type", "unknown")
            if name:
                ts.add_fact(
                    TemporalFact(
                        entity=name,
                        attribute="entity_type",
                        value=etype,
                        source_doc="hn_monthly_build",
                        valid_from=now,
                    )
                )
                stats["facts_added"] += 1
    timers["temporal"] = t.elapsed

    doc_dir = Path("knowledge_base/documents")
    doc_dir.mkdir(parents=True, exist_ok=True)
    for doc in all_documents:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", doc["title"][:50].lower()).strip("-")
        ts_str = doc["timestamp"].strftime("%Y%m%d_%H%M%S")
        filepath = doc_dir / f"{ts_str}_{slug}.md"
        if not filepath.exists():
            body = f"---\ntitle: {doc['title']}\nsource: hacker_news\nurl: {doc.get('url', '')}\npoints: {doc['points']}\n---\n\n{doc['text']}"
            filepath.write_text(body, encoding="utf-8")

    print(f"\n{'=' * 70}")
    print("RETRIEVAL TEST (Korean)")
    print("=" * 70)

    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    test_queries = [
        "인공지능 최신 트렌드",
        "Rust 프로그래밍 언어",
        "오픈소스 프로젝트",
        "스타트업 투자",
        "클라우드 인프라",
    ]
    for q in test_queries:
        results = await retriever.retrieve(query=q, top_k=5, mode="hybrid")
        top = results[0] if results else {}
        top_ent = top.get("entity", "없음")
        top_score = top.get("final_score", 0)
        print(f"  '{q}' → {top_ent} ({top_score:.4f}), {len(results)} hits")

    print(f"\n{'=' * 70}")
    print("FINAL STATS")
    print("=" * 70)
    final_stats = kg.get_stats()
    print(
        f"  Graph: {final_stats['total_nodes']} entities, {final_stats['total_edges']} relations"
    )
    print(f"  Vectors: {vs.get_stats()['total_documents']} chunks")
    print(f"  Temporal: {ts.get_stats()['total_facts']} facts")
    print(f"  Documents: {len(list(doc_dir.glob('*.md')))} files")

    total_time = sum(timers.values())
    print(f"\n  Pipeline time: {total_time:.0f}s")
    for label, elapsed in timers.items():
        pct = elapsed / total_time * 100 if total_time > 0 else 0
        print(f"    {label:25s} {elapsed:8.1f}s  {pct:5.1f}%")

    comms = kg.detect_communities()
    print(f"\n  Communities: {len(comms)}")
    for c in comms[:5]:
        print(f"    C{c['id']}: {c['label'][:50]} ({c['size']} nodes)")


if __name__ == "__main__":
    asyncio.run(build_monthly_kb())
