#!/usr/bin/env python3
"""
Daily News Pipeline — 하루 2회 (10AM/10PM KST) 자동 실행
1. HN/Lobsters/Dev.to/RSS에서 최근 12시간 뉴스 수집
2. vLLM으로 한국어 entity/relation 추출 (source-grounded)
3. KB 증분 업데이트 (기존 데이터 유지)
4. 트렌드 감지 (신규 entity, 성장 community, 핫 토픽)
5. 한국어 마크다운 리포트 생성 → knowledge_base/reports/
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp
from bs4 import BeautifulSoup

from config import Settings
from config.llm_client import create_llm_client, get_model_name
from extraction import Deduplicator, RelationMapper
from ingestion import DocumentParser
from retrieval import ContextAssembler, DualLevelRetriever
from storage import KnowledgeGraph, TemporalFactStore, VectorStore
from storage.temporal_store import TemporalFact

ALGOLIA_SEARCH = "http://hn.algolia.com/api/v1/search"

KOREAN_PROMPT = (
    "아래 텍스트에서 엔티티와 관계를 추출하세요.\n\n"
    "규칙:\n"
    "1. 텍스트에 실제 등장하는 엔티티만 추출. 텍스트에 없는 엔티티 금지.\n"
    "2. description은 한국어로 작성. name은 원문 그대로 유지.\n"
    "3. 엔티티 최대 15개, 관계 최대 10개.\n\n"
    '출력: {"entities": [{"name": "...", "type": "...", "description": "한국어"}], '
    '"relations": [{"source": "...", "target": "...", "relation": "...", "description": "한국어", "weight": 0.9}]}\n\n'
    "텍스트:\n"
)

SEEN_IDS_PATH = Path("knowledge_base/.seen_ids.json")


def _load_seen_ids() -> set[str]:
    if SEEN_IDS_PATH.exists():
        try:
            return set(json.loads(SEEN_IDS_PATH.read_text()))
        except Exception:
            pass
    return set()


def _save_seen_ids(ids: set[str]) -> None:
    SEEN_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEN_IDS_PATH.write_text(json.dumps(sorted(ids)[-20000:]))


async def fetch_recent_hn(
    session: aiohttp.ClientSession,
    hours: int = 12,
    min_points: int = 5,
    max_stories: int = 500,
) -> list[dict[str, Any]]:
    cutoff = int(time.time()) - hours * 3600
    stories: list[dict[str, Any]] = []
    page = 0
    while len(stories) < max_stories and page < 10:
        params = {
            "tags": "story",
            "numericFilters": f"created_at_i>{cutoff},points>{min_points}",
            "hitsPerPage": 100,
            "page": page,
        }
        try:
            async with session.get(ALGOLIA_SEARCH, params=params) as resp:
                data = await resp.json()
        except Exception:
            break
        hits = data.get("hits", [])
        if not hits:
            break
        for hit in hits:
            stories.append(
                {
                    "id": f"hn_{hit.get('objectID', '')}",
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "points": hit.get("points", 0),
                    "author": hit.get("author", ""),
                    "created_at": hit.get("created_at_i", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "source": "hacker_news",
                }
            )
        page += 1
        if page >= data.get("nbPages", 0):
            break
        await asyncio.sleep(0.15)
    return stories


async def fetch_recent_lobsters(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    for page in range(1, 4):
        try:
            async with session.get(f"https://lobste.rs/page/{page}.json") as resp:
                if resp.status != 200:
                    break
                items = await resp.json()
        except Exception:
            break
        for item in items:
            stories.append(
                {
                    "id": f"lob_{item.get('short_id', '')}",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "points": item.get("score", 0),
                    "author": item.get("submitter_user", "")
                    if isinstance(item.get("submitter_user"), str)
                    else "",
                    "created_at": 0,
                    "num_comments": item.get("comment_count", 0),
                    "source": "lobsters",
                }
            )
        await asyncio.sleep(0.3)
    return stories


async def fetch_recent_devto(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    try:
        async with session.get(
            "https://dev.to/api/articles", params={"top": "1", "per_page": "50"}
        ) as resp:
            if resp.status == 200:
                items = await resp.json()
                for item in items:
                    stories.append(
                        {
                            "id": f"devto_{item.get('id', '')}",
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "points": item.get("positive_reactions_count", 0),
                            "author": (item.get("user") or {}).get("username", ""),
                            "created_at": 0,
                            "num_comments": item.get("comments_count", 0),
                            "source": "dev.to",
                        }
                    )
    except Exception:
        pass
    return stories


async def fetch_reddit(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    subreddits = ["programming", "technology", "MachineLearning", "netsec", "devops"]
    stories: list[dict[str, Any]] = []
    for sub in subreddits:
        url = f"https://old.reddit.com/r/{sub}/top/.json?t=day&limit=25"
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
        except Exception:
            continue
        for post in data.get("data", {}).get("children", []):
            d = post.get("data", {})
            if d.get("stickied"):
                continue
            stories.append(
                {
                    "id": f"reddit_{d.get('id', '')}",
                    "title": d.get("title", ""),
                    "url": d.get("url", ""),
                    "points": d.get("score", 0),
                    "author": d.get("author", ""),
                    "created_at": int(d.get("created_utc", 0)),
                    "num_comments": d.get("num_comments", 0),
                    "source": f"r/{sub}",
                }
            )
        await asyncio.sleep(1.0)
    return stories


async def fetch_github_trending(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []
    for period in ["daily"]:
        try:
            async with session.get(
                f"https://github.com/trending?since={period}"
            ) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()
        except Exception:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for repo in soup.select("article.Box-row")[:25]:
            name_el = repo.select_one("h2 a")
            desc_el = repo.select_one("p")
            if not name_el:
                continue
            repo_name = name_el.get_text(strip=True).replace("\n", "").replace(" ", "")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            href = name_el.get("href", "")
            url = f"https://github.com{href}" if href else ""

            stars_text = ""
            for span in repo.select("span.d-inline-block"):
                t = span.get_text(strip=True)
                if "stars" in t.lower():
                    stars_text = t
                    break
            stars = 0
            if stars_text:
                import re as _re

                m = _re.search(r"([\d,]+)", stars_text)
                if m:
                    stars = int(m.group(1).replace(",", ""))

            stories.append(
                {
                    "id": f"gh_{repo_name.replace('/', '_')}",
                    "title": f"{repo_name}: {desc[:100]}" if desc else repo_name,
                    "url": url,
                    "points": stars,
                    "author": repo_name.split("/")[0] if "/" in repo_name else "",
                    "created_at": 0,
                    "num_comments": 0,
                    "source": "github_trending",
                }
            )
    return stories


async def fetch_rss_feeds(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    feeds = [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("ArsTechnica", "https://feeds.arstechnica.com/arstechnica/index"),
        ("TheVerge", "https://www.theverge.com/rss/index.xml"),
    ]
    stories: list[dict[str, Any]] = []
    for name, url in feeds:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    continue
                xml = await resp.text()
        except Exception:
            continue
        soup = BeautifulSoup(xml, "html.parser")
        for item in soup.find_all("item")[:15]:
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el:
                stories.append(
                    {
                        "id": f"rss_{name}_{len(stories)}",
                        "title": title_el.get_text(strip=True),
                        "url": link_el.get_text(strip=True) if link_el else "",
                        "points": 0,
                        "author": name,
                        "created_at": 0,
                        "num_comments": 0,
                        "source": name,
                    }
                )
    return stories


async def fetch_article_text(session: aiohttp.ClientSession, url: str) -> str:
    if not url or any(x in url.lower() for x in ["pdf", "youtube.com", "twitter.com"]):
        return ""
    try:
        async with session.get(url) as resp:
            if resp.status >= 400:
                return ""
            html = await resp.text(errors="ignore")
    except Exception:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    article = soup.find("article") or soup.find("main") or soup.find("body")
    if not article:
        return ""
    text = article.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 30]
    return "\n".join(lines[:60])


def detect_trends(
    kg: KnowledgeGraph,
    new_entity_names: set[str],
    prev_node_count: int,
) -> dict[str, Any]:
    communities = kg.detect_communities()

    type_counter: Counter[str] = Counter()
    for name in new_entity_names:
        node = kg.graph.nodes.get(name, {})
        t = node.get("type", "unknown")
        type_counter[t] += 1

    hot_entities = []
    for name in new_entity_names:
        degree = kg.graph.degree(name) if kg.graph.has_node(name) else 0
        if degree >= 3:
            node = kg.graph.nodes.get(name, {})
            hot_entities.append(
                {
                    "name": name,
                    "type": node.get("type", "?"),
                    "degree": degree,
                }
            )
    hot_entities.sort(key=lambda x: -x["degree"])

    top_communities = []
    for c in communities[:10]:
        new_in_comm = sum(1 for m in c["members"] if m in new_entity_names)
        if new_in_comm > 0:
            top_communities.append(
                {
                    "label": c["label"],
                    "size": c["size"],
                    "dominant_type": c["dominant_type"],
                    "new_entities": new_in_comm,
                }
            )
    top_communities.sort(key=lambda x: -x["new_entities"])

    return {
        "new_entities_count": len(new_entity_names),
        "total_entities": kg.graph.number_of_nodes(),
        "growth": kg.graph.number_of_nodes() - prev_node_count,
        "type_distribution": dict(type_counter.most_common(10)),
        "hot_entities": hot_entities[:15],
        "active_communities": top_communities[:10],
        "total_communities": len(communities),
    }


def _build_structured_input(
    trends: dict[str, Any],
    stories: list[dict[str, Any]],
    stats: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append(f"수집 문서: {stats.get('docs_collected', 0)}건")
    lines.append(
        f"신규 엔티티: {trends['new_entities_count']}개 (총 {trends['total_entities']}개)"
    )
    lines.append(f"KB 성장: +{trends['growth']} 엔티티")
    lines.append(f"커뮤니티: {trends['total_communities']}개")
    lines.append("")

    if trends["hot_entities"]:
        lines.append("[핫 엔티티]")
        for e in trends["hot_entities"][:15]:
            lines.append(f"- {e['name']} (유형: {e['type']}, 연결도: {e['degree']})")
        lines.append("")

    if trends["type_distribution"]:
        lines.append("[신규 엔티티 유형]")
        for etype, count in trends["type_distribution"].items():
            lines.append(f"- {etype}: {count}")
        lines.append("")

    if trends["active_communities"]:
        lines.append("[활성 커뮤니티]")
        for c in trends["active_communities"][:10]:
            lines.append(
                f"- {c['label'][:60]} ({c['size']}노드, 신규+{c['new_entities']})"
            )
        lines.append("")

    top_stories = sorted(stories, key=lambda s: s.get("points", 0), reverse=True)[:20]
    if top_stories:
        lines.append("[상위 뉴스]")
        for s in top_stories:
            lines.append(
                f"- [{s.get('points', 0)}pts] {s['title']} ({s.get('source', '?')})"
            )
        lines.append("")

    return "\n".join(lines)


BRIEFING_PROMPT = (
    "너는 12시간 단위 기술 인텔리전스 분석가다. 연구자·엔지니어를 위한 브리핑을 작성하라.\n\n"
    "원칙:\n"
    "- 입력 리포트에 없는 사실 금지. 모든 주장에 리포트 내부 근거.\n"
    "- 유사 항목은 하나의 신호로 묶어라. 과장 대신 불확실성 명시.\n"
    "- '상승/약화' 방향성 표현은 증감 근거 있을 때만. 없으면 '단면 관측'.\n"
    "- 트렌드와 지식을 분리하라. 시끄러운 주제가 배울 게 많은 주제를 밀어내면 안 된다.\n\n"
    "점수 체계 (각 항목에 반드시 3축 점수를 붙여라):\n"
    "- 트렌드 점수(T): 커뮤니티에서 얼마나 뜨거운가 (1~5)\n"
    "- 지식 점수(K): 읽었을 때 얼마나 배움이 남는가 (1~5)\n"
    "- 연구 적합도(R): 논문/연구/시스템 이해로 연결될 가능성 (1~5)\n\n"
    "[출력 형식 — 반드시 이 구조, 이 순서를 따라라]\n\n"
    "# 0. 오늘 꼭 읽을 글 3개\n"
    "지식 점수(K)와 연구 적합도(R)가 가장 높은 글 3개를 선택하라.\n"
    "각 글:\n"
    "- 제목 + URL + 출처\n"
    "- 한줄 이유 (왜 이 글이 최우선인가)\n"
    "- T/K/R 점수\n\n"
    "# 1. 한 화면 요약\n"
    "진짜 변화만 3줄. 관측형 문장으로.\n\n"
    "# 2. 핵심 신호 (5개)\n"
    "각 항목:\n"
    "- **신호명**: / 분류: 신규|지속|이벤트성|잡음후보\n"
    "- T/K/R 점수\n"
    "- 근거: 엔티티, 커뮤니티, 뉴스 인용\n"
    "- 해석 + 불확실성\n"
    "- 실무 액션: 연구자 / 엔지니어 / 전략\n\n"
    "# 3. 장문 딥리드\n"
    "지식 점수(K) ≥ 4인 글을 최대 5개 선택하여 각각 상세 분석하라.\n"
    "각 글마다 반드시 아래 항목 전부 작성 (200~400자 이상):\n"
    "- **제목**: + URL\n"
    "- **T/K/R**: 점수\n"
    "- **왜 읽어야 하는가**:\n"
    "- **이 글이 답하는 핵심 질문**:\n"
    "- **읽고 나면 무엇을 배우는가**:\n"
    "- **누구에게 특히 유익한가**:\n"
    "- **기술 깊이**: 입문 / 중급 / 고급\n"
    "- **분류**: 트렌드성 / 지식성 / 혼합\n"
    "- **같이 봐야 할 1차 자료**: (있으면)\n\n"
    "# 4. 지식 노트\n"
    "## 4-1. 오늘 새로 등장한 개념 3개\n"
    "각각: 개념명, 정의, 왜 지금 등장했는가, 관련 글\n"
    "## 4-2. 꼭 알아야 할 배경 개념 3개\n"
    "이번 뉴스를 이해하려면 알아야 하는 기존 개념\n"
    "## 4-3. 도구/시스템 카드 3개\n"
    "이름, 한줄 설명, 주요 용도, 대안, URL\n"
    "## 4-4. 열린 연구 질문 3개\n"
    "이번 데이터에서 파생되는, 아직 답이 없는 질문\n"
    "## 4-5. 용어 정리\n"
    "이번 리포트에서 나온 전문 용어 5~8개: 용어 = 정의\n\n"
    "# 5. 다음 12시간 체크리스트\n"
    "검증 가능한 질문 7개 + 후속 수집 키워드 10개.\n\n"
    "---\n"
    "[입력 데이터]\n"
)


async def generate_intelligence_report(
    llm_client: Any,
    model_name: str,
    trends: dict[str, Any],
    stories: list[dict[str, Any]],
    run_time: str,
    stats: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    structured_input = _build_structured_input(trends, stories, stats)
    prompt = BRIEFING_PROMPT + structured_input

    try:
        resp = await llm_client.messages.create(
            model=model_name,
            max_tokens=6144,
            messages=[{"role": "user", "content": prompt}],
        )
        analysis = resp.content[0].text
    except Exception as exc:
        analysis = f"(LLM 분석 생성 실패: {exc})"

    header = (
        f"# 기술 트렌드 인텔리전스 브리핑\n"
        f"**생성**: {now_str} | **수집**: 최근 12시간 | **처리**: {run_time}\n"
        f"**데이터**: {stats.get('docs_collected', 0)}건, "
        f"+{trends['new_entities_count']} 엔티티, "
        f"{trends['total_communities']} 커뮤니티\n\n---\n\n"
    )

    full_report = (
        header + analysis + f"\n\n---\n*GAKMS Intelligence Report — {now_str}*"
    )

    deep_reads: list[dict[str, str]] = []
    if "# 3. 장문 딥리드" in analysis:
        section_start = analysis.index("# 3. 장문 딥리드")
        section_end = (
            analysis.index("# 4.")
            if "# 4." in analysis[section_start + 1 :]
            else len(analysis)
        )
        section_end = (
            analysis.index("# 4.", section_start + 1)
            if "# 4." in analysis[section_start + 1 :]
            else len(analysis)
        )
        deep_section = analysis[section_start:section_end].strip()
        articles = deep_section.split("- **제목**:")
        for art in articles[1:]:
            title_line = art.split("\n")[0].strip()
            title_clean = re.sub(r"\[|\]|\(http[^\)]*\)", "", title_line).strip()
            slug = re.sub(r"[^a-zA-Z0-9가-힣_-]+", "-", title_clean[:60]).strip("-")
            deep_reads.append(
                {
                    "title": title_clean,
                    "slug": slug,
                    "content": f"# 딥리드: {title_clean}\n\n- **제목**:{art.strip()}",
                }
            )

    return full_report, deep_reads


async def run_daily_pipeline(hours: int = 12):
    t_start = time.perf_counter()
    print("=" * 60)
    print(f"Daily News Pipeline — {datetime.now(tz=timezone.utc).isoformat()}")
    print("=" * 60)

    settings = Settings.load()
    hf_home = Path(__file__).resolve().parent.parent / ".cache" / "hf"
    hf_home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(hf_home)

    kg = KnowledgeGraph(settings.storage.graph_path)
    ts = TemporalFactStore(settings.storage.temporal_path)
    vs = VectorStore(
        persist_dir=settings.storage.vector_path,
        embedding_model=settings.embedding.model_name,
    )
    llm_client = create_llm_client()
    model_name = get_model_name()
    deduplicator = Deduplicator()
    relation_mapper = RelationMapper()
    parser = DocumentParser()

    prev_node_count = kg.graph.number_of_nodes()
    seen_ids = _load_seen_ids()

    print(f"  KB: {prev_node_count} entities, {kg.graph.number_of_edges()} relations")
    print(f"  Seen IDs: {len(seen_ids)}")

    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) GAKMS-DailyBot/1.0"}
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        hn, lob, devto, rss, reddit, gh = await asyncio.gather(
            fetch_recent_hn(session, hours=hours),
            fetch_recent_lobsters(session),
            fetch_recent_devto(session),
            fetch_rss_feeds(session),
            fetch_reddit(session),
            fetch_github_trending(session),
        )

    all_raw = hn + lob + devto + rss + reddit + gh
    new_stories: list[dict[str, Any]] = []
    for s in all_raw:
        if s["id"] in seen_ids:
            continue
        if s["title"].lower().strip() in {
            ss["title"].lower().strip() for ss in new_stories
        }:
            continue
        new_stories.append(s)
        seen_ids.add(s["id"])

    print(
        f"\n  Sources: HN={len(hn)}, Lobsters={len(lob)}, Dev.to={len(devto)}, "
        f"Reddit={len(reddit)}, GitHub={len(gh)}, RSS={len(rss)}"
    )
    print(f"  New (unseen): {len(new_stories)}")

    if not new_stories:
        print("  No new stories. Skipping.")
        _save_seen_ids(seen_ids)
        return

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        article_urls = [s["url"] for s in new_stories if s.get("url")][:100]
        sem = asyncio.Semaphore(10)

        async def _fetch(url):
            async with sem:
                return await fetch_article_text(session, url)

        article_texts = await asyncio.gather(*[_fetch(u) for u in article_urls])
    fetched = sum(1 for t in article_texts if t)
    print(f"  Article content: {fetched}/{len(article_urls)}")

    documents: list[dict[str, Any]] = []
    for i, story in enumerate(new_stories):
        text = f"Title: {story['title']}\nPoints: {story['points']}, Source: {story['source']}\n"
        if i < len(article_texts) and article_texts[i]:
            text += f"\n{article_texts[i][:3000]}\n"
        ts_val = story.get("created_at", 0)
        created = (
            datetime.fromtimestamp(ts_val, tz=timezone.utc)
            if ts_val
            else datetime.now(tz=timezone.utc)
        )
        documents.append(
            {
                "id": story["id"],
                "text": text,
                "title": story["title"],
                "url": story.get("url", ""),
                "source": story.get("source", "?"),
                "points": story.get("points", 0),
                "timestamp": created,
            }
        )

    all_entities: list[dict[str, Any]] = []
    all_relations: list[dict[str, Any]] = []
    extraction_sem = asyncio.Semaphore(5)

    async def _extract(doc: dict, text: str):
        try:
            prompt = KOREAN_PROMPT + text[:4000]
            async with extraction_sem:
                resp = await llm_client.messages.create(
                    model=model_name,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
            raw = resp.content[0].text
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return doc, {"entities": [], "relations": []}
            return doc, json.loads(m.group())
        except Exception:
            return doc, {"entities": [], "relations": []}

    print(f"\n  Extracting entities (vLLM, {len(documents)} docs)...")
    batch_size = 20
    for batch_start in range(0, len(documents), batch_size):
        batch = documents[batch_start : batch_start + batch_size]
        tasks = [_extract(d, d["text"]) for d in batch if len(d["text"].strip()) >= 50]
        if not tasks:
            continue
        results = await asyncio.gather(*tasks)

        for doc_info, result in results:
            text_lower = doc_info["text"].lower()
            for ent in result.get("entities", []):
                if isinstance(ent, str):
                    ent = {"name": ent, "type": "CONCEPT", "description": ent}
                if not isinstance(ent, dict):
                    continue
                name = str(ent.get("name", "")).strip()
                if not name or name.lower() not in text_lower:
                    continue
                ent["source_doc"] = doc_info["id"]
                all_entities.append(ent)

            grounded = {
                e["name"] for e in all_entities if e.get("source_doc") == doc_info["id"]
            }
            for rel in result.get("relations", []):
                if not isinstance(rel, dict):
                    continue
                if (
                    str(rel.get("source", "")) in grounded
                    and str(rel.get("target", "")) in grounded
                ):
                    all_relations.append(rel)

        done = min(batch_start + batch_size, len(documents))
        if done % 100 == 0 or done == len(documents):
            print(f"    {done}/{len(documents)} — {len(all_entities)} entities")

    co_occur = relation_mapper.infer_co_occurrence(all_entities)
    all_relations.extend(co_occur)
    deduped = deduplicator.deduplicate(all_entities, all_relations)
    deduped_entities = deduped.get("entities", [])
    deduped_relations = deduped.get("relations", [])
    print(
        f"  Deduped: {len(deduped_entities)} entities, {len(deduped_relations)} relations"
    )

    graph_stats = kg.incremental_update(
        entities=deduped_entities,
        relations=deduped_relations,
        source_doc="daily_pipeline",
        timestamp=datetime.now(tz=timezone.utc),
    )
    print(
        f"  Graph: +{graph_stats['nodes_added']} nodes, +{graph_stats['edges_added']} edges"
    )

    batch_items = []
    for doc in documents:
        chunks = parser._chunk_text(doc["text"])
        for ci, chunk in enumerate(chunks):
            batch_items.append(
                (
                    f"{doc['id']}_chunk_{ci}",
                    chunk,
                    {
                        "source": doc["source"],
                        "title": doc["title"],
                        "timestamp": doc["timestamp"].isoformat(),
                    },
                )
            )
    await vs.upsert_batch(batch_items)
    print(f"  Vectors: {len(batch_items)} chunks")

    now = datetime.now(tz=timezone.utc)
    for ent in deduped_entities:
        name = ent.get("name", "")
        if name:
            ts.add_fact(
                TemporalFact(
                    entity=name,
                    attribute="entity_type",
                    value=ent.get("type", "unknown"),
                    source_doc="daily_pipeline",
                    valid_from=now,
                )
            )

    doc_dir = Path("knowledge_base/documents")
    doc_dir.mkdir(parents=True, exist_ok=True)
    for doc in documents:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", doc["title"][:50].lower()).strip("-")
        ts_str = doc["timestamp"].strftime("%Y%m%d_%H%M%S")
        filepath = doc_dir / f"{ts_str}_{slug}.md"
        if not filepath.exists():
            filepath.write_text(
                f"---\ntitle: {doc['title']}\nsource: {doc['source']}\nurl: {doc.get('url', '')}\npoints: {doc['points']}\n---\n\n{doc['text']}",
                encoding="utf-8",
            )

    _save_seen_ids(seen_ids)

    new_entity_names = {e.get("name", "") for e in deduped_entities}
    trends = detect_trends(kg, new_entity_names, prev_node_count)

    elapsed = time.perf_counter() - t_start
    run_time = f"{elapsed:.0f}초"

    print("\n  Generating intelligence report (LLM)...")
    report, deep_reads = await generate_intelligence_report(
        llm_client=llm_client,
        model_name=model_name,
        trends=trends,
        stories=new_stories,
        run_time=run_time,
        stats={"docs_collected": len(new_stories)},
    )

    report_dir = Path("knowledge_base/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    ts_slug = now.strftime("%Y-%m-%d_%H%M")
    report_path = report_dir / f"{ts_slug}_intelligence_brief.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n  Report: {report_path}")

    if deep_reads:
        deepread_dir = report_dir / "deep_reads"
        deepread_dir.mkdir(parents=True, exist_ok=True)
        for dr in deep_reads:
            dr_path = deepread_dir / f"{ts_slug}_{dr['slug'][:40]}.md"
            dr_path.write_text(dr["content"], encoding="utf-8")
            print(f"  Deep read: {dr_path.name}")

    from config.notification import notify_all

    notif_results = notify_all(
        settings,
        report,
        report_title=f"📰 기술 인텔리전스 — {now.strftime('%Y-%m-%d %H:%M')}",
    )
    for channel, status in notif_results.items():
        print(f"  Notification [{channel}]: {status}")

    print(f"\n{'=' * 60}")
    print(report)
    print(f"{'=' * 60}")
    print(f"  Completed in {run_time}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=int, default=12, help="hours to look back")
    args = p.parse_args()
    asyncio.run(run_daily_pipeline(hours=args.hours))
