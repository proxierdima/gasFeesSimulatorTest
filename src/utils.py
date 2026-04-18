from __future__ import annotations

import json
import re
import shlex
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, TypeVar

T = TypeVar("T")
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp_slug() -> str:
    return now_utc().strftime("%Y-%m-%d_%H-%M-%S")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def json_dump(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, default=str)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "run"


def shell_context(raw: Dict[str, Any]) -> Dict[str, str]:
    import sys

    ctx: Dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            value = ""
        if not isinstance(value, str):
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            else:
                value = str(value)
        ctx[key] = value

        # On Windows, use simpler quoting to avoid over-escaping
        if sys.platform == "win32":
            # Only quote if the value contains spaces or special characters
            if " " in value or any(c in value for c in "&|<>^"):
                ctx[f"{key}_sh"] = f'"{value}"'
            else:
                ctx[f"{key}_sh"] = value
        else:
            ctx[f"{key}_sh"] = shlex.quote(value)
    return ctx


def expand_template(template: str, raw_context: Dict[str, Any]) -> str:
    ctx = shell_context(raw_context)
    command = template.format(**ctx)
    for key, value in ctx.items():
        command = command.replace(f"{{{{{key}}}}}", value)
        command = command.replace(f"{{{key}}}", value)
    unresolved = sorted(set(_PLACEHOLDER_RE.findall(command)))
    if unresolved:
        raise KeyError(
            f"Unresolved placeholders in command template: {', '.join(unresolved)}"
        )
    return command


def retry_call(
    fn: Callable[[], T], retries: int, backoff_seconds: float
) -> Tuple[T, int]:
    attempts = 0
    last_error: Exception | None = None
    while attempts < max(1, retries):
        attempts += 1
        try:
            return fn(), attempts
        except (
            Exception
        ) as exc:  # pragma: no cover - exercised in command tests manually
            last_error = exc
            if attempts >= max(1, retries):
                break
            time.sleep(backoff_seconds * attempts)
    assert last_error is not None
    raise last_error


def mask_private_key(value: str) -> str:
    if not value:
        return value
    return f"***{value[-6:]}"
