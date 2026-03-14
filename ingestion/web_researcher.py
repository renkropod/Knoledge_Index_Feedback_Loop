from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
import logging
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import aiohttp
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    topic: str
    text: str
    sources: list[dict[str, str]]
    timestamp: datetime


class WebResearcher:
    def __init__(self, llm_client: Any = None, max_sources: int = 10):
        self.llm_client = llm_client
        self.max_sources = max_sources
        self._request_timeout = aiohttp.ClientTimeout(total=30)
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        }
        self._semaphore = asyncio.Semaphore(5)

    async def research(
        self,
        topic: str,
        existing_knowledge: str = "",
        max_sources: int | None = None,
    ) -> ResearchResult:
        target_sources = max_sources or self.max_sources
        queries = await self._generate_search_queries(topic, existing_knowledge)
        if not queries:
            queries = [topic]

        collected_sources: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        async with aiohttp.ClientSession(
            timeout=self._request_timeout, headers=self._headers
        ) as session:
            search_tasks = [
                self._search_query(session, query, target_sources) for query in queries
            ]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            for result in search_results:
                if isinstance(result, Exception):
                    LOGGER.warning("Search query failed: %s", result)
                    continue

                for source in result:
                    url = source.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    collected_sources.append(source)
                    if len(collected_sources) >= target_sources:
                        break

                if len(collected_sources) >= target_sources:
                    break

            content_tasks = [
                self._fetch_url(source["url"], session=session)
                for source in collected_sources
            ]
            contents = await asyncio.gather(*content_tasks, return_exceptions=True)

        compiled_parts: list[str] = []
        filtered_sources: list[dict[str, str]] = []
        for source, content in zip(collected_sources, contents):
            if isinstance(content, Exception):
                LOGGER.warning(
                    "Failed to fetch source %s: %s", source.get("url", ""), content
                )
                continue

            clean_content = content.strip()
            if not clean_content:
                continue

            filtered_sources.append(source)
            excerpt = clean_content[:4000]
            compiled_parts.append(
                "\n".join(
                    [
                        f"Title: {source.get('title', '')}",
                        f"URL: {source.get('url', '')}",
                        f"Snippet: {source.get('snippet', '')}",
                        f"Content:\n{excerpt}",
                    ]
                )
            )

        combined_text = "\n\n---\n\n".join(compiled_parts)
        return ResearchResult(
            topic=topic,
            text=combined_text,
            sources=filtered_sources,
            timestamp=datetime.now(timezone.utc),
        )

    async def _fetch_url(
        self,
        url: str,
        session: aiohttp.ClientSession | None = None,
    ) -> str:
        if session is not None:
            return await self._fetch_url_with_session(session, url)

        async with aiohttp.ClientSession(
            timeout=self._request_timeout, headers=self._headers
        ) as own_session:
            return await self._fetch_url_with_session(own_session, url)

    async def _generate_search_queries(
        self, topic: str, existing_knowledge: str
    ) -> list[str]:
        if self.llm_client is None:
            return [topic]

        if hasattr(self.llm_client, "generate_search_queries"):
            try:
                response = self.llm_client.generate_search_queries(
                    topic, existing_knowledge
                )
                if inspect.isawaitable(response):
                    response = await response
                return self._normalize_queries(response, topic)
            except Exception as exc:
                LOGGER.warning("LLM query generation failed: %s", exc)

        return [topic]

    async def _search_query(
        self,
        session: aiohttp.ClientSession,
        query: str,
        max_results: int,
    ) -> list[dict[str, str]]:
        encoded_query = quote_plus(query)
        search_url = f"https://duckduckgo.com/html/?q={encoded_query}"

        html = await self._fetch_url_with_session(session, search_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []

        for card in soup.select(".result"):
            link = card.select_one("a.result__a")
            snippet_node = card.select_one(".result__snippet")
            if not link:
                continue

            raw_href = link.get("href", "").strip()
            url = self._normalize_result_url(raw_href)
            if not url:
                continue

            title = link.get_text(" ", strip=True)
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
            results.append({"url": url, "title": title, "snippet": snippet})

            if len(results) >= max_results:
                break

        return results

    async def _fetch_url_with_session(
        self, session: aiohttp.ClientSession, url: str
    ) -> str:
        try:
            async with self._semaphore:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status >= 400:
                        LOGGER.warning("HTTP %s for %s", response.status, url)
                        return ""

                    content_type = response.headers.get("Content-Type", "")
                    body = await response.text(errors="ignore")
                    if "html" not in content_type:
                        return body.strip()

                    return self._extract_main_text(body)
        except asyncio.TimeoutError:
            LOGGER.warning("Timeout while fetching %s", url)
        except aiohttp.ClientError as exc:
            LOGGER.warning("Connection error while fetching %s: %s", url, exc)
        except Exception as exc:
            LOGGER.warning("Unexpected fetch error for %s: %s", url, exc)
        return ""

    @staticmethod
    def _extract_main_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag_name in [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "aside",
            "form",
            "svg",
        ]:
            for node in soup.find_all(tag_name):
                node.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines)

    @staticmethod
    def _normalize_result_url(url: str) -> str:
        if not url:
            return ""

        parsed = urlparse(url)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            query_map = parse_qs(parsed.query)
            if "uddg" in query_map and query_map["uddg"]:
                return unquote(query_map["uddg"][0])

        if parsed.scheme in {"http", "https"}:
            return url

        return ""

    @staticmethod
    def _normalize_queries(raw: Any, topic: str) -> list[str]:
        if raw is None:
            return [topic]

        queries: list[str] = []
        if isinstance(raw, str):
            for line in raw.splitlines():
                value = line.strip(" -*\t")
                if value:
                    queries.append(value)
        elif isinstance(raw, list):
            for item in raw:
                if item is None:
                    continue
                value = str(item).strip()
                if value:
                    queries.append(value)
        else:
            value = str(raw).strip()
            if value:
                queries.append(value)

        deduped: list[str] = []
        seen: set[str] = set()
        for query in [topic, *queries]:
            key = query.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(query)

        return deduped or [topic]
