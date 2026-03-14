from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from anthropic import AsyncAnthropic


@dataclass
class GenerationResult:
    text: str
    referenced_docs: list[str]
    token_usage: dict[str, int]
    model: str
    timestamp: datetime


class LLMGenerator:
    def __init__(
        self,
        llm_client: AsyncAnthropic,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 1200,
    ):
        self.client = llm_client
        self.model = model
        self.max_tokens = max_tokens

    async def generate(
        self,
        query: str,
        context: str,
        system_prompt: str | None = None,
    ) -> GenerationResult:
        prompt = self._build_generation_prompt(query=query, context=context)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt or self._default_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        )

        text = self._extract_text(response)
        usage = getattr(response, "usage", None)
        token_usage = {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        }

        return GenerationResult(
            text=text,
            referenced_docs=self._extract_referenced_docs(context),
            token_usage=token_usage,
            model=str(getattr(response, "model", self.model)),
            timestamp=datetime.utcnow(),
        )

    async def generate_research_report(
        self,
        topic: str,
        context: str,
        existing_knowledge: str = "",
    ) -> GenerationResult:
        report_system_prompt = (
            "You are a rigorous research report writer. Cite sources with document IDs, "
            "clearly separate established facts from your new analysis, and explicitly note "
            "contradictions or uncertainty. You may answer in Korean or English depending on "
            "the user context, and you should preserve key Korean terminology when present."
        )

        report_prompt = self._build_research_prompt(
            topic=topic,
            context=context,
            existing_knowledge=existing_knowledge,
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=report_system_prompt,
            messages=[{"role": "user", "content": report_prompt}],
        )

        text = self._extract_text(response)
        usage = getattr(response, "usage", None)
        token_usage = {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        }

        return GenerationResult(
            text=text,
            referenced_docs=self._extract_referenced_docs(context),
            token_usage=token_usage,
            model=str(getattr(response, "model", self.model)),
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def _extract_text(response) -> str:
        content_blocks = getattr(response, "content", [])
        text_parts = []
        for block in content_blocks:
            text = getattr(block, "text", None)
            if text:
                text_parts.append(text)
        return "\n".join(text_parts).strip()

    @staticmethod
    def _extract_referenced_docs(context: str) -> list[str]:
        patterns = [
            r'"doc_id"\s*:\s*"([^"\\]+)"',
            r'"source_doc"\s*:\s*"([^"\\]+)"',
            r"\bdoc_id\s*[:=]\s*([A-Za-z0-9._:-]+)",
            r"\bsource_doc\s*[:=]\s*([A-Za-z0-9._:-]+)",
            r"\[\s*doc(?:ument)?(?:_id)?\s*[:=]\s*([A-Za-z0-9._:-]+)\s*\]",
            r"\[\[\s*doc\s*[:=]\s*([A-Za-z0-9._:-]+)\s*\]\]",
        ]

        seen = set()
        doc_ids: list[str] = []
        for pattern in patterns:
            for match in re.findall(pattern, context, flags=re.IGNORECASE):
                doc_id = match.strip()
                if not doc_id or doc_id in seen:
                    continue
                seen.add(doc_id)
                doc_ids.append(doc_id)
        return doc_ids

    @staticmethod
    def _default_system_prompt() -> str:
        return (
            "You are a knowledge-grounded research assistant. Use only the provided context "
            "for factual claims when possible. Cite source document IDs inline for key claims. "
            "Clearly separate established facts from your own analysis or inferences. If context "
            "is insufficient, state uncertainty explicitly instead of guessing."
        )

    @staticmethod
    def _build_generation_prompt(query: str, context: str) -> str:
        return (
            "Answer the query using the supplied context.\n\n"
            "[Context]\n"
            f"{context}\n\n"
            "[Query]\n"
            f"{query}\n\n"
            "Response requirements:\n"
            "1) Cite relevant document IDs for important factual statements.\n"
            "2) Mark uncertain points clearly.\n"
            "3) Distinguish facts from analysis."
        )

    @staticmethod
    def _build_research_prompt(
        topic: str,
        context: str,
        existing_knowledge: str,
    ) -> str:
        existing_block = existing_knowledge.strip() or "(none)"
        return (
            "Generate a concise research report for the topic below.\n"
            "You may write in Korean when the topic/context is Korean.\n\n"
            "[Topic]\n"
            f"{topic}\n\n"
            "[Retrieved Context]\n"
            f"{context}\n\n"
            "[Existing Knowledge]\n"
            f"{existing_block}\n\n"
            "Report requirements:\n"
            "- Section 1: Established facts (with document ID citations).\n"
            "- Section 2: New insights from synthesis/analysis.\n"
            "- Section 3: Contradictions, gaps, or uncertain claims.\n"
            "- Keep claims grounded in provided context."
        )
