from itertools import combinations
from typing import Any


class RelationMapper:
    def infer_co_occurrence(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        grouped: dict[int, list[dict[str, Any]]] = {}
        for entity in entities:
            chunk_index = entity.get("chunk_index")
            if not isinstance(chunk_index, int):
                chunk_index = 0
            grouped.setdefault(chunk_index, []).append(entity)

        relations: list[dict[str, Any]] = []
        seen_pairs: set[tuple[int, str, str]] = set()

        max_per_chunk = 15

        for chunk_index, group in grouped.items():
            chunk_count = 0
            for left, right in combinations(group, 2):
                if chunk_count >= max_per_chunk:
                    break

                source = str(left.get("name", "")).strip()
                target = str(right.get("name", "")).strip()
                if not source or not target or source == target:
                    continue

                pair_key = (chunk_index, source.lower(), target.lower())
                reverse_key = (chunk_index, target.lower(), source.lower())
                if pair_key in seen_pairs or reverse_key in seen_pairs:
                    continue

                seen_pairs.add(pair_key)
                relations.append(
                    {
                        "source": source,
                        "target": target,
                        "relation": "CO_OCCURS_WITH",
                        "description": f"{source} and {target} co-occur in the same text chunk.",
                        "weight": 0.5,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_count += 1

        return relations

    def infer_hierarchical(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        relations: list[dict[str, Any]] = []
        protocol_entities = [
            e for e in entities if str(e.get("type", "")).upper() == "PROTOCOL"
        ]
        token_like_entities = [e for e in entities if self._is_token_like(e)]

        for protocol in protocol_entities:
            protocol_name = str(protocol.get("name", "")).strip()
            if not protocol_name:
                continue

            for token in token_like_entities:
                token_name = str(token.get("name", "")).strip()
                if not token_name or token_name == protocol_name:
                    continue

                protocol_name_lower = protocol_name.lower()
                token_name_lower = token_name.lower()
                token_desc_lower = str(token.get("description", "")).lower()
                same_chunk = token.get("chunk_index") == protocol.get("chunk_index")
                mentions_protocol = (
                    protocol_name_lower in token_desc_lower
                    or protocol_name_lower in token_name_lower
                )

                if same_chunk and mentions_protocol:
                    relations.append(
                        {
                            "source": token_name,
                            "target": protocol_name,
                            "relation": "PART_OF",
                            "description": f"{token_name} appears to be part of the {protocol_name} protocol ecosystem.",
                            "weight": 0.65,
                            "chunk_index": token.get("chunk_index"),
                        }
                    )

        return relations

    def _is_token_like(self, entity: dict[str, Any]) -> bool:
        name_lower = str(entity.get("name", "")).lower()
        description_lower = str(entity.get("description", "")).lower()
        entity_type = str(entity.get("type", "")).upper()

        token_keywords = ("token", "coin", "asset")
        if any(keyword in name_lower for keyword in token_keywords):
            return True
        if any(keyword in description_lower for keyword in token_keywords):
            return True

        return entity_type in {"CONCEPT", "TECHNOLOGY"} and len(name_lower) <= 6
