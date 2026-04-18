from __future__ import annotations

import hashlib
import random
import threading
import uuid
from typing import Any, Dict

from ..models import AppSettings, Scenario, SubmissionResult
from ..utils import now_utc
from .base import BaseAdapter


class MockAdapter(BaseAdapter):
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._lock = threading.Lock()
        self._rng = random.Random(settings.random_seed)
        self._tx_store: Dict[str, Dict[str, Any]] = {}
        self._state: Dict[str, Dict[str, Any]] = {}

    def _required_gas(self, scenario: Scenario) -> int:
        required = scenario.behavior.base_required_gas
        if scenario.behavior.appeal_like:
            required += 20
        if scenario.behavior.nondeterministic:
            required += 5
        if scenario.kind == "deploy":
            required += 10
        return required

    def _outcome(self, scenario: Scenario, gaslimit: int) -> Dict[str, Any]:
        required = self._required_gas(scenario)
        tx_seed = f"{scenario.name}:{gaslimit}:{scenario.behavior.nondeterministic}:{scenario.behavior.force_revert}"
        fingerprint = int(hashlib.sha256(tx_seed.encode("utf-8")).hexdigest(), 16)
        borderline_flip = (fingerprint % 2) == 0

        if scenario.behavior.force_revert:
            return {
                "final_status": "FINALIZED",
                "execution_result": "FINISHED_WITH_ERROR",
                "result_code": 1,
                "stderr": "Simulated contract revert",
                "genvm_log": ["revert() called in mock adapter"],
                "gas_used": min(gaslimit, required),
                "success": False,
                "out_of_fee": False,
            }

        if gaslimit < self.settings.gas_thresholds.fail_below or gaslimit < required - 15:
            return {
                "final_status": "OUT_OF_FEE",
                "execution_result": "FINISHED_WITH_ERROR",
                "result_code": 2,
                "stderr": "Simulated out of fee",
                "genvm_log": ["execution halted: out of fee"],
                "gas_used": gaslimit,
                "success": False,
                "out_of_fee": True,
            }

        if gaslimit <= self.settings.gas_thresholds.borderline_below and scenario.behavior.nondeterministic and borderline_flip:
            return {
                "final_status": "OUT_OF_FEE",
                "execution_result": "FINISHED_WITH_ERROR",
                "result_code": 3,
                "stderr": "Simulated borderline fee failure",
                "genvm_log": ["nondeterministic branch triggered extra gas use"],
                "gas_used": gaslimit,
                "success": False,
                "out_of_fee": True,
            }

        return {
            "final_status": "FINALIZED",
            "execution_result": "FINISHED_WITH_RETURN",
            "result_code": 0,
            "stderr": "",
            "genvm_log": ["execution ok"],
            "gas_used": min(gaslimit, required),
            "success": True,
            "out_of_fee": False,
        }

    def submit(self, scenario: Scenario, network: str, gaslimit: int) -> SubmissionResult:
        tx_hash = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:8]
        submitted_at = now_utc()

        contract_address = scenario.contract.address
        if scenario.kind == "deploy":
            contract_address = "0x" + uuid.uuid4().hex[:40]

        outcome = self._outcome(scenario, gaslimit)
        state_preview = None
        if outcome["success"] and scenario.kind == "write":
            value = scenario.contract.args[0] if scenario.contract.args else None
            state_preview = {scenario.behavior.state_key: value}

        with self._lock:
            self._tx_store[tx_hash] = {
                "scenario_name": scenario.name,
                "scenario": scenario,
                "network": network,
                "submitted_at": submitted_at,
                "gaslimit": gaslimit,
                "outcome": outcome,
                "contract_address": contract_address,
                "state_preview": state_preview,
            }
            if outcome["success"]:
                state_bucket = self._state.setdefault(contract_address or "", {})
                if scenario.kind == "write" and state_preview:
                    state_bucket.update(state_preview)
                elif scenario.kind == "deploy":
                    state_bucket["deployed"] = True
                    state_bucket["constructor_args"] = list(scenario.contract.constructor_args)

        return SubmissionResult(
            tx_hash=tx_hash,
            network=network,
            submitted_at=submitted_at,
            raw={
                "mock": True,
                "scenario_name": scenario.name,
                "gaslimit": gaslimit,
                "contract_address": contract_address,
            },
            contract_address=contract_address,
        )

    def get_status(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        with self._lock:
            info = self._tx_store[tx_hash]
        submitted_at = info["submitted_at"]
        now = now_utc()
        elapsed_ms = int((now - submitted_at).total_seconds() * 1000)
        delay = info["scenario"].behavior.artificial_delay_ms
        stages = [
            (0, "PENDING"),
            (int(delay * 0.2), "PROPOSING"),
            (int(delay * 0.4), "COMMITTING"),
            (int(delay * 0.6), "REVEALING"),
            (delay, info["outcome"]["final_status"]),
        ]
        current = "PENDING"
        for threshold, status in stages:
            if elapsed_ms >= threshold:
                current = status
        return {
            "tx_hash": tx_hash,
            "status": current,
            "execution_result": info["outcome"]["execution_result"] if current == info["outcome"]["final_status"] else None,
            "result_code": info["outcome"]["result_code"] if current == info["outcome"]["final_status"] else None,
            "gas_used": info["outcome"]["gas_used"] if current == info["outcome"]["final_status"] else None,
            "contract_address": info["contract_address"],
            "mock": True,
        }

    def get_receipt(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        with self._lock:
            info = self._tx_store[tx_hash]
        return {
            "tx_hash": tx_hash,
            "status": info["outcome"]["final_status"],
            "execution_result": info["outcome"]["execution_result"],
            "result_code": info["outcome"]["result_code"],
            "gas_used": info["outcome"]["gas_used"],
            "stderr": info["outcome"]["stderr"],
            "contract_address": info["contract_address"],
            "raw": {
                "scenario_name": info["scenario_name"],
                "network": info["network"],
                "state_preview": info["state_preview"],
            },
        }

    def get_trace(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        with self._lock:
            info = self._tx_store[tx_hash]
        return {
            "tx_hash": tx_hash,
            "result_code": info["outcome"]["result_code"],
            "return_data": None if not info["outcome"]["success"] else {"ok": True},
            "stderr": info["outcome"]["stderr"],
            "genvm_log": info["outcome"]["genvm_log"],
            "mock": True,
        }

    def read_state(self, contract_address: str, function_name: str, args: list[Any] | None = None, network: str | None = None) -> Dict[str, Any]:
        with self._lock:
            state = self._state.get(contract_address, {}).copy()
        if function_name in {"get_storage", "get_value", "read_storage"}:
            value = state.get("storage")
            if value is None and len(state) == 1:
                value = next(iter(state.values()))
            return {"value": value, "state": state, "mock": True}
        return {"state": state, "mock": True}
