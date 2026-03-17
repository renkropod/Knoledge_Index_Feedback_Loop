from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import TypedDict, cast


class SourceEntry(TypedDict):
    title: str
    url: str
    date: str


class HistoryEntry(TypedDict):
    date: str
    event: str
    source: str


@dataclass
class KnowledgeCard:
    slug: str
    name: str
    category: str
    definition: str
    why_important: str
    related_tools: list[str]
    related_cards: list[str]
    representative_sources: list[SourceEntry]
    open_questions: list[str]
    history: list[HistoryEntry]
    first_seen: str
    last_updated: str
    mention_count: int


class KnowledgeCardStore:
    cards_dir: str
    _lock: threading.RLock

    def __init__(self, cards_dir: str = "knowledge_base/cards/"):
        self.cards_dir = cards_dir
        self._lock = threading.RLock()
        os.makedirs(self.cards_dir, exist_ok=True)

    def get(self, slug: str) -> KnowledgeCard | None:
        normalized_slug = self._slug(slug)
        if not normalized_slug:
            return None
        path = self._path_for_slug(normalized_slug)
        with self._lock:
            if not os.path.exists(path):
                return None
            try:
                with open(path, "r", encoding="utf-8") as file_obj:
                    raw_payload_obj = cast(object, json.load(file_obj))
            except (OSError, json.JSONDecodeError):
                return None
        if not isinstance(raw_payload_obj, dict):
            return None
        payload: dict[str, object] = {}
        raw_payload = cast(dict[object, object], raw_payload_obj)
        for key_obj, value_obj in raw_payload.items():
            payload[str(key_obj)] = value_obj
        return self._from_payload(payload)

    def upsert(self, card: KnowledgeCard) -> None:
        normalized = self._normalize_card(card)
        existing = self.get(normalized.slug)
        merged = normalized if existing is None else self._merge(existing, normalized)
        with self._lock:
            self._write_card(merged)

    def search(self, query: str) -> list[KnowledgeCard]:
        needle = query.strip().lower()
        if not needle:
            return []
        matches: list[KnowledgeCard] = []
        for card in self.get_all():
            tools_text = " ".join(card.related_tools).lower()
            if (
                needle in card.name.lower()
                or needle in card.definition.lower()
                or needle in tools_text
            ):
                matches.append(card)
        return matches

    def get_recent(self, days: int = 7) -> list[KnowledgeCard]:
        window_days = max(days, 0)
        cutoff = date.today() - timedelta(days=window_days)
        recent: list[KnowledgeCard] = []
        for card in self.get_all():
            updated = self._parse_iso_date(card.last_updated)
            if updated is not None and updated >= cutoff:
                recent.append(card)
        return recent

    def get_all(self) -> list[KnowledgeCard]:
        with self._lock:
            try:
                names = os.listdir(self.cards_dir)
            except OSError:
                return []
        cards: list[KnowledgeCard] = []
        for name in names:
            if not name.endswith(".json"):
                continue
            full_path = os.path.join(self.cards_dir, name)
            if not os.path.isfile(full_path):
                continue
            card = self.get(name[:-5])
            if card is not None:
                cards.append(card)
        cards.sort(
            key=lambda item: (
                self._parse_iso_date(item.last_updated) or date.min,
                item.slug,
            ),
            reverse=True,
        )
        return cards

    def get_stats(self) -> dict[str, object]:
        cards = self.get_all()
        if not cards:
            return {
                "total_cards": 0,
                "categories": {},
                "avg_mention_count": 0.0,
            }
        categories: dict[str, int] = {}
        total_mentions = 0
        for card in cards:
            categories[card.category] = categories.get(card.category, 0) + 1
            total_mentions += card.mention_count
        return {
            "total_cards": len(cards),
            "categories": categories,
            "avg_mention_count": total_mentions / len(cards),
        }

    def to_markdown(self, card: KnowledgeCard) -> str:
        tools = ", ".join(card.related_tools) if card.related_tools else "-"
        related = ", ".join(card.related_cards) if card.related_cards else "-"
        if card.representative_sources:
            sources = "\n".join(
                f"- [{source['title']}]({source['url']}) ({source['date']})"
                for source in card.representative_sources
            )
        else:
            sources = "- None"
        if card.open_questions:
            questions = "\n".join(f"- {question}" for question in card.open_questions)
        else:
            questions = "- None"
        if card.history:
            history = "\n".join(
                f"- {item['date']}: {item['event']} ({item['source']})"
                for item in card.history
            )
        else:
            history = "- None"
        return "\n".join(
            [
                f"# {card.name}",
                "",
                f"- Slug: `{card.slug}`",
                f"- Category: `{card.category}`",
                f"- First seen: `{card.first_seen}`",
                f"- Last updated: `{card.last_updated}`",
                f"- Mention count: `{card.mention_count}`",
                "",
                "## Definition",
                card.definition,
                "",
                "## Why Important",
                card.why_important,
                "",
                "## Related Tools",
                tools,
                "",
                "## Related Cards",
                related,
                "",
                "## Representative Sources",
                sources,
                "",
                "## Open Questions",
                questions,
                "",
                "## History",
                history,
            ]
        )

    @staticmethod
    def _slug(name: str) -> str:
        lowered = name.strip().lower()
        dashed = re.sub(r"[^a-z0-9]+", "-", lowered)
        compacted = re.sub(r"-+", "-", dashed)
        return compacted.strip("-")

    def _merge(self, existing: KnowledgeCard, new: KnowledgeCard) -> KnowledgeCard:
        merged_definition = (
            new.definition
            if len(new.definition.strip()) > len(existing.definition.strip())
            else existing.definition
        )
        mention_increment = new.mention_count if new.mention_count > 0 else 1
        return KnowledgeCard(
            slug=existing.slug,
            name=new.name if new.name else existing.name,
            category=new.category if new.category else existing.category,
            definition=merged_definition,
            why_important=(
                new.why_important
                if len(new.why_important.strip()) >= len(existing.why_important.strip())
                else existing.why_important
            ),
            related_tools=self._dedup_preserve(
                existing.related_tools + new.related_tools
            ),
            related_cards=self._dedup_preserve(
                existing.related_cards + new.related_cards
            ),
            representative_sources=self._merge_sources(
                existing.representative_sources,
                new.representative_sources,
            ),
            open_questions=self._dedup_preserve(
                existing.open_questions + new.open_questions
            ),
            history=existing.history + new.history,
            first_seen=existing.first_seen,
            last_updated=new.last_updated or date.today().isoformat(),
            mention_count=existing.mention_count + mention_increment,
        )

    def _normalize_card(self, card: KnowledgeCard) -> KnowledgeCard:
        today = date.today().isoformat()
        slug = self._slug(card.slug or card.name)
        first_seen = card.first_seen or today
        last_updated = card.last_updated or today
        mention_count = card.mention_count if card.mention_count > 0 else 1
        related_tools = self._dedup_preserve(
            [tool.strip() for tool in card.related_tools if tool.strip()]
        )
        related_cards = self._dedup_preserve(
            [self._slug(value) for value in card.related_cards if self._slug(value)]
        )
        return KnowledgeCard(
            slug=slug,
            name=card.name.strip(),
            category=card.category.strip(),
            definition=card.definition.strip(),
            why_important=card.why_important.strip(),
            related_tools=related_tools,
            related_cards=related_cards,
            representative_sources=self._normalize_sources(card.representative_sources),
            open_questions=self._dedup_preserve(
                [q.strip() for q in card.open_questions if q.strip()]
            ),
            history=self._normalize_history(card.history),
            first_seen=first_seen,
            last_updated=last_updated,
            mention_count=mention_count,
        )

    @staticmethod
    def _dedup_preserve(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _merge_sources(
        existing: list[SourceEntry],
        new: list[SourceEntry],
    ) -> list[SourceEntry]:
        seen: set[tuple[str, str, str]] = set()
        merged: list[SourceEntry] = []
        for item in existing + new:
            key = (item["title"], item["url"], item["date"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    @staticmethod
    def _normalize_sources(sources: list[SourceEntry]) -> list[SourceEntry]:
        cleaned: list[SourceEntry] = []
        for source in sources:
            title = source.get("title", "").strip()
            url = source.get("url", "").strip()
            source_date = source.get("date", "").strip()
            if not (title or url or source_date):
                continue
            cleaned.append({"title": title, "url": url, "date": source_date})
        return KnowledgeCardStore._merge_sources([], cleaned)

    @staticmethod
    def _normalize_history(entries: list[HistoryEntry]) -> list[HistoryEntry]:
        cleaned: list[HistoryEntry] = []
        today = date.today().isoformat()
        for entry in entries:
            event_date = entry.get("date", "").strip() or today
            event = entry.get("event", "").strip()
            source = entry.get("source", "").strip()
            if not (event or source):
                continue
            cleaned.append({"date": event_date, "event": event, "source": source})
        return cleaned

    def _write_card(self, card: KnowledgeCard) -> None:
        path = self._path_for_slug(card.slug)
        payload = asdict(card)
        with open(path, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, ensure_ascii=False, indent=2)

    def _path_for_slug(self, slug: str) -> str:
        return os.path.join(self.cards_dir, f"{slug}.json")

    @staticmethod
    def _parse_iso_date(value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except ValueError:
            if "T" not in value:
                return None
            date_part = value.split("T", 1)[0]
            try:
                return date.fromisoformat(date_part)
            except ValueError:
                return None

    @staticmethod
    def _from_payload(payload: dict[str, object]) -> KnowledgeCard:
        today = date.today().isoformat()
        raw_slug = str(payload.get("slug", ""))
        name = str(payload.get("name", "")).strip()
        category = str(payload.get("category", "term")).strip() or "term"
        definition = str(payload.get("definition", "")).strip()
        why_important = str(payload.get("why_important", "")).strip()
        first_seen = str(payload.get("first_seen", today)).strip() or today
        last_updated = str(payload.get("last_updated", today)).strip() or today
        raw_mention_count = payload.get("mention_count", 1)
        mention_count = 1
        if isinstance(raw_mention_count, int):
            mention_count = raw_mention_count
        elif isinstance(raw_mention_count, str):
            try:
                mention_count = int(raw_mention_count)
            except ValueError:
                mention_count = 1
        mention_count = mention_count if mention_count > 0 else 1

        related_tools = KnowledgeCardStore._normalize_str_list(
            payload.get("related_tools", [])
        )
        related_cards = [
            KnowledgeCardStore._slug(item)
            for item in KnowledgeCardStore._normalize_str_list(
                payload.get("related_cards", [])
            )
            if KnowledgeCardStore._slug(item)
        ]
        open_questions = KnowledgeCardStore._normalize_str_list(
            payload.get("open_questions", [])
        )

        raw_sources = payload.get("representative_sources", [])
        parsed_sources = KnowledgeCardStore._parse_sources(raw_sources)
        raw_history = payload.get("history", [])
        parsed_history = KnowledgeCardStore._parse_history(raw_history)

        return KnowledgeCard(
            slug=KnowledgeCardStore._slug(raw_slug) or KnowledgeCardStore._slug(name),
            name=name,
            category=category,
            definition=definition,
            why_important=why_important,
            related_tools=KnowledgeCardStore._dedup_preserve(related_tools),
            related_cards=KnowledgeCardStore._dedup_preserve(related_cards),
            representative_sources=KnowledgeCardStore._normalize_sources(
                parsed_sources
            ),
            open_questions=KnowledgeCardStore._dedup_preserve(open_questions),
            history=KnowledgeCardStore._normalize_history(parsed_history),
            first_seen=first_seen,
            last_updated=last_updated,
            mention_count=mention_count,
        )

    @staticmethod
    def _normalize_str_list(raw: object) -> list[str]:
        if not isinstance(raw, list):
            return []
        values: list[str] = []
        raw_items = cast(list[object], raw)
        for item in raw_items:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if cleaned:
                values.append(cleaned)
        return values

    @staticmethod
    def _parse_sources(raw: object) -> list[SourceEntry]:
        if not isinstance(raw, list):
            return []
        values: list[SourceEntry] = []
        raw_items = cast(list[object], raw)
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            item_dict: dict[str, object] = {}
            raw_item = cast(dict[object, object], item)
            for key_obj, value_obj in raw_item.items():
                item_dict[str(key_obj)] = value_obj
            title = str(item_dict.get("title", "")).strip()
            url = str(item_dict.get("url", "")).strip()
            source_date = str(item_dict.get("date", "")).strip()
            values.append({"title": title, "url": url, "date": source_date})
        return values

    @staticmethod
    def _parse_history(raw: object) -> list[HistoryEntry]:
        if not isinstance(raw, list):
            return []
        values: list[HistoryEntry] = []
        raw_items = cast(list[object], raw)
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            item_dict: dict[str, object] = {}
            raw_item = cast(dict[object, object], item)
            for key_obj, value_obj in raw_item.items():
                item_dict[str(key_obj)] = value_obj
            event_date = str(item_dict.get("date", "")).strip()
            event = str(item_dict.get("event", "")).strip()
            source = str(item_dict.get("source", "")).strip()
            values.append({"date": event_date, "event": event, "source": source})
        return values
