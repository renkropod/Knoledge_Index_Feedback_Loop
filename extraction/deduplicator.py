from typing import Any


class Deduplicator:
    def __init__(self, alias_map: dict[str, str] | None = None) -> None:
        default_aliases = {
            "eth": "Ethereum",
            "ethereum": "Ethereum",
            "btc": "Bitcoin",
            "bitcoin": "Bitcoin",
            "sol": "Solana",
            "solana": "Solana",
        }
        provided_aliases = alias_map or {}
        self.alias_map = {
            key.lower().strip(): value.strip()
            for key, value in {**default_aliases, **provided_aliases}.items()
        }

    def deduplicate(
        self, entities: list[dict[str, Any]], relations: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        canonical_index: dict[str, dict[str, Any]] = {}
        alias_to_canonical: dict[str, str] = {}

        for entity in entities:
            raw_name = str(entity.get("name", "")).strip()
            if not raw_name:
                continue

            canonical_name = self._canonical_name(raw_name)
            canonical_key = canonical_name.lower()

            existing = canonical_index.get(canonical_key)
            if existing is None:
                merged = dict(entity)
                merged["name"] = canonical_name
                canonical_index[canonical_key] = merged
            else:
                canonical_index[canonical_key] = self._merge_entity(
                    existing, entity, canonical_name
                )

            alias_to_canonical[raw_name.lower()] = canonical_name
            alias_to_canonical[canonical_key] = canonical_name

        updated_relations = [
            self._normalize_relation(relation, alias_to_canonical)
            for relation in relations
        ]
        deduped_relations = self._dedupe_relations(updated_relations)

        return {
            "entities": list(canonical_index.values()),
            "relations": deduped_relations,
        }

    def _canonical_name(self, name: str) -> str:
        normalized = name.strip()
        if not normalized:
            return normalized

        alias_match = self.alias_map.get(normalized.lower())
        if alias_match:
            return alias_match

        if normalized.isupper() and len(normalized) <= 5:
            alias_match = self.alias_map.get(normalized.lower())
            if alias_match:
                return alias_match

        return normalized

    def _merge_entity(
        self, base: dict[str, Any], incoming: dict[str, Any], canonical_name: str
    ) -> dict[str, Any]:
        merged = dict(base)
        merged["name"] = canonical_name

        base_type = str(base.get("type", "")).strip()
        incoming_type = str(incoming.get("type", "")).strip()
        if not base_type and incoming_type:
            merged["type"] = incoming_type

        base_desc = str(base.get("description", "")).strip()
        incoming_desc = str(incoming.get("description", "")).strip()
        merged["description"] = self._merge_description(base_desc, incoming_desc)

        if "chunk_index" not in merged and "chunk_index" in incoming:
            merged["chunk_index"] = incoming["chunk_index"]

        return merged

    def _merge_description(self, left: str, right: str) -> str:
        if not left:
            return right
        if not right:
            return left
        if left in right:
            return right
        if right in left:
            return left
        if len(right) > len(left):
            return f"{right} | {left}"
        return f"{left} | {right}"

    def _normalize_relation(
        self, relation: dict[str, Any], alias_to_canonical: dict[str, str]
    ) -> dict[str, Any]:
        normalized = dict(relation)

        source = str(relation.get("source", "")).strip()
        target = str(relation.get("target", "")).strip()
        normalized["source"] = self._resolve_alias(source, alias_to_canonical)
        normalized["target"] = self._resolve_alias(target, alias_to_canonical)

        raw_weight = relation.get("weight", 0.5)
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            weight = 0.5
        normalized["weight"] = max(0.0, min(1.0, weight))

        return normalized

    def _resolve_alias(self, name: str, alias_to_canonical: dict[str, str]) -> str:
        if not name:
            return name

        alias_match = alias_to_canonical.get(name.lower())
        if alias_match:
            return alias_match

        return self._canonical_name(name)

    def _dedupe_relations(
        self, relations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        deduped: dict[tuple[str, str, str], dict[str, Any]] = {}

        for relation in relations:
            source = str(relation.get("source", "")).strip()
            target = str(relation.get("target", "")).strip()
            relation_type = str(relation.get("relation", "")).strip().upper()

            if not source or not target or not relation_type:
                continue

            key = (source.lower(), target.lower(), relation_type)
            existing = deduped.get(key)
            if existing is None:
                relation["relation"] = relation_type
                deduped[key] = relation
                continue

            if float(relation.get("weight", 0.0)) > float(existing.get("weight", 0.0)):
                deduped[key] = relation

        return list(deduped.values())
