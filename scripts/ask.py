#!/usr/bin/env python3
"""
RAG 기반 한국어 Q&A — Knowledge Base를 활용하여 정제된 한국어 답변 생성
사용법: python scripts/ask.py "최근 AI 트렌드를 요약해줘"
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Settings
from config.llm_client import create_llm_client, get_model_name
from retrieval import ContextAssembler, DualLevelRetriever
from storage import KnowledgeGraph, TemporalFactStore, VectorStore

ANSWER_PROMPT = (
    "당신은 기술 트렌드 분석가입니다. "
    "아래 Knowledge Base에서 검색된 컨텍스트를 기반으로 사용자의 질문에 한국어로 답변하세요.\n\n"
    "규칙:\n"
    "1. 반드시 컨텍스트에 있는 정보만 사용하세요.\n"
    "2. 출처(entity 이름, 문서 제목)를 인용하세요.\n"
    "3. 최신 정보를 우선하세요.\n"
    "4. 모르는 내용은 '해당 정보가 KB에 없습니다'라고 답하세요.\n"
    "5. 구조화된 마크다운 형식으로 답변하세요.\n\n"
)


async def ask(question: str, top_k: int = 10, verbose: bool = False):
    settings = Settings.load()
    hf_home = Path(__file__).resolve().parent.parent / ".cache" / "hf"
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(hf_home))

    kg = KnowledgeGraph(settings.storage.graph_path)
    ts = TemporalFactStore(settings.storage.temporal_path)
    vs = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )

    retriever = DualLevelRetriever(graph_store=kg, vector_store=vs, temporal_store=ts)
    assembler = ContextAssembler(max_context_tokens=6000)

    t0 = time.perf_counter()
    results = await retriever.retrieve(query=question, top_k=top_k, mode="hybrid")
    t_retrieve = time.perf_counter() - t0

    if not results:
        print("KB에서 관련 정보를 찾지 못했습니다.")
        return

    temporal_facts = []
    for r in results:
        entity = r.get("entity", "")
        if entity:
            temporal_facts.extend(ts.query_current(entity))

    context = assembler.assemble_with_temporal(results, question, temporal_facts)

    if verbose:
        print(f"검색 결과: {len(results)}건 ({t_retrieve:.2f}s)")
        print(f"컨텍스트: {len(context)} chars")
        print("-" * 60)

    llm_client = create_llm_client()
    model_name = get_model_name()

    prompt = ANSWER_PROMPT
    prompt += f"## 컨텍스트\n{context}\n\n"
    prompt += f"## 질문\n{question}\n\n"
    prompt += "## 답변\n"

    t1 = time.perf_counter()
    resp = await llm_client.messages.create(
        model=model_name,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = resp.content[0].text
    t_gen = time.perf_counter() - t1

    print(answer)

    if verbose:
        print(f"\n{'─' * 60}")
        print(f"검색: {t_retrieve:.2f}s | 생성: {t_gen:.2f}s")
        print(
            f"KB: {kg.get_stats()['total_nodes']} entities, {vs.get_stats()['total_documents']} vectors"
        )

        print(f"\n참고 소스:")
        for i, r in enumerate(results[:5], 1):
            entity = r.get("entity", "?")
            score = r.get("final_score", 0)
            print(f"  {i}. {entity} ({score:.4f})")


def main():
    import argparse

    p = argparse.ArgumentParser(description="GAKMS 한국어 Q&A")
    p.add_argument("question", nargs="+", help="질문")
    p.add_argument("-k", "--top-k", type=int, default=10)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    asyncio.run(ask(" ".join(args.question), top_k=args.top_k, verbose=args.verbose))


if __name__ == "__main__":
    main()
