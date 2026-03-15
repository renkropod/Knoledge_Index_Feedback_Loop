from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT = """Extract entities and relations from the provided text and respond with JSON only.

Expected output schema:
{
  "entities": [
    {"name": "...", "type": "PERSON|ORGANIZATION|PROTOCOL|CONCEPT|METRIC|EVENT|TECHNOLOGY|LOCATION", "description": "..."}
  ],
  "relations": [
    {"source": "...", "target": "...", "relation": "UPPERCASE_SNAKE_CASE", "description": "...", "weight": 0.0}
  ]
}

Rules:
1) Only include entities that are meaningful and specific.
2) Relation direction must be explicit and correct.
3) relation must be UPPERCASE_SNAKE_CASE.
4) weight must be between 0.0 and 1.0.
5) Normalize entity names to canonical forms where possible.
6) Return valid JSON only. No markdown, no explanations.
"""


class EntityExtractor:
    def __init__(
        self,
        llm_client: Any,
        model: str = "claude-sonnet-4-20250514",
        max_concurrent: int = 3,
    ) -> None:
        self.llm_client = llm_client
        self.model = model
        self._max_concurrent = max_concurrent
        self.base_prompt = self._load_prompt()

    async def extract(
        self, text: str, chunk_size: int = 2000
    ) -> Dict[str, List[Dict[str, Any]]]:
        return await self._extract_internal(
            text=text, chunk_size=chunk_size, prompt_modifier=""
        )

    async def extract_with_insight_filter(
        self,
        text: str,
        prompt_modifier: str = "",
    ) -> Dict[str, List[Dict[str, Any]]]:
        insight_modifier = (
            "Focus only on new, non-obvious insights that add distinct information. "
            "Avoid generic or already implied entities and relations."
        )
        if prompt_modifier.strip():
            insight_modifier = f"{insight_modifier}\n{prompt_modifier.strip()}"

        return await self._extract_internal(
            text=text, chunk_size=2000, prompt_modifier=insight_modifier
        )

    def _split_text(self, text: str, chunk_size: int, overlap: int = 200) -> List[str]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        normalized_text = text.strip()
        if not normalized_text:
            return []

        chunks: List[str] = []
        start = 0
        text_length = len(normalized_text)
        step = chunk_size - overlap

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(normalized_text[start:end])
            if end >= text_length:
                break
            start += step

        return chunks

    async def _extract_internal(
        self,
        text: str,
        chunk_size: int,
        prompt_modifier: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        chunks = self._split_text(text=text, chunk_size=chunk_size, overlap=200)
        merged_entities: List[Dict[str, Any]] = []
        merged_relations: List[Dict[str, Any]] = []
        semaphore = asyncio.Semaphore(self._max_concurrent)

        tasks = [
            self._extract_single_chunk(
                chunk=chunk,
                chunk_index=chunk_index,
                prompt_modifier=prompt_modifier,
                semaphore=semaphore,
            )
            for chunk_index, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

        text_lower = text.lower()

        for chunk_index, payload in results:
            if not payload:
                continue

            entities = payload.get("entities", [])
            relations = payload.get("relations", [])
            if not isinstance(entities, list) or not isinstance(relations, list):
                LOGGER.warning(
                    "Chunk %s returned invalid structure; skipping", chunk_index
                )
                continue

            grounded_names: set[str] = set()
            for entity in entities:
                if isinstance(entity, dict):
                    name = str(entity.get("name", "")).strip()
                    if not name:
                        continue
                    if not self._is_grounded(name, text_lower):
                        continue
                    entity.setdefault("chunk_index", chunk_index)
                    merged_entities.append(entity)
                    grounded_names.add(name)

            for relation in relations:
                if isinstance(relation, dict):
                    src = str(relation.get("source", "")).strip()
                    tgt = str(relation.get("target", "")).strip()
                    if src not in grounded_names or tgt not in grounded_names:
                        continue
                    relation.setdefault("chunk_index", chunk_index)
                    merged_relations.append(relation)

        return {"entities": merged_entities, "relations": merged_relations}

    @staticmethod
    def _is_grounded(entity_name: str, source_text_lower: str) -> bool:
        name_lower = entity_name.lower()
        if name_lower in source_text_lower:
            return True
        tokens = name_lower.split()
        if len(tokens) >= 2:
            matched = sum(1 for t in tokens if t in source_text_lower and len(t) > 2)
            return matched >= max(2, len(tokens) // 2)
        return False

    async def _extract_single_chunk(
        self,
        chunk: str,
        chunk_index: int,
        prompt_modifier: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[int, Optional[Dict[str, Any]]]:
        async with semaphore:
            payload = await self._extract_chunk_with_retries(
                chunk=chunk,
                chunk_index=chunk_index,
                prompt_modifier=prompt_modifier,
            )
        return chunk_index, payload

    async def _extract_chunk_with_retries(
        self,
        chunk: str,
        chunk_index: int,
        prompt_modifier: str,
    ) -> Optional[Dict[str, Any]]:
        retries = 2
        for attempt in range(retries + 1):
            try:
                response = await self.llm_client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": self._build_prompt(
                                chunk=chunk, prompt_modifier=prompt_modifier
                            ),
                        }
                    ],
                )
            except Exception:
                LOGGER.exception(
                    "Claude API call failed for chunk %s on attempt %s",
                    chunk_index,
                    attempt + 1,
                )
                continue

            raw_text = self._extract_response_text(response)
            try:
                return self._parse_json(raw_text)
            except json.JSONDecodeError:
                LOGGER.warning(
                    "JSON parsing failed for chunk %s on attempt %s",
                    chunk_index,
                    attempt + 1,
                )

        LOGGER.error("Skipping chunk %s after retry exhaustion", chunk_index)
        return None

    def _build_prompt(self, chunk: str, prompt_modifier: str) -> str:
        modifier = prompt_modifier.strip()
        if modifier:
            modifier = f"\nAdditional constraints:\n{modifier}\n"

        return f"{self.base_prompt}{modifier}\nText:\n{chunk}"

    def _load_prompt(self) -> str:
        prompt_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "prompts"
            / "entity_extraction.txt"
        )
        try:
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8").strip() or DEFAULT_PROMPT
        except OSError:
            LOGGER.exception("Failed loading prompt from %s", prompt_path)

        LOGGER.info("Using inline default entity extraction prompt")
        return DEFAULT_PROMPT

    def _extract_response_text(self, response: Any) -> str:
        content_blocks = getattr(response, "content", [])
        if not isinstance(content_blocks, list):
            return ""

        texts: List[str] = []
        for block in content_blocks:
            block_text = getattr(block, "text", None)
            if isinstance(block_text, str):
                texts.append(block_text)
            elif isinstance(block, dict):
                possible_text = block.get("text")
                if isinstance(possible_text, str):
                    texts.append(possible_text)

        return "\n".join(texts).strip()

    def _parse_json(self, content: str) -> Dict[str, Any]:
        if not content:
            raise json.JSONDecodeError("Empty response", "", 0)

        fenced_match = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL
        )
        raw_json = fenced_match.group(1) if fenced_match else content

        if not fenced_match:
            brace_match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if brace_match:
                raw_json = brace_match.group(0)

        parsed = json.loads(raw_json)
        if not isinstance(parsed, dict):
            raise json.JSONDecodeError("JSON root must be object", raw_json, 0)
        return parsed
