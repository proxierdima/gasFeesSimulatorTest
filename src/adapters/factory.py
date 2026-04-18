from __future__ import annotations

from ..models import AppSettings
from .base import BaseAdapter
from .command import CommandAdapter
from .mock import MockAdapter


def create_adapter(mode: str, settings: AppSettings) -> BaseAdapter:
    normalized = (mode or settings.adapter_mode or "mock").lower()
    if normalized == "mock":
        return MockAdapter(settings)
    if normalized == "command":
        return CommandAdapter(settings)
    raise ValueError(f"Unsupported adapter mode: {mode}")
