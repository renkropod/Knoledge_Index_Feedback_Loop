from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QualityReport:
    score: float
    metrics: dict
    suggestions: list[str]


class QualityScorer:
    ANALYSIS_MARKERS = (
        "따라서",
        "분석 결과",
        "이는 의미한다",
        "종합하면",
        "시사점",
        "결론적으로",
        "implication",
        "therefore",
        "this suggests",
    )

    INTRO_MARKERS = ("요약", "개요", "배경", "문제", "목표", "introduction")
    CONCLUSION_MARKERS = ("결론", "정리", "제언", "후속", "한계", "conclusion")

    def __init__(self):
        pass

    def score(
        self, output_text: str, context_docs: list[dict], query: str
    ) -> QualityReport:
        safe_text = (output_text or "").strip()
        safe_docs = context_docs or []
        safe_query = query or ""

        source_coverage = self._source_coverage_score(safe_text, safe_docs)
        length_adequacy = self._length_score(safe_text, safe_query)
        factual_grounding = self._factual_grounding_score(safe_text, safe_docs)
        novelty = self._novelty_score(safe_text, safe_docs)
        coherence = self._coherence_score(safe_text)

        metrics = {
            "source_coverage": source_coverage,
            "length_adequacy": length_adequacy,
            "factual_grounding": factual_grounding,
            "novelty": novelty,
            "coherence": coherence,
        }

        weights = {
            "source_coverage": 0.25,
            "length_adequacy": 0.15,
            "factual_grounding": 0.25,
            "novelty": 0.20,
            "coherence": 0.15,
        }

        overall = sum(metrics[name] * weight for name, weight in weights.items())
        suggestions = self._build_suggestions(metrics)

        return QualityReport(
            score=self._clamp(overall),
            metrics={k: self._clamp(v) for k, v in metrics.items()},
            suggestions=suggestions,
        )

    def _source_coverage_score(
        self, output_text: str, context_docs: list[dict]
    ) -> float:
        if not context_docs:
            return 1.0

        text_lower = output_text.lower()
        total = 0
        covered = 0
        for doc in context_docs:
            refs = self._doc_reference_tokens(doc)
            if not refs:
                continue
            total += 1
            if any(token.lower() in text_lower for token in refs):
                covered += 1

        if total == 0:
            return 0.0
        return covered / total

    def _length_score(self, output_text: str, query: str) -> float:
        length = len(output_text)
        if length == 0:
            return 0.0

        if length < 200:
            return self._clamp(length / 200.0)
        if length > 10000:
            overflow = min(length - 10000, 10000)
            return self._clamp(1.0 - (overflow / 10000.0))

        query_complexity = len(query.strip())
        if query_complexity > 120:
            preferred_min = 600
        elif query_complexity > 40:
            preferred_min = 400
        else:
            preferred_min = 250

        if length < preferred_min:
            return self._clamp(0.65 + 0.35 * (length / preferred_min))
        if length <= 5000:
            return 1.0

        taper = min(length - 5000, 5000)
        return self._clamp(1.0 - 0.25 * (taper / 5000.0))

    def _novelty_score(self, output_text: str, context_docs: list[dict]) -> float:
        text_lower = output_text.lower()
        markers_found = sum(
            1 for marker in self.ANALYSIS_MARKERS if marker.lower() in text_lower
        )
        marker_score = min(markers_found / 3.0, 1.0)

        context_joined = " ".join(
            str(doc.get("text") or doc.get("content") or "") for doc in context_docs
        ).strip()
        if not context_joined:
            return marker_score

        overlap_ratio = self._token_overlap_ratio(output_text, context_joined)
        synthesis_bonus = 1.0 - overlap_ratio

        return self._clamp(0.6 * marker_score + 0.4 * synthesis_bonus)

    def _coherence_score(self, output_text: str) -> float:
        if not output_text.strip():
            return 0.0

        paragraphs = [
            block.strip()
            for block in re.split(r"\n\s*\n", output_text)
            if block.strip()
        ]
        para_score = min(len(paragraphs) / 4.0, 1.0)

        heading_like_count = sum(
            1
            for line in output_text.splitlines()
            if line.strip()
            and len(line.strip()) <= 40
            and line.rstrip().endswith((":", "?"))
        )
        heading_score = min(heading_like_count / 3.0, 1.0)

        lowered = output_text.lower()
        intro_present = any(marker in lowered for marker in self.INTRO_MARKERS)
        conclusion_present = any(
            marker in lowered for marker in self.CONCLUSION_MARKERS
        )
        structure_score = (
            1.0
            if intro_present and conclusion_present
            else 0.5
            if (intro_present or conclusion_present)
            else 0.0
        )

        return self._clamp(
            0.45 * para_score + 0.20 * heading_score + 0.35 * structure_score
        )

    def _factual_grounding_score(
        self, output_text: str, context_docs: list[dict]
    ) -> float:
        sentences = [
            s.strip()
            for s in re.split(r"[.!?\n]+", output_text)
            if len(s.strip()) >= 20
        ]
        if not sentences:
            return 0.0

        refs = []
        for doc in context_docs:
            refs.extend(self._doc_reference_tokens(doc))
        refs = [item.lower() for item in refs if item]

        if not refs:
            return 0.5

        backed = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            has_ref = any(token in sentence_lower for token in refs)
            has_citation_pattern = bool(
                re.search(r"\[(?:\d+|source|ref|doc)\]", sentence_lower)
            )
            if has_ref or has_citation_pattern:
                backed += 1

        ratio = backed / len(sentences)
        return self._clamp(0.2 + 0.8 * ratio)

    def _build_suggestions(self, metrics: dict[str, float]) -> list[str]:
        suggestions: list[str] = []

        if metrics.get("source_coverage", 0.0) < 0.6:
            suggestions.append(
                "더 많은 원문 출처 제목/ID를 본문에 명시해 근거 범위를 넓히세요."
            )
        if metrics.get("factual_grounding", 0.0) < 0.6:
            suggestions.append(
                "주요 주장마다 출처 표기(문서 ID, 제목, 인용 표식)를 추가하세요."
            )
        if metrics.get("length_adequacy", 0.0) < 0.6:
            suggestions.append(
                "응답 길이를 조정하세요. 200~10000자 범위에서 질의 복잡도에 맞추는 것이 좋습니다."
            )
        if metrics.get("novelty", 0.0) < 0.6:
            suggestions.append(
                "요약을 넘어 원인-결과, 시사점, 비교 분석 문장을 더 포함하세요."
            )
        if metrics.get("coherence", 0.0) < 0.6:
            suggestions.append("도입-본론-결론 구조와 문단 구분을 명확히 하세요.")

        return suggestions

    @staticmethod
    def _doc_reference_tokens(doc: dict) -> list[str]:
        tokens: list[str] = []
        if not isinstance(doc, dict):
            return tokens

        for key in ("id", "doc_id", "title", "source_doc"):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                tokens.append(value.strip())

        metadata = doc.get("metadata")
        if isinstance(metadata, dict):
            for key in ("id", "doc_id", "title", "source_doc"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    tokens.append(value.strip())

        return list(dict.fromkeys(tokens))

    @staticmethod
    def _token_overlap_ratio(text_a: str, text_b: str) -> float:
        tokens_a = set(re.findall(r"[\w가-힣]{3,}", text_a.lower()))
        tokens_b = set(re.findall(r"[\w가-힣]{3,}", text_b.lower()))
        if not tokens_a or not tokens_b:
            return 0.0

        overlap = len(tokens_a.intersection(tokens_b))
        denominator = min(len(tokens_a), len(tokens_b))
        if denominator == 0:
            return 0.0
        return overlap / denominator

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
