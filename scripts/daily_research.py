#!/usr/bin/env python3
"""
Daily automated research pipeline.
Cron: 0 6 * * * python scripts/daily_research.py

Pipeline:
1. Load research topics from config
2. For each topic: web research -> document save -> entity extraction -> graph update -> vector update
3. Re-index previous outputs (feedback loop)
4. Generate knowledge report
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import importlib
import re
import sys
from pathlib import Path
from typing import Any
from typing import Optional

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Settings
from extraction import Deduplicator, EntityExtractor, RelationMapper
from feedback.output_indexer import OutputIndexer
from ingestion import DocumentParser, ResearchResult, WebResearcher
from scripts.knowledge_report import generate_report, print_report
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact


async def daily_pipeline(topics: Optional[list[str]] = None):
    settings = Settings.load()
    topic_list = topics if topics else settings.research.default_topics
    topic_list = [
        topic.strip()
        for topic in topic_list
        if isinstance(topic, str) and topic.strip()
    ]
    if not topic_list:
        raise ValueError(
            "No research topics available. Configure settings.yaml or pass topics via CLI."
        )

    from config.llm_client import create_llm_client, get_model_name

    llm_client = create_llm_client(api_key=settings.llm_api_key or "")
    model_name = get_model_name(
        api_key=settings.llm_api_key or "",
        default=settings.llm.extraction_model,
    )
    researcher = WebResearcher(
        llm_client=llm_client, max_sources=settings.research.max_sources
    )
    extractor = EntityExtractor(llm_client=llm_client, model=model_name)
    deduplicator = Deduplicator()
    relation_mapper = RelationMapper()
    graph_store = KnowledgeGraph(settings.storage.graph_path)
    vector_store = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    temporal_store = TemporalFactStore(settings.storage.temporal_path)
    output_indexer = OutputIndexer(
        graph_store=graph_store,
        vector_store=vector_store,
        temporal_store=temporal_store,
        entity_extractor=extractor,
    )
    parser = DocumentParser()

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Daily research start")
    print(f"Topics: {', '.join(topic_list)}")

    pipeline_stats: dict[str, int] = {
        "topics_processed": 0,
        "documents_saved": 0,
        "entities_added": 0,
        "relations_added": 0,
        "facts_added": 0,
        "feedback_docs_reindexed": 0,
    }

    for index, topic in enumerate(topic_list, start=1):
        print(f"\n[{index}/{len(topic_list)}] Researching: {topic}")
        existing_knowledge = graph_store.get_topic_summary(topic)
        result = await researcher.research(
            topic=topic,
            existing_knowledge=existing_knowledge,
            max_sources=settings.research.max_sources,
        )

        if not result.text.strip():
            print(f"  - No content retrieved for topic: {topic}")
            continue

        doc_path = save_research_document(result)
        extraction = await extractor.extract(result.text)
        inferred_relations = relation_mapper.infer_co_occurrence(
            extraction.get("entities", [])
        ) + relation_mapper.infer_hierarchical(extraction.get("entities", []))
        deduped = deduplicator.deduplicate(
            extraction.get("entities", []),
            extraction.get("relations", []) + inferred_relations,
        )

        graph_stats = graph_store.incremental_update(
            entities=deduped.get("entities", []),
            relations=deduped.get("relations", []),
            source_doc=doc_path,
            timestamp=result.timestamp,
        )

        vector_metadata = {
            "topic": result.topic,
            "source_count": len(result.sources),
            "timestamp": result.timestamp.isoformat(),
            "source_type": "daily_research",
        }
        await vector_store.upsert(doc_path, result.text, metadata=vector_metadata)

        facts_added = _index_temporal_entity_facts(
            temporal_store=temporal_store,
            entities=deduped.get("entities", []),
            source_doc=doc_path,
            valid_from=result.timestamp,
        )

        pipeline_stats["topics_processed"] += 1
        pipeline_stats["documents_saved"] += 1
        pipeline_stats["entities_added"] += int(graph_stats.get("nodes_added", 0))
        pipeline_stats["relations_added"] += int(graph_stats.get("edges_added", 0))
        pipeline_stats["facts_added"] += facts_added

        print(f"  - Saved document: {doc_path}")
        print(
            "  - Graph update: "
            f"+{graph_stats.get('nodes_added', 0)} entities, "
            f"+{graph_stats.get('edges_added', 0)} relations"
        )
        print(f"  - Temporal facts added: {facts_added}")

    reindexed_count = await _reindex_previous_outputs(
        documents_dir=Path("knowledge_base/documents"),
        parser=parser,
        output_indexer=output_indexer,
    )
    pipeline_stats["feedback_docs_reindexed"] = reindexed_count

    report = generate_report(graph_store, vector_store, temporal_store)
    print("\nDaily knowledge report")
    print_report(report)

    print("\nPipeline summary")
    print(f"  - topics_processed: {pipeline_stats['topics_processed']}")
    print(f"  - documents_saved: {pipeline_stats['documents_saved']}")
    print(f"  - entities_added: {pipeline_stats['entities_added']}")
    print(f"  - relations_added: {pipeline_stats['relations_added']}")
    print(f"  - facts_added: {pipeline_stats['facts_added']}")
    print(f"  - feedback_docs_reindexed: {pipeline_stats['feedback_docs_reindexed']}")


def save_research_document(result, output_dir: str = "knowledge_base/documents") -> str:
    if not isinstance(result, ResearchResult):
        raise TypeError(
            "result must be an ingestion.web_researcher.ResearchResult instance"
        )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = result.timestamp.astimezone(timezone.utc)
    slug = _slugify_topic(result.topic)
    file_name = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{slug}.md"
    file_path = out_dir / file_name

    frontmatter = {
        "title": result.topic,
        "topic": result.topic,
        "generated_at": timestamp.isoformat(),
        "source_type": "daily_research",
        "source_count": len(result.sources),
        "sources": [
            {
                "title": source.get("title", ""),
                "url": source.get("url", ""),
                "snippet": source.get("snippet", ""),
            }
            for source in result.sources
        ],
    }

    source_lines = []
    for index, source in enumerate(result.sources, start=1):
        title = source.get("title", "(untitled)").strip() or "(untitled)"
        url = source.get("url", "").strip()
        snippet = source.get("snippet", "").strip()
        line = f"{index}. {title}"
        if url:
            line += f" - {url}"
        if snippet:
            line += f"\n   - {snippet}"
        source_lines.append(line)

    body = "\n".join(
        [
            "---",
            yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip(),
            "---",
            "",
            f"# {result.topic}",
            "",
            f"생성 시각(UTC): {timestamp.isoformat()}",
            "",
            "## Research Content",
            "",
            result.text.strip(),
            "",
            "## Sources",
            "",
            "\n".join(source_lines) if source_lines else "- No sources collected",
            "",
        ]
    )

    file_path.write_text(body, encoding="utf-8")
    return str(file_path)


async def _reindex_previous_outputs(
    documents_dir: Path,
    parser: DocumentParser,
    output_indexer: OutputIndexer,
) -> int:
    if not documents_dir.exists():
        return 0

    today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    candidates = sorted(documents_dir.glob("*.md"))
    reindexed = 0

    for path in candidates:
        if path.name.startswith(today_prefix):
            continue

        frontmatter = _read_frontmatter(path)
        if frontmatter.get("source_type") != "daily_research":
            continue

        parsed = parser.parse_markdown(str(path))
        if not parsed.content.strip():
            continue

        references = [str(path)]
        for src in frontmatter.get("sources", []):
            if isinstance(src, dict):
                title = src.get("title", "")
                if title:
                    references.append(title)

        await output_indexer.index_output(
            output_text=parsed.content,
            metadata={
                "timestamp": frontmatter.get(
                    "generated_at", datetime.now(tz=timezone.utc).isoformat()
                ),
                "referenced_docs": references,
                "origin_doc": str(path),
            },
        )
        reindexed += 1

    return reindexed


def _index_temporal_entity_facts(
    temporal_store: TemporalFactStore,
    entities: list[dict[str, Any]],
    source_doc: str,
    valid_from: datetime,
) -> int:
    added = 0
    seen: set[tuple[str, str, str]] = set()
    for entity in entities:
        name = str(entity.get("name", "")).strip()
        entity_type = str(entity.get("type", "")).strip()
        if not name or not entity_type:
            continue

        dedupe_key = (name.lower(), "entity_type", entity_type.upper())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        temporal_store.add_fact(
            TemporalFact(
                entity=name,
                attribute="entity_type",
                value=entity_type.upper(),
                source_doc=source_doc,
                valid_from=valid_from,
                confidence=1.0,
            )
        )
        added += 1
    return added


def _read_frontmatter(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\n(.*?)\n---\n", content, flags=re.DOTALL)
    if not match:
        return {}

    try:
        payload = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}

    return payload if isinstance(payload, dict) else {}


def _slugify_topic(topic: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", topic.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "research"


if __name__ == "__main__":
    topics = sys.argv[1:] if len(sys.argv) > 1 else None
    asyncio.run(daily_pipeline(topics))
