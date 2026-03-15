from __future__ import annotations

import json
import os
import tempfile
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

import networkx as nx


class KnowledgeGraph:
    def __init__(self, graph_path: str = "knowledge_base/graph/kg.json"):
        self.graph_path = graph_path
        self._lock = threading.RLock()
        self.graph = self._load_or_create()

    def _load_or_create(self) -> nx.DiGraph:
        if not os.path.exists(self.graph_path):
            return nx.DiGraph()

        try:
            with self._lock:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return nx.node_link_graph(data, directed=True, edges="edges")
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to load graph from %s: %s — starting fresh",
                self.graph_path,
                exc,
            )
            return nx.DiGraph()

    def _save(self):
        graph_dir = os.path.dirname(self.graph_path)
        if graph_dir:
            os.makedirs(graph_dir, exist_ok=True)

        payload = nx.node_link_data(self.graph, edges="edges")
        with self._lock:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=graph_dir or ".",
                delete=False,
            ) as tmp_file:
                json.dump(payload, tmp_file, ensure_ascii=False, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_path = tmp_file.name
            os.replace(temp_path, self.graph_path)

    def incremental_update(
        self,
        entities: list,
        relations: list,
        source_doc: str,
        timestamp: datetime | None = None,
    ) -> dict:
        now = (timestamp or datetime.now(tz=timezone.utc)).isoformat()
        stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "nodes_updated": 0,
            "edges_updated": 0,
        }

        with self._lock:
            for entity in entities:
                parsed = self._normalize_entity(entity)
                if not parsed:
                    continue

                name = parsed["name"]
                node_type = parsed.get("type", "unknown")
                description_text = parsed.get("description")

                if not self.graph.has_node(name):
                    descriptions = []
                    if description_text:
                        descriptions.append(
                            {
                                "text": description_text,
                                "source": source_doc,
                                "timestamp": now,
                            }
                        )
                    self.graph.add_node(
                        name,
                        type=node_type,
                        descriptions=descriptions,
                        created_at=now,
                        last_updated=now,
                    )
                    stats["nodes_added"] += 1
                    continue

                node_data = self.graph.nodes[name]
                node_data.setdefault("descriptions", [])
                if description_text:
                    node_data["descriptions"].append(
                        {
                            "text": description_text,
                            "source": source_doc,
                            "timestamp": now,
                        }
                    )
                    if len(node_data["descriptions"]) > 5:
                        node_data["descriptions"] = node_data["descriptions"][-5:]
                node_data["type"] = node_data.get("type") or node_type
                node_data["last_updated"] = now
                stats["nodes_updated"] += 1

            for relation in relations:
                parsed = self._normalize_relation(relation)
                if not parsed:
                    continue

                source = parsed["source"]
                target = parsed["target"]
                if self._is_junk_entity(source) or self._is_junk_entity(target):
                    continue
                relation_name = parsed.get("relation", "related_to")
                description = parsed.get("description", "")
                weight = float(parsed.get("weight", 1.0))

                if not self.graph.has_node(source):
                    self.graph.add_node(
                        source,
                        type="unknown",
                        descriptions=[],
                        created_at=now,
                        last_updated=now,
                    )
                    stats["nodes_added"] += 1
                if not self.graph.has_node(target):
                    self.graph.add_node(
                        target,
                        type="unknown",
                        descriptions=[],
                        created_at=now,
                        last_updated=now,
                    )
                    stats["nodes_added"] += 1

                if not self.graph.has_edge(source, target):
                    self.graph.add_edge(
                        source,
                        target,
                        relation=relation_name,
                        description=description,
                        weight=weight,
                        sources=[source_doc],
                        created_at=now,
                    )
                    stats["edges_added"] += 1
                    continue

                edge_data = self.graph[source][target]
                edge_data["weight"] = max(float(edge_data.get("weight", 0.0)), weight)
                edge_data.setdefault("sources", [])
                if source_doc not in edge_data["sources"]:
                    edge_data["sources"].append(source_doc)
                if relation_name:
                    edge_data["relation"] = relation_name
                if description:
                    existing_desc = edge_data.get("description", "")
                    if description not in existing_desc:
                        edge_data["description"] = (
                            f"{existing_desc} | {description}".strip(" |")
                            if existing_desc
                            else description
                        )
                stats["edges_updated"] += 1

            self._save()

        return stats

    def add_meta_relation(self, source: str, target: str, relation: str):
        now = datetime.now(tz=timezone.utc).isoformat()
        with self._lock:
            if not self.graph.has_node(source):
                self.graph.add_node(
                    source,
                    type="unknown",
                    descriptions=[],
                    created_at=now,
                    last_updated=now,
                )
            if not self.graph.has_node(target):
                self.graph.add_node(
                    target,
                    type="unknown",
                    descriptions=[],
                    created_at=now,
                    last_updated=now,
                )

            if self.graph.has_edge(source, target):
                self.graph[source][target]["relation"] = relation
            else:
                self.graph.add_edge(
                    source,
                    target,
                    relation=relation,
                    description="",
                    weight=1.0,
                    sources=[],
                    created_at=now,
                )
            self._save()

    def get_neighbors(self, entity: str, hops: int = 1) -> list[dict]:
        if entity not in self.graph:
            return []

        queue = deque([(entity, 0)])
        visited = {entity}
        results = []
        seen_edges = set()

        while queue:
            current, depth = queue.popleft()
            if depth >= hops:
                continue

            for neighbor in set(self.graph.successors(current)).union(
                set(self.graph.predecessors(current))
            ):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

                if self.graph.has_edge(current, neighbor):
                    edge_key = (current, neighbor)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edge_data = dict(self.graph[current][neighbor])
                        results.append(
                            {
                                "source": current,
                                "target": neighbor,
                                "hops": depth + 1,
                                **edge_data,
                            }
                        )
                if self.graph.has_edge(neighbor, current):
                    edge_key = (neighbor, current)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edge_data = dict(self.graph[neighbor][current])
                        results.append(
                            {
                                "source": neighbor,
                                "target": current,
                                "hops": depth + 1,
                                **edge_data,
                            }
                        )

        return results

    def get_topic_summary(self, topic: str) -> str:
        topic_lower = topic.lower()
        snippets = []

        for node, data in self.graph.nodes(data=True):
            descriptions = data.get("descriptions", [])
            matched = topic_lower in str(node).lower() or any(
                topic_lower in str(item.get("text", "")).lower()
                for item in descriptions
            )
            if not matched:
                continue

            node_descs = [
                item.get("text", "").strip()
                for item in descriptions
                if item.get("text")
            ]
            if node_descs:
                snippets.append(f"{node}: {' | '.join(node_descs[-3:])}")
            else:
                snippets.append(f"{node}: (no descriptions)")

        if not snippets:
            return f"No topic matches found for '{topic}'."

        return "\n".join(snippets)

    def get_stats(self) -> dict:
        last_updated = None
        for _, data in self.graph.nodes(data=True):
            candidate = data.get("last_updated")
            if not candidate:
                continue
            if last_updated is None or candidate > last_updated:
                last_updated = candidate

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "last_updated": last_updated,
        }

    def search_entities(self, query: str) -> list[dict]:
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        matches = []
        for node, data in self.graph.nodes(data=True):
            node_text = str(node)
            descriptions = data.get("descriptions", [])
            desc_texts = [str(item.get("text", "")) for item in descriptions]

            node_lower = node_text.lower()
            in_name = query_lower in node_lower or node_lower in query_lower
            in_desc = any(query_lower in text.lower() for text in desc_texts)
            if not (in_name or in_desc):
                continue

            score = 2 if in_name else 1
            if in_name and in_desc:
                score = 3
            if query_lower == node_lower:
                score = 4

            matches.append(
                {
                    "entity": node_text,
                    "type": data.get("type", "unknown"),
                    "score": score,
                    "description_count": len(descriptions),
                    "last_updated": data.get("last_updated"),
                }
            )

        matches.sort(key=lambda item: (-item["score"], item["entity"]))
        return matches

    @staticmethod
    def _normalize_entity(entity: Any) -> dict[str, Any] | None:
        if isinstance(entity, str):
            clean_name = entity.strip()
            if not clean_name or KnowledgeGraph._is_junk_entity(clean_name):
                return None
            return {"name": clean_name}

        if isinstance(entity, dict):
            name = (
                entity.get("name")
                or entity.get("id")
                or entity.get("entity")
                or entity.get("label")
            )
            if not name:
                return None
            clean_name = str(name).strip()
            if KnowledgeGraph._is_junk_entity(clean_name):
                return None
            return {
                "name": clean_name,
                "type": entity.get("type", "unknown"),
                "description": (
                    entity.get("description")
                    or entity.get("summary")
                    or entity.get("text")
                    or ""
                ),
            }

        return None

    @staticmethod
    def _is_junk_entity(name: str) -> bool:
        if name.startswith(("http://", "https://", "ftp://", "www.")):
            return True
        if len(name) > 120:
            return True
        if len(name) < 2:
            return True
        return False

    @staticmethod
    def _normalize_relation(relation: Any) -> dict[str, Any] | None:
        if not isinstance(relation, dict):
            return None

        source = relation.get("source") or relation.get("from")
        target = relation.get("target") or relation.get("to")
        if not source or not target:
            return None

        return {
            "source": str(source).strip(),
            "target": str(target).strip(),
            "relation": relation.get("relation")
            or relation.get("type")
            or "related_to",
            "description": relation.get("description") or relation.get("text") or "",
            "weight": relation.get("weight", 1.0),
        }
