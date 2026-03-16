#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from json import dumps
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict, cast

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Settings
from storage.graph_store import KnowledgeGraph
from storage.temporal_store import TemporalFactStore

hf_home = os.environ.get("HF_HOME", "")
if not hf_home:
    cache_dir = Path(__file__).resolve().parent.parent / ".cache" / "hf"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)

from storage.vector_store import VectorStore


DOC_TIMESTAMP_RE = re.compile(r"^(\d{8})_(\d{6})")


@dataclass
class DocumentInfo:
    file_name: str
    file_path: str
    timestamp: datetime | None
    date_key: str


class CurrentStats(TypedDict):
    entities: int
    relations: int
    vectors: int
    facts: int


class EntityTypeRow(TypedDict):
    type: str
    count: int
    percentage: int


class GrowthRow(TypedDict):
    date: str
    documents: int


class TopConnectedRow(TypedDict):
    entity: str
    degree: int


class TemporalSummary(TypedDict):
    total: int
    current: int
    invalidated: int


class RecentDocumentRow(TypedDict):
    timestamp: str
    file: str
    path: str


class MetaRow(TypedDict):
    graph_path: str
    vector_path: str
    temporal_path: str
    documents_dir: str


class CommunityRow(TypedDict):
    id: int
    size: int
    label: str
    dominant_type: str
    top_entities: list[str]


class DashboardData(TypedDict):
    current_stats: CurrentStats
    entity_type_distribution: list[EntityTypeRow]
    growth_timeline: list[GrowthRow]
    top_connected_entities: list[TopConnectedRow]
    temporal_facts_summary: TemporalSummary
    recent_documents: list[RecentDocumentRow]
    communities: list[CommunityRow]
    meta: MetaRow


def _to_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _load_documents(documents_dir: Path) -> list[DocumentInfo]:
    docs: list[DocumentInfo] = []
    for path in documents_dir.glob("*.md"):
        match = DOC_TIMESTAMP_RE.match(path.name)
        parsed_ts: datetime | None = None
        date_key = "unknown"
        if match:
            raw_ts = f"{match.group(1)}_{match.group(2)}"
            try:
                parsed_ts = datetime.strptime(raw_ts, "%Y%m%d_%H%M%S")
                date_key = parsed_ts.strftime("%Y-%m-%d")
            except ValueError:
                parsed_ts = None
                date_key = "unknown"

        docs.append(
            DocumentInfo(
                file_name=path.name,
                file_path=str(path),
                timestamp=parsed_ts,
                date_key=date_key,
            )
        )

    docs.sort(
        key=lambda item: (
            item.timestamp is None,
            item.timestamp or datetime.min,
            item.file_name,
        )
    )
    return docs


def _build_bar(value: int, max_value: int, width: int = 24) -> str:
    if max_value <= 0:
        return ""
    bar_len = max(1, round((value / max_value) * width)) if value > 0 else 0
    return "#" * bar_len


def _format_label(raw: str) -> str:
    clean = raw.strip()
    if not clean:
        return "Unknown"
    if clean.isupper() and len(clean) <= 5:
        return clean
    return clean.title()


