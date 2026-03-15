#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Settings


def main():
    settings = Settings.load()
    cron_expr = settings.research.schedule_cron
    topics = settings.research.default_topics

    hf_home = os.environ.get("HF_HOME", "")
    if not hf_home:
        cache_dir = Path(__file__).resolve().parent.parent / ".cache" / "hf"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(cache_dir)

    print(f"GAKMS Research Scheduler")
    print(f"  Cron: {cron_expr}")
    print(f"  Topics: {', '.join(topics)}")

    try:
        from ingestion.scheduler import ResearchScheduler

        scheduler = ResearchScheduler(config_path="config/settings.yaml")
        scheduler.start()
        print(f"  Scheduler running. Press Ctrl+C to stop.\n")
        asyncio.get_event_loop().run_forever()
    except ImportError:
        print("  APScheduler not available. Running single execution.")
        from scripts.daily_research import daily_pipeline

        asyncio.run(daily_pipeline(topics))
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
