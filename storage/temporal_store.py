from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import cast
from uuid import uuid4


@dataclass
class TemporalFact:
    entity: str
    attribute: str
    value: str
    source_doc: str
    valid_from: datetime
    valid_until: datetime | None = None
    confidence: float = 1.0
    fact_id: str = field(default_factory=lambda: str(uuid4()))


class TemporalFactStore:
    store_path: str
    _lock: threading.RLock
    facts: list[TemporalFact]

    def __init__(self, store_path: str = "knowledge_base/temporal/facts.jsonl"):
        self.store_path = store_path
        self._lock = threading.RLock()
        self.facts = self._load()

    def _load(self) -> list[TemporalFact]:
        if not os.path.exists(self.store_path):
            return []

        facts_by_id: dict[str, TemporalFact] = {}
        fact_order: list[str] = []
        with self._lock:
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            payload = cast(dict[str, object], json.loads(line))
                        except json.JSONDecodeError:
                            import logging

                            logging.getLogger(__name__).warning(
                                "Skipping malformed line %d in %s",
                                line_num,
                                self.store_path,
                            )
                            continue
                        action = payload.get("_action")
                        try:
                            fact = self._dict_to_fact(payload)
                        except (KeyError, ValueError, TypeError):
                            continue
                        if action == "update":
                            if fact.fact_id not in facts_by_id:
                                fact_order.append(fact.fact_id)
                            facts_by_id[fact.fact_id] = fact
                            continue
                        if fact.fact_id not in facts_by_id:
                            fact_order.append(fact.fact_id)
                        facts_by_id[fact.fact_id] = fact
            except OSError:
                return []
        facts = [facts_by_id[fact_id] for fact_id in fact_order]
        return facts

    def _save(self):
        store_dir = os.path.dirname(self.store_path)
        if store_dir:
            os.makedirs(store_dir, exist_ok=True)

        with self._lock:
            with open(self.store_path, "w", encoding="utf-8") as f:
                for fact in self.facts:
                    _ = f.write(
                        json.dumps(self._fact_to_dict(fact), ensure_ascii=False)
                    )
                    _ = f.write("\n")

    def _append_line(self, fact: TemporalFact):
        store_dir = os.path.dirname(self.store_path)
        if store_dir:
            os.makedirs(store_dir, exist_ok=True)

        with self._lock:
            with open(self.store_path, "a", encoding="utf-8") as f:
                _ = f.write(json.dumps(self._fact_to_dict(fact), ensure_ascii=False))
                _ = f.write("\n")

    def _append_update(self, fact: TemporalFact):
        store_dir = os.path.dirname(self.store_path)
        if store_dir:
            os.makedirs(store_dir, exist_ok=True)

        with self._lock:
            with open(self.store_path, "a", encoding="utf-8") as f:
                payload = self._fact_to_dict(fact)
                payload["_action"] = "update"
                payload["fact_id"] = fact.fact_id
                _ = f.write(json.dumps(payload, ensure_ascii=False))
                _ = f.write("\n")

    def add_fact(self, fact: TemporalFact):
        with self._lock:
            for existing in self.facts:
                if (
                    existing.entity == fact.entity
                    and existing.attribute == fact.attribute
                    and existing.valid_until is None
                ):
                    existing.valid_until = fact.valid_from
                    self._append_update(existing)

            self.facts.append(fact)
            self.facts.sort(key=lambda item: item.valid_from)
            self._append_line(fact)

    def compact(self):
        with self._lock:
            self._save()

    def query_current(
        self, entity: str, attribute: str | None = None
    ) -> list[TemporalFact]:
        return [
            fact
            for fact in self.facts
            if fact.entity == entity
            and fact.valid_until is None
            and (attribute is None or fact.attribute == attribute)
        ]

    def query_at_time(self, entity: str, at: datetime) -> list[TemporalFact]:
        return [
            fact
            for fact in self.facts
            if fact.entity == entity
            and fact.valid_from <= at
            and (fact.valid_until is None or at < fact.valid_until)
        ]

    def get_entity_history(self, entity: str) -> list[TemporalFact]:
        history = [fact for fact in self.facts if fact.entity == entity]
        history.sort(key=lambda item: item.valid_from)
        return history

    def get_stats(self) -> dict[str, int]:
        unique_entities = {fact.entity for fact in self.facts}
        current_facts = [fact for fact in self.facts if fact.valid_until is None]
        return {
            "total_facts": len(self.facts),
            "current_facts": len(current_facts),
            "entities": len(unique_entities),
        }

    @staticmethod
    def _fact_to_dict(fact: TemporalFact) -> dict[str, object]:
        payload = asdict(fact)
        payload["valid_from"] = fact.valid_from.isoformat()
        payload["valid_until"] = (
            fact.valid_until.isoformat() if fact.valid_until is not None else None
        )
        return payload

    @staticmethod
    def _dict_to_fact(payload: dict[str, object]) -> TemporalFact:
        valid_from = datetime.fromisoformat(str(payload["valid_from"]))
        valid_until_raw = payload.get("valid_until")
        valid_until = (
            datetime.fromisoformat(str(valid_until_raw)) if valid_until_raw else None
        )
        fact_id_raw = payload.get("fact_id")
        confidence_raw = payload.get("confidence", 1.0)
        return TemporalFact(
            entity=str(payload["entity"]),
            attribute=str(payload["attribute"]),
            value=str(payload["value"]),
            source_doc=str(payload["source_doc"]),
            valid_from=valid_from,
            valid_until=valid_until,
            confidence=float(str(confidence_raw)),
            fact_id=str(fact_id_raw) if fact_id_raw else str(uuid4()),
        )
