from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(slots=True)
class LLMSettings:
    api_key_env: str
    extraction_model: str
    generation_model: str


@dataclass(slots=True)
class StorageSettings:
    graph_path: str
    vector_path: str
    temporal_path: str


@dataclass(slots=True)
class EmbeddingSettings:
    model_name: str
    device: str


@dataclass(slots=True)
class ResearchSettings:
    default_topics: list[str]
    max_sources: int
    schedule_cron: str


@dataclass(slots=True)
class Settings:
    llm: LLMSettings
    storage: StorageSettings
    embedding: EmbeddingSettings
    research: ResearchSettings

    @property
    def llm_api_key(self) -> str | None:
        return os.getenv(self.llm.api_key_env)

    @classmethod
    def load(
        cls,
        settings_path: str | Path | None = None,
        env_path: str | Path | None = None,
    ) -> "Settings":
        config_file = (
            Path(settings_path)
            if settings_path
            else Path(__file__).with_name("settings.yaml")
        )
        dotenv_file = Path(env_path) if env_path else config_file.parent.parent / ".env"

        load_dotenv(dotenv_path=dotenv_file, override=False)

        with config_file.open("r", encoding="utf-8") as fh:
            raw_config = yaml.safe_load(fh) or {}

        llm_raw = raw_config.get("llm", {})
        storage_raw = raw_config.get("storage", {})
        embedding_raw = raw_config.get("embedding", {})
        research_raw = raw_config.get("research", {})

        llm = LLMSettings(
            api_key_env=_env_str(
                "GAKMS_LLM_API_KEY_ENV", llm_raw.get("api_key_env", "ANTHROPIC_API_KEY")
            ),
            extraction_model=_env_str(
                "GAKMS_LLM_EXTRACTION_MODEL",
                llm_raw.get("extraction_model", "claude-3-5-sonnet-20241022"),
            ),
            generation_model=_env_str(
                "GAKMS_LLM_GENERATION_MODEL",
                llm_raw.get("generation_model", "claude-sonnet-4-20250514"),
            ),
        )

        storage = StorageSettings(
            graph_path=_env_str(
                "GAKMS_STORAGE_GRAPH_PATH",
                storage_raw.get("graph_path", "knowledge_base/graph/kg.json"),
            ),
            vector_path=_env_str(
                "GAKMS_STORAGE_VECTOR_PATH",
                storage_raw.get("vector_path", "knowledge_base/vectors"),
            ),
            temporal_path=_env_str(
                "GAKMS_STORAGE_TEMPORAL_PATH",
                storage_raw.get("temporal_path", "knowledge_base/temporal/facts.jsonl"),
            ),
        )

        embedding = EmbeddingSettings(
            model_name=_env_str(
                "GAKMS_EMBEDDING_MODEL_NAME",
                embedding_raw.get("model_name", "BAAI/bge-m3"),
            ),
            device=_env_str(
                "GAKMS_EMBEDDING_DEVICE", embedding_raw.get("device", "cpu")
            ),
        )

        research = ResearchSettings(
            default_topics=_env_list(
                "GAKMS_RESEARCH_DEFAULT_TOPICS",
                research_raw.get(
                    "default_topics",
                    [
                        "AI governance",
                        "retrieval-augmented generation",
                        "autonomous research agents",
                    ],
                ),
            ),
            max_sources=_env_int(
                "GAKMS_RESEARCH_MAX_SOURCES", research_raw.get("max_sources", 15)
            ),
            schedule_cron=_env_str(
                "GAKMS_RESEARCH_SCHEDULE_CRON",
                research_raw.get("schedule_cron", "0 */6 * * *"),
            ),
        )

        return cls(llm=llm, storage=storage, embedding=embedding, research=research)


def _env_str(key: str, default: Any) -> str:
    value = os.getenv(key)
    if value is None:
        return str(default)
    value = value.strip()
    return value if value else str(default)


def _env_int(key: str, default: Any) -> int:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return int(default)
    return int(value)


def _env_list(key: str, default: Any) -> list[str]:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        if isinstance(default, list):
            return [str(item) for item in default]
        return [str(default)]
    return [item.strip() for item in value.split(",") if item.strip()]
