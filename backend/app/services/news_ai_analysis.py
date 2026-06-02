"""Generate and serve scheduled AI analysis for News Center."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.db.repositories import news_ai as news_ai_repository
from backend.app.services.config import (
    AI_ANALYSIS_ENABLED,
    AI_ANALYSIS_MAX_NEWS,
    AI_API_BASE,
    AI_API_KEY,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_NUM_RETRIES,
    AI_TEMPERATURE,
    AI_TIMEOUT_SECONDS,
)
from backend.app.services.news_ai_timeline import SHANGHAI_TZ, resolve_due_nodes
from backend.app.services.news_r2 import get_analysis_items, refresh_snapshot


PROMPT_PATH = Path("backend/config/ai_analysis_prompt.txt")
INTERESTS_PATH = Path("backend/config/ai_interests.txt")
CONTENT_KEYS = (
    "core_trends",
    "sentiment_controversy",
    "signals",
    "outlook_strategy",
)


def run_due_analyses(now: datetime | None = None) -> dict[str, Any]:
    """Generate reports for timeline nodes matching the current minute."""

    if not AI_ANALYSIS_ENABLED:
        return {"status": "disabled", "reason": "AI_ANALYSIS_ENABLED is false"}

    current_time = now or datetime.now(timezone.utc)
    trading_day, nodes = resolve_due_nodes(current_time)
    if not nodes:
        return {
            "status": "idle",
            "calendar_degraded": trading_day.degraded,
            "runs": [],
        }

    runs = []
    for node in nodes:
        if news_ai_repository.has_run(_execution_date(current_time), node.key, node.scheduled_time):
            runs.append({"node": node.key, "status": "already_executed"})
            continue
        runs.append(
            run_analysis(
                node_key=node.key,
                scheduled_time=node.scheduled_time,
                analysis_mode=node.analysis_mode,
                execution_time=current_time,
                calendar_degraded=trading_day.degraded,
            )
        )
    return {
        "status": "ready",
        "calendar_degraded": trading_day.degraded,
        "runs": runs,
    }


def run_analysis(
    *,
    node_key: str,
    scheduled_time: str,
    analysis_mode: str,
    execution_time: datetime,
    calendar_degraded: bool,
) -> dict[str, Any]:
    """Generate one report or record why generation was skipped."""

    started_at = _aware_datetime(execution_time)
    snapshot_key: str | None = None
    snapshot_etag: str | None = None
    try:
        snapshot, items = get_analysis_items(analysis_mode, AI_ANALYSIS_MAX_NEWS)
        snapshot_key = snapshot.key
        snapshot_etag = snapshot.etag
        if news_ai_repository.has_analysis(snapshot.key, snapshot.etag, analysis_mode):
            status = "skipped_unchanged_snapshot"
            _record_run(
                execution_time=started_at,
                node_key=node_key,
                scheduled_time=scheduled_time,
                analysis_mode=analysis_mode,
                status=status,
                snapshot_key=snapshot.key,
                snapshot_etag=snapshot.etag,
                calendar_degraded=calendar_degraded,
            )
            return {"node": node_key, "status": status}

        content = generate_analysis(
            node_key=node_key,
            analysis_mode=analysis_mode,
            snapshot=snapshot,
            items=items,
        )
        generated_at = datetime.now(timezone.utc)
        news_ai_repository.insert_analysis(
            {
                "snapshot_key": snapshot.key,
                "snapshot_etag": snapshot.etag,
                "snapshot_date": date_from_iso(snapshot.snapshot_date),
                "snapshot_crawl_time": snapshot.crawl_time,
                "node_key": node_key,
                "analysis_mode": analysis_mode,
                "model": AI_MODEL,
                "content": content,
                "analyzed_news": len(items),
                "generated_at": generated_at,
            }
        )
        _record_run(
            execution_time=started_at,
            node_key=node_key,
            scheduled_time=scheduled_time,
            analysis_mode=analysis_mode,
            status="succeeded",
            snapshot_key=snapshot.key,
            snapshot_etag=snapshot.etag,
            calendar_degraded=calendar_degraded,
            finished_at=generated_at,
        )
        return {"node": node_key, "status": "succeeded", "analyzed_news": len(items)}
    except Exception as error:  # pylint: disable=broad-exception-caught
        _record_run(
            execution_time=started_at,
            node_key=node_key,
            scheduled_time=scheduled_time,
            analysis_mode=analysis_mode,
            status="failed",
            snapshot_key=snapshot_key,
            snapshot_etag=snapshot_etag,
            calendar_degraded=calendar_degraded,
            error=str(error),
        )
        return {"node": node_key, "status": "failed", "error": str(error)}


def generate_analysis(
    *,
    node_key: str,
    analysis_mode: str,
    snapshot,
    items: list[dict[str, Any]],
) -> dict[str, str]:
    """Call LiteLLM and validate the four-section JSON response."""

    if not AI_API_KEY:
        raise RuntimeError("AI_API_KEY is not configured")
    system_prompt, user_template = load_prompt_template()
    user_prompt = (
        user_template.replace("{analysis_mode}", analysis_mode)
        .replace("{node_key}", node_key)
        .replace("{snapshot_date}", snapshot.snapshot_date)
        .replace("{snapshot_crawl_time}", snapshot.crawl_time)
        .replace("{platforms}", ", ".join(sorted({item["source_name"] for item in items})))
        .replace("{interests}", INTERESTS_PATH.read_text(encoding="utf-8"))
        .replace("{news_content}", format_news_items(items))
    )
    response = call_model(system_prompt, user_prompt)
    return parse_analysis_content(response)


def get_latest_analysis() -> dict[str, Any]:
    """Return the latest successful report without invoking a model."""

    try:
        row = news_ai_repository.fetch_latest_analysis()
    except Exception as error:  # pylint: disable=broad-exception-caught
        return {"status": "unavailable", "message": str(error), "data": None}
    if row is None:
        return {"status": "waiting", "data": None}

    stale = True
    try:
        snapshot = refresh_snapshot()
        stale = row["snapshot_key"] != snapshot.key or row["snapshot_etag"] != snapshot.etag
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    return {
        "status": "ready",
        "source": "news_collector.r2.ai",
        "stale": stale,
        "data": {
            **row["content"],
            "node_key": row["node_key"],
            "analysis_mode": row["analysis_mode"],
            "model": row["model"],
            "snapshot_date": row["snapshot_date"],
            "snapshot_crawl_time": row["snapshot_crawl_time"],
            "generated_at": row["generated_at"],
            "analyzed_news": row["analyzed_news"],
        },
    }


def call_model(system_prompt: str, user_prompt: str) -> str:
    """Invoke LiteLLM using the configured OpenAI-compatible model."""

    import litellm  # pylint: disable=import-error,import-outside-toplevel

    kwargs: dict[str, Any] = {
        "model": AI_MODEL,
        "api_key": AI_API_KEY,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "timeout": AI_TIMEOUT_SECONDS,
        "temperature": AI_TEMPERATURE,
        "num_retries": AI_NUM_RETRIES,
    }
    if AI_API_BASE:
        kwargs["api_base"] = AI_API_BASE
    if AI_MAX_TOKENS > 0:
        kwargs["max_tokens"] = AI_MAX_TOKENS
    response = litellm.completion(**kwargs)
    return str(response.choices[0].message.content or "")


def load_prompt_template() -> tuple[str, str]:
    """Read the local two-part prompt template."""

    content = PROMPT_PATH.read_text(encoding="utf-8")
    system_marker = "[system]"
    user_marker = "[user]"
    if system_marker not in content or user_marker not in content:
        raise ValueError("AI analysis prompt must include [system] and [user]")
    system_prompt, user_prompt = content.split(user_marker, 1)
    return system_prompt.replace(system_marker, "", 1).strip(), user_prompt.strip()


def format_news_items(items: list[dict[str, Any]]) -> str:
    """Render snapshot items compactly while retaining quantitative context."""

    lines = []
    for item in items:
        timeline = " -> ".join(
            f"{point['time']}:{point['rank'] if point['rank'] is not None else 'off'}"
            for point in item.get("rank_timeline", [])
        )
        lines.append(
            f"[{item['source_name']}] #{item['rank']} {item['title']} "
            f"| crawls={item.get('crawl_count', 1)} | timeline={timeline or 'none'}"
        )
    return "\n".join(lines)


def parse_analysis_content(raw_response: str) -> dict[str, str]:
    """Parse and constrain the JSON returned by the model."""

    text = raw_response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("AI analysis response must be a JSON object")
    return {key: str(payload.get(key) or "") for key in CONTENT_KEYS}


def date_from_iso(value: str):
    """Convert snapshot dates lazily to keep serialization helpers simple."""

    from datetime import date  # pylint: disable=import-outside-toplevel,redefined-outer-name

    return date.fromisoformat(value)


def _record_run(
    *,
    execution_time: datetime,
    node_key: str,
    scheduled_time: str,
    analysis_mode: str,
    status: str,
    snapshot_key: str | None,
    snapshot_etag: str | None,
    calendar_degraded: bool,
    error: str | None = None,
    finished_at: datetime | None = None,
) -> None:
    # pylint: disable=too-many-arguments
    news_ai_repository.record_run(
        {
            "execution_date": _execution_date(execution_time),
            "node_key": node_key,
            "scheduled_time": scheduled_time,
            "analysis_mode": analysis_mode,
            "status": status,
            "snapshot_key": snapshot_key,
            "snapshot_etag": snapshot_etag,
            "calendar_degraded": calendar_degraded,
            "error": error,
            "started_at": execution_time,
            "finished_at": finished_at or datetime.now(timezone.utc),
        }
    )


def _aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _execution_date(value: datetime):
    return _aware_datetime(value).astimezone(SHANGHAI_TZ).date()
