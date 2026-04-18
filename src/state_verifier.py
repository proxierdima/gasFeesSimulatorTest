from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .adapters.base import BaseAdapter
from .models import Scenario


def verify_state(adapter: BaseAdapter, scenario: Scenario, contract_address: str | None, network: str | None = None) -> tuple[bool | None, dict[str, Any] | None, str]:
    check = scenario.expect.state_check
    if not check.enabled:
        return None, None, "state_check_disabled"
    if not contract_address:
        return None, None, "missing_contract_address"
    if not check.function_name:
        return None, None, "missing_state_function"

    payload = adapter.read_state(contract_address, check.function_name, check.args, network=network)
    candidate = payload.get("value")
    if candidate is None and "result" in payload:
        candidate = payload.get("result")
    matched = candidate == check.expected
    note = "state_match" if matched else f"state_mismatch expected={check.expected!r} actual={candidate!r}"
    return matched, payload, note
