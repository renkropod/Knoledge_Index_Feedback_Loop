from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Callable

import yaml

from .document_parser import ParsedDocument
from .web_researcher import WebResearcher


LOGGER = logging.getLogger(__name__)


@dataclass
class PipelinePayload:
    topic: str
    research_text: str
    sources: list[dict[str, str]]
    parsed_document: ParsedDocument


class ResearchScheduler:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config(self.config_path)

        research_cfg = self.config.get("research", {})
        self.default_topics = list(research_cfg.get("default_topics", []))
        self.default_cron = str(research_cfg.get("schedule_cron", "0 6 * * *"))
        self.max_sources = int(research_cfg.get("max_sources", 10))

        asyncio_scheduler = importlib.import_module("apscheduler.schedulers.asyncio")
        self.scheduler = asyncio_scheduler.AsyncIOScheduler()
        self.web_researcher = WebResearcher(max_sources=self.max_sources)
        self.pipeline_handler: Callable[[PipelinePayload], Any] | None = None
        self._jobs_by_topic: dict[str, str] = {}

        for topic in self.default_topics:
            self.add_topic(topic, self.default_cron)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            LOGGER.info("Research scheduler started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            LOGGER.info("Research scheduler stopped")

    def add_topic(self, topic: str, cron_expression: str = "0 6 * * *"):
        clean_topic = topic.strip()
        if not clean_topic:
            raise ValueError("topic cannot be empty")

        if clean_topic in self._jobs_by_topic:
            self.remove_topic(clean_topic)

        trigger = self._cron_to_trigger(cron_expression)
        job_id = self._make_job_id(clean_topic)
        self.scheduler.add_job(
            self._run_research,
            trigger=trigger,
            args=[clean_topic],
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        self._jobs_by_topic[clean_topic] = job_id

    def remove_topic(self, topic: str):
        clean_topic = topic.strip()
        job_id = self._jobs_by_topic.pop(clean_topic, None)
        if not job_id:
            return

        try:
            self.scheduler.remove_job(job_id)
        except Exception as exc:
            LOGGER.warning("Failed to remove schedule for %s: %s", clean_topic, exc)

    def list_schedules(self) -> list[dict[str, Any]]:
        schedules: list[dict[str, Any]] = []
        for topic, job_id in self._jobs_by_topic.items():
            job = self.scheduler.get_job(job_id)
            if job is None:
                continue

            schedules.append(
                {
                    "topic": topic,
                    "job_id": job.id,
                    "cron": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                }
            )

        return sorted(schedules, key=lambda item: item["topic"].lower())

    async def _run_research(self, topic: str):
        LOGGER.info("Starting research cycle for topic: %s", topic)

        result = await self.web_researcher.research(topic, max_sources=self.max_sources)
        parsed = ParsedDocument(
            title=topic,
            content=result.text,
            metadata={
                "source_path": "web",
                "format": "web_research",
                "parsed_at": result.timestamp.isoformat(),
                "word_count": len(result.text.split()),
            },
            chunks=self._chunk_research_text(result.text),
        )

        payload = PipelinePayload(
            topic=topic,
            research_text=result.text,
            sources=result.sources,
            parsed_document=parsed,
        )

        if self.pipeline_handler is None:
            LOGGER.info(
                "No pipeline handler attached for topic '%s'. "
                "Attach ResearchScheduler.pipeline_handler for extraction/storage integration.",
                topic,
            )
            return

        try:
            maybe_awaitable = self.pipeline_handler(payload)
            if inspect.isawaitable(maybe_awaitable):
                await maybe_awaitable
        except Exception as exc:
            LOGGER.exception("Research pipeline failed for topic %s: %s", topic, exc)

    @staticmethod
    def _load_config(config_path: Path) -> dict[str, Any]:
        if not config_path.is_absolute():
            base_dir = Path(__file__).resolve().parents[1]
            config_path = base_dir / config_path

        if not config_path.exists():
            return {}

        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return data or {}

    @staticmethod
    def _cron_to_trigger(cron_expression: str):
        cron_mod = importlib.import_module("apscheduler.triggers.cron")
        try:
            return cron_mod.CronTrigger.from_crontab(cron_expression)
        except ValueError as exc:
            raise ValueError(f"Invalid cron expression: {cron_expression}") from exc

    @staticmethod
    def _make_job_id(topic: str) -> str:
        digest = hashlib.sha1(topic.encode("utf-8")).hexdigest()[:12]
        return f"research-{digest}"

    @staticmethod
    def _chunk_research_text(
        text: str, chunk_size: int = 2000, overlap: int = 200
    ) -> list[str]:
        if not text.strip():
            return []

        chunks: list[str] = []
        step = max(1, chunk_size - overlap)
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start += step

        return chunks
