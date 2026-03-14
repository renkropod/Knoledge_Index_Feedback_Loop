from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .llm_generator import GenerationResult


@dataclass
class ProvenanceRecord:
    output_id: str
    query: str
    referenced_docs: list[str]
    generated_text: str
    model: str
    timestamp: datetime
    confidence: float


class ProvenanceTracker:
    def __init__(self, store_path: str = "knowledge_base/provenance/records.jsonl"):
        self.store_path = store_path
        self._lock = threading.RLock()
        self.records = self._load()

    def record(self, result: GenerationResult, query: str) -> ProvenanceRecord:
        timestamp = result.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        provenance = ProvenanceRecord(
            output_id=str(uuid4()),
            query=query,
            referenced_docs=list(result.referenced_docs),
            generated_text=result.text,
            model=result.model,
            timestamp=timestamp,
            confidence=self._calculate_confidence(
                referenced_docs=result.referenced_docs,
                timestamp=timestamp,
            ),
        )

        with self._lock:
            self.records.append(provenance)
            self._save()
        return provenance

    def get_records_for_doc(self, doc_id: str) -> list[ProvenanceRecord]:
        target = doc_id.strip()
        if not target:
            return []
        return [
            record for record in self.records if target in set(record.referenced_docs)
        ]

    def get_recent_records(self, limit: int = 20) -> list[ProvenanceRecord]:
        bounded_limit = max(0, int(limit))
        ordered = sorted(self.records, key=lambda item: item.timestamp, reverse=True)
        return ordered[:bounded_limit]

    def _load(self) -> list[ProvenanceRecord]:
        if not os.path.exists(self.store_path):
            return []

        records: list[ProvenanceRecord] = []
        with self._lock:
            with open(self.store_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    records.append(self._dict_to_record(payload))
        return records

    def _save(self):
        store_dir = os.path.dirname(self.store_path)
        if store_dir:
            os.makedirs(store_dir, exist_ok=True)

        with self._lock:
            with open(self.store_path, "w", encoding="utf-8") as f:
                for record in self.records:
                    f.write(
                        json.dumps(self._record_to_dict(record), ensure_ascii=False)
                    )
                    f.write("\n")

    @staticmethod
    def _calculate_confidence(referenced_docs: list[str], timestamp: datetime) -> float:
        source_count = len(set(referenced_docs))
        source_score = min(source_count / 5.0, 1.0)

        now = datetime.now(timezone.utc)
        ts = (
            timestamp
            if timestamp.tzinfo is not None
            else timestamp.replace(tzinfo=timezone.utc)
        )
        age_days = max((now - ts).total_seconds(), 0.0) / 86400.0

        if age_days <= 1:
            recency_score = 1.0
        elif age_days <= 7:
            recency_score = 0.85
        elif age_days <= 30:
            recency_score = 0.7
        else:
            recency_score = 0.5

        confidence = 0.7 * source_score + 0.3 * recency_score
        return round(max(0.0, min(confidence, 1.0)), 3)

    @staticmethod
    def _record_to_dict(record: ProvenanceRecord) -> dict:
        payload = asdict(record)
        payload["timestamp"] = record.timestamp.isoformat()
        return payload

    @staticmethod
    def _dict_to_record(payload: dict) -> ProvenanceRecord:
        return ProvenanceRecord(
            output_id=payload["output_id"],
            query=payload["query"],
            referenced_docs=list(payload.get("referenced_docs", [])),
            generated_text=payload.get("generated_text", ""),
            model=payload.get("model", ""),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            confidence=float(payload.get("confidence", 0.0)),
        )
