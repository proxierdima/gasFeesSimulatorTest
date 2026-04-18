
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .models import BehaviorSpec, ContractSpec, ExpectSpec, GasProfile, RunSpec, Scenario, StateCheck


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def _scenario_from_dict(data: Dict[str, Any], file_path: Path) -> Scenario:
    contract_data = data.get("contract", {})
    run_data = data.get("run", {})
    gas_data = data.get("gas_profile", {})
    expect_data = data.get("expect", {})
    behavior_data = data.get("behavior", {})
    state_check_data = expect_data.get("state_check", {})

    return Scenario(
        name=data["name"],
        kind=data.get("kind", "write"),
        network=data.get("network", "bradbury"),
        contract=ContractSpec(
            address=contract_data.get("address"),
            function_name=contract_data.get("function_name"),
            args=contract_data.get("args", []) or [],
            contract_file=contract_data.get("contract_file"),
            constructor_args=contract_data.get("constructor_args", []) or [],
        ),
        run=RunSpec(
            repeat=int(run_data.get("repeat", 1)),
            concurrency=int(run_data.get("concurrency", 1)),
            wait_status=run_data.get("wait_status", "finalized"),
            debug=run_data.get("debug", "on-fail"),
            timeout_seconds=float(run_data.get("timeout_seconds", 30)),
            poll_interval_seconds=float(run_data.get("poll_interval_seconds", 0.5)),
            tags=run_data.get("tags", []) or [],
        ),
        gas_profile=GasProfile(
            mode=gas_data.get("mode", "preset"),
            preset=gas_data.get("preset"),
            gaslimit=gas_data.get("gaslimit"),
            tip_for_appeal=int(gas_data.get("tip_for_appeal", 0)),
            note=gas_data.get("note", ""),
        ),
        expect=ExpectSpec(
            allowed_final_statuses=expect_data.get("allowed_final_statuses", ["FINALIZED"]),
            allowed_execution_results=expect_data.get("allowed_execution_results", ["FINISHED_WITH_RETURN"]),
            expect_out_of_fee=bool(expect_data.get("expect_out_of_fee", False)),
            expect_possible_failure=bool(expect_data.get("expect_possible_failure", False)),
            state_check=StateCheck(
                enabled=bool(state_check_data.get("enabled", False)),
                function_name=state_check_data.get("function_name"),
                args=state_check_data.get("args", []) or [],
                expected=state_check_data.get("expected"),
            ),
        ),
        behavior=BehaviorSpec(
            base_required_gas=int(behavior_data.get("base_required_gas", 60)),
            appeal_like=bool(behavior_data.get("appeal_like", False)),
            nondeterministic=bool(behavior_data.get("nondeterministic", False)),
            force_revert=bool(behavior_data.get("force_revert", False)),
            state_key=behavior_data.get("state_key", "storage"),
            artificial_delay_ms=int(behavior_data.get("artificial_delay_ms", 500)),
            rpc_flaky=bool(behavior_data.get("rpc_flaky", False)),
        ),
        file_path=str(file_path),
    )


def load_scenarios(path_str: str) -> List[Scenario]:
    path = Path(path_str)
    files: List[Path]
    if path.is_dir():
        files = sorted([p for p in path.glob("*.yaml") if p.is_file()])
    else:
        files = [path]

    scenarios: List[Scenario] = []
    for file_path in files:
        with file_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        scenarios.append(_scenario_from_dict(_expand_env(data), file_path.resolve()))
    return scenarios