def _load_graph_snapshot(
    graph_path: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    graph_file = Path(graph_path)
    if not graph_file.exists():
        return [], []

    try:
        payload_raw = cast(
            dict[str, object], json.loads(graph_file.read_text(encoding="utf-8"))
        )
    except (OSError, json.JSONDecodeError):
        return [], []

    nodes_raw = payload_raw.get("nodes", [])
    edges_raw = payload_raw.get("edges", [])

    nodes: list[dict[str, object]] = []
    if isinstance(nodes_raw, list):
        node_items = cast(list[object], nodes_raw)
        for row in node_items:
            if isinstance(row, dict):
                nodes.append(cast(dict[str, object], row))

    edges: list[dict[str, object]] = []
    if isinstance(edges_raw, list):
        edge_items = cast(list[object], edges_raw)
        for row in edge_items:
            if isinstance(row, dict):
                edges.append(cast(dict[str, object], row))

    return nodes, edges


def _build_community_data(graph_store: KnowledgeGraph) -> list[CommunityRow]:
    try:
        communities = graph_store.detect_communities()
    except Exception:
        return []
    result = []
    for comm in communities[:20]:
        result.append(
            {
                "id": comm["id"],
                "size": comm["size"],
                "label": comm["label"],
                "dominant_type": comm["dominant_type"],
                "top_entities": comm["top_entities"],
            }
        )
    return result


def build_dashboard_data() -> DashboardData:
    settings = Settings.load()
    project_root = Path(__file__).resolve().parent.parent

    graph_store = KnowledgeGraph(settings.storage.graph_path)
    temporal_store = TemporalFactStore(settings.storage.temporal_path)
    vector_store = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )

    graph_nodes_data, graph_edges_data = _load_graph_snapshot(graph_store.graph_path)
    vector_stats_raw = vector_store.get_stats()
    temporal_stats_raw = temporal_store.get_stats()

    graph_nodes = len(graph_nodes_data)
    graph_edges = len(graph_edges_data)
    vector_docs = _to_int(vector_stats_raw.get("total_documents"))
    total_facts = _to_int(temporal_stats_raw.get("total_facts"))
    current_facts = _to_int(temporal_stats_raw.get("current_facts"))
    invalidated_facts = max(total_facts - current_facts, 0)

    type_counter: Counter[str] = Counter()
    for node_data in graph_nodes_data:
        node_type = str(node_data.get("type", "unknown"))
        type_counter[node_type] += 1
    sorted_type_items = sorted(
        type_counter.items(), key=lambda item: (-item[1], item[0])
    )

    documents_dir = project_root / "knowledge_base" / "documents"
    documents = _load_documents(documents_dir)
    growth_counter: Counter[str] = Counter(doc.date_key for doc in documents)
    growth_items = sorted(growth_counter.items(), key=lambda item: item[0])

    degree_counter: Counter[str] = Counter()
    for node_data in graph_nodes_data:
        node_id = str(node_data.get("id", "")).strip()
        if node_id:
            degree_counter[node_id] += 0

    for edge_data in graph_edges_data:
        source = str(edge_data.get("source", "")).strip()
        target = str(edge_data.get("target", "")).strip()
        if source:
            degree_counter[source] += 1
        if target:
            degree_counter[target] += 1

    degree_items: list[TopConnectedRow] = []
    for entity, degree in degree_counter.items():
        degree_items.append({"entity": entity, "degree": degree})
    degree_items.sort(key=lambda item: (-item["degree"], item["entity"]))

    recent_documents = [doc for doc in documents if doc.timestamp is not None][-10:]
    recent_documents.reverse()

    return {
        "current_stats": {
            "entities": graph_nodes,
            "relations": graph_edges,
            "vectors": vector_docs,
            "facts": total_facts,
        },
        "entity_type_distribution": [
            {
                "type": _format_label(node_type),
                "count": count,
                "percentage": round((count / max(graph_nodes, 1)) * 100),
            }
            for node_type, count in sorted_type_items
        ],
        "growth_timeline": [
            {"date": date_key, "documents": count}
            for date_key, count in growth_items
            if date_key != "unknown"
        ],
        "top_connected_entities": degree_items[:10],
        "temporal_facts_summary": {
            "total": total_facts,
            "current": current_facts,
            "invalidated": invalidated_facts,
        },
        "recent_documents": [
            {
                "timestamp": doc.timestamp.strftime("%Y-%m-%d %H:%M")
                if doc.timestamp
                else "",
                "file": DOC_TIMESTAMP_RE.sub("", doc.file_name, count=1).lstrip("_"),
                "path": doc.file_path,
            }
            for doc in recent_documents
        ],
        "communities": _build_community_data(graph_store),
        "meta": {
            "graph_path": settings.storage.graph_path,
            "vector_path": settings.storage.vector_path,
            "temporal_path": settings.storage.temporal_path,
            "documents_dir": str(documents_dir),
        },
    }


def render_ascii(data: DashboardData) -> str:
    lines: list[str] = []
    stats = data["current_stats"]

    lines.append("KNOWLEDGE BASE DASHBOARD")
    lines.append("========================")
    lines.append(
        "Entities: {entities} | Relations: {relations} | Vectors: {vectors} | Facts: {facts}".format(
            **stats
        )
    )
    lines.append("")

    lines.append("Entity Types:")
    type_rows = data["entity_type_distribution"]
    max_type_count = max((row["count"] for row in type_rows), default=0)
    for row in type_rows:
        label = row["type"][:14]
        bar = _build_bar(row["count"], max_type_count, width=20)
        lines.append(f"  {label:<14}  {bar:<20} {row['count']} ({row['percentage']}%)")
    if not type_rows:
        lines.append("  (no entity types)")
    lines.append("")

    lines.append("Growth (docs per day):")
    growth_rows = data["growth_timeline"]
    max_growth = max((row["documents"] for row in growth_rows), default=0)
    for row in growth_rows:
        bar = _build_bar(row["documents"], max_growth, width=24)
        lines.append(f"  {row['date']}  {bar:<24} {row['documents']}")
    if not growth_rows:
        lines.append("  (no timestamped documents)")
    lines.append("")

    lines.append("Top 10 Connected:")
    top_rows = data["top_connected_entities"]
    for index, row in enumerate(top_rows, start=1):
        entity = row["entity"][:18]
        lines.append(f"  {index:>2}. {entity:<18} (degree: {row['degree']})")
    if not top_rows:
        lines.append("  (no connected entities)")
    lines.append("")

    communities = data.get("communities", [])
    if communities:
        lines.append(f"Communities ({len(communities)}):")
        max_size = max((c["size"] for c in communities), default=1)
        for comm in communities[:10]:
            bar = _build_bar(comm["size"], max_size, width=16)
            top = ", ".join(comm["top_entities"][:3])
            lines.append(
                f"  C{comm['id']:>2} [{comm['dominant_type'][:10]:10s}] {bar} {comm['size']:>3} nodes  {top}"
            )
        lines.append("")

    temporal = data["temporal_facts_summary"]
    lines.append(
        f"Temporal Facts: {temporal['total']} total, {temporal['current']} current, {temporal['invalidated']} invalidated"
    )
    lines.append("")

    lines.append("Recent Documents:")
    recent_docs = data["recent_documents"]
    for row in recent_docs:
        lines.append(f"  {row['timestamp']}  {row['file']}")
    if not recent_docs:
        lines.append("  (no documents found)")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show knowledge base growth and connectivity dashboard"
    )
    _ = parser.add_argument(
        "--json",
        action="store_true",
        help="Output dashboard data as JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = build_dashboard_data()
    json_output = bool(getattr(args, "json", False))

    if json_output:
        print(dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(render_ascii(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
