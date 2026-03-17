from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def send_discord(webhook_url: str, report_markdown: str, title: str = "") -> bool:
    if not webhook_url:
        return False

    chunks = _split_discord_chunks(report_markdown)

    for i, chunk in enumerate(chunks):
        embed: dict[str, Any] = {
            "description": chunk,
            "color": 0x5865F2,
        }
        if i == 0 and title:
            embed["title"] = title[:256]
        if i == len(chunks) - 1:
            embed["footer"] = {
                "text": f"GAKMS • {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            }

        payload = json.dumps({"embeds": [embed]}).encode("utf-8")
        req = Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                if resp.status not in (200, 204):
                    return False
        except Exception:
            return False

    return True


def _split_discord_chunks(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    lines = text.split("\n")
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_len and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def save_to_obsidian(
    vault_path: str,
    folder: str,
    report_markdown: str,
    filename: str = "",
) -> str:
    if not vault_path:
        return ""

    vault = Path(vault_path)
    if not vault.exists():
        return ""

    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        now = datetime.now(tz=timezone.utc)
        filename = f"{now.strftime('%Y-%m-%d_%H%M')}_Tech_Trends.md"

    filepath = target_dir / filename
    filepath.write_text(report_markdown, encoding="utf-8")
    return str(filepath)


def notify_all(
    settings: Any,
    report_markdown: str,
    report_title: str = "",
) -> dict[str, str]:
    results: dict[str, str] = {}

    if not hasattr(settings, "notification"):
        return results

    notif = settings.notification

    webhook_url = getattr(notif, "discord_webhook_url", "")
    if webhook_url:
        ok = send_discord(webhook_url, report_markdown, title=report_title)
        results["discord"] = "sent" if ok else "failed"

    vault_path = getattr(notif, "obsidian_vault_path", "")
    obs_folder = getattr(notif, "obsidian_folder", "Tech Trends")
    if vault_path:
        path = save_to_obsidian(vault_path, obs_folder, report_markdown)
        results["obsidian"] = path if path else "vault not found"

    return results
