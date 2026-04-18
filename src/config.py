from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

from .models import AppSettings, GasThresholds



def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}



def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}



def load_settings(project_root: Path) -> AppSettings:
    load_dotenv(project_root / ".env")

    defaults = _load_yaml(project_root / "config" / "defaults.yaml")
    networks_file = _load_yaml(project_root / "config" / "networks.yaml")
    gas_cfg = defaults.get("gas_thresholds", {})

    return AppSettings(
        adapter_mode=os.getenv("HARNESS_ADAPTER_MODE", defaults.get("adapter_mode", "mock")),
        output_dir=os.getenv("HARNESS_OUTPUT_DIR", defaults.get("output_dir", "artifacts")),
        default_network=os.getenv("HARNESS_DEFAULT_NETWORK", defaults.get("default_network", "bradbury")),
        default_wait_status=os.getenv("HARNESS_DEFAULT_WAIT_STATUS", defaults.get("default_wait_status", "finalized")),
        default_debug=os.getenv("HARNESS_DEFAULT_DEBUG", defaults.get("default_debug", "on-fail")),
        poll_interval_seconds=float(os.getenv("HARNESS_POLL_INTERVAL_SECONDS", defaults.get("poll_interval_seconds", 0.75))),
        timeout_seconds=float(os.getenv("HARNESS_TIMEOUT_SECONDS", defaults.get("timeout_seconds", 45))),
        random_seed=int(os.getenv("HARNESS_RANDOM_SEED", defaults.get("random_seed", 42))),
        rpc_url=os.getenv("HARNESS_RPC_URL", ""),
        private_key=os.getenv("HARNESS_PRIVATE_KEY", ""),
        gas_thresholds=GasThresholds(
            fail_below=int(os.getenv("HARNESS_GAS_FAIL_BELOW", gas_cfg.get("fail_below", 40))),
            borderline_below=int(os.getenv("HARNESS_GAS_BORDERLINE_BELOW", gas_cfg.get("borderline_below", 65))),
            normal=int(os.getenv("HARNESS_GAS_NORMAL", gas_cfg.get("normal", 90))),
            high=int(os.getenv("HARNESS_GAS_HIGH", gas_cfg.get("high", 140))),
        ),
        command_submit_write=os.getenv("HARNESS_CMD_SUBMIT_WRITE", ""),
        command_submit_deploy=os.getenv("HARNESS_CMD_SUBMIT_DEPLOY", ""),
        command_status=os.getenv("HARNESS_CMD_STATUS", ""),
        command_receipt=os.getenv("HARNESS_CMD_RECEIPT", ""),
        command_trace=os.getenv("HARNESS_CMD_TRACE", ""),
        command_read_state=os.getenv("HARNESS_CMD_READ_STATE", ""),
        command_retries=int(os.getenv("HARNESS_COMMAND_RETRIES", defaults.get("command_retries", 3))),
        command_retry_backoff_seconds=float(os.getenv("HARNESS_COMMAND_RETRY_BACKOFF_SECONDS", defaults.get("command_retry_backoff_seconds", 1.0))),
        trace_round=int(os.getenv("HARNESS_TRACE_ROUND", defaults.get("trace_round", 0))),
        networks=networks_file.get("networks", {}),
        verbose=_bool_env("HARNESS_VERBOSE", False),
        print_logs=_bool_env("HARNESS_PRINT_LOGS", False),
    )
