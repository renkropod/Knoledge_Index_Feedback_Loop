from __future__ import annotations

# pyright: reportUnknownParameterType=false, reportMissingTypeArgument=false, reportUnannotatedClassAttribute=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAny=false, reportExplicitAny=false

from datetime import datetime
from typing import Any


class ContextAssembler:
    def __init__(self, max_context_tokens: int = 4000):
        self.max_context_tokens = max_context_tokens

    def assemble(self, results: list[dict], query: str) -> str:
        max_chars = self.max_context_tokens * 4
        lines = [f"Query: {query}", "", "Retrieved Context:"]

        for index, item in enumerate(results, start=1):
            text = str(item.get("text") or item.get("entity") or "").strip()
            if not text:
                continue

            source_doc = str(item.get("source_doc") or "unknown")
            score = self._safe_float(item.get("final_score"), default=0.0)
            candidate_lines = [
                f"{index}. {text}",
                f"   [Source: {source_doc}, Score: {score:.2f}]",
            ]

            if item.get("timestamp"):
                timestamp = self._format_timestamp(item["timestamp"])
                if timestamp:
                    candidate_lines[1] = (
                        f"   [Source: {source_doc}, Score: {score:.2f}, Time: {timestamp}]"
                    )

            proposed = "\n".join(lines + candidate_lines)
            if len(proposed) > max_chars:
                break

            lines.extend(candidate_lines)

        return "\n".join(lines).strip()

    def assemble_with_temporal(
        self, results: list[dict], query: str, temporal_facts: list
    ) -> str:
        base_context = self.assemble(results=results, query=query)
        max_chars = self.max_context_tokens * 4

        lines = [base_context, "", "Temporal Facts:"]
        for fact in temporal_facts:
            formatted_fact = self._format_temporal_fact(fact)
            if not formatted_fact:
                continue

            candidate = "\n".join(lines + [formatted_fact])
            if len(candidate) > max_chars:
                break

            lines.append(formatted_fact)

        return "\n".join(lines).strip()

    @staticmethod
    def _format_temporal_fact(fact: Any) -> str:
        if isinstance(fact, dict):
            entity = fact.get("entity")
            attribute = fact.get("attribute")
            value = fact.get("value")
            source_doc = fact.get("source_doc", "unknown")
            valid_from = fact.get("valid_from")
            valid_until = fact.get("valid_until")
        else:
            entity = getattr(fact, "entity", None)
            attribute = getattr(fact, "attribute", None)
            value = getattr(fact, "value", None)
            source_doc = getattr(fact, "source_doc", "unknown")
            valid_from = getattr(fact, "valid_from", None)
            valid_until = getattr(fact, "valid_until", None)

        if not entity or not attribute:
            return ""

        valid_from_text = ContextAssembler._format_timestamp(valid_from) or "unknown"
        valid_until_text = ContextAssembler._format_timestamp(valid_until) or "present"
        value_text = value if value is not None else "unknown"
        return (
            f"- {entity}.{attribute} = {value_text} "
            f"({valid_from_text} -> {valid_until_text}) [Source: {source_doc}]"
        )

    @staticmethod
    def _format_timestamp(timestamp: Any) -> str:
        if not timestamp:
            return ""
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        return str(timestamp)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
