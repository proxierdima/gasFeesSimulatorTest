from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Dict

from ..models import AppSettings, Scenario, SubmissionResult
from ..utils import expand_template, now_utc, retry_call
from .base import BaseAdapter

_TX_HASH_RE = re.compile(r"0x[a-fA-F0-9]{64}\b")


class CommandAdapter(BaseAdapter):
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def _echo_process(
        self, command: str, stdout: str, stderr: str, *, failed: bool = False
    ) -> None:
        if not (self.settings.verbose or self.settings.print_logs):
            return
        prefix = "[cmd:fail]" if failed else "[cmd]"
        print(f"{prefix} {command}", flush=True)
        if stdout and self.settings.print_logs:
            for line in stdout.splitlines():
                print(f"[stdout] {line}", flush=True)
        if stderr and self.settings.print_logs:
            for line in stderr.splitlines():
                print(f"[stderr] {line}", flush=True)

    def _run_template(self, template: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not template:
            raise RuntimeError("Command adapter template is empty")
        command = expand_template(template, context)

        def _exec() -> Dict[str, Any]:
            # On Windows, cmd.exe doesn't handle single quotes like bash does
            # We need to replace single quotes around paths with double quotes,
            # but preserve single quotes inside arguments (like JSON strings)
            import re
            import sys

            if sys.platform == "win32":
                # Pattern to match single-quoted paths (not containing spaces or special chars inside)
                # This matches 'C:\path\to\file.py' but not '[true]'
                win_command = re.sub(
                    r"'([A-Za-z]:[/\\][^']*?\.(?:py|mjs|js|exe))'", r'"\1"', command
                )
                proc = subprocess.run(
                    win_command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    env=os.environ.copy(),
                )
            else:
                proc = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    env=os.environ.copy(),
                )
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            self._echo_process(command, stdout, stderr, failed=proc.returncode != 0)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"Command failed ({proc.returncode}): {command}\nSTDERR: {stderr}\nSTDOUT: {stdout}"
                )
            if not stdout:
                return {"stdout": "", "stderr": stderr, "command": command}
            try:
                payload = json.loads(stdout)
                if isinstance(payload, dict):
                    payload.setdefault("_command", command)
                    payload.setdefault("_stderr", stderr)
                    return payload
                return {"value": payload, "_command": command, "_stderr": stderr}
            except json.JSONDecodeError:
                match = _TX_HASH_RE.search(stdout)
                data = {"stdout": stdout, "_command": command, "_stderr": stderr}
                if match:
                    data["tx_hash"] = match.group(0)
                return data

        payload, attempts = retry_call(
            _exec,
            retries=self.settings.command_retries,
            backoff_seconds=self.settings.command_retry_backoff_seconds,
        )
        payload.setdefault("_attempts", attempts)
        return payload

    def _network_rpc(self, network: str) -> str:
        return (
            self.settings.networks.get(network, {}).get("rpc_url")
            or self.settings.rpc_url
        )

    def submit(
        self, scenario: Scenario, network: str, gaslimit: int
    ) -> SubmissionResult:
        template = (
            self.settings.command_submit_write
            if scenario.kind == "write"
            else self.settings.command_submit_deploy
        )
        payload = self._run_template(
            template,
            {
                "rpc_url": self._network_rpc(network),
                "private_key": self.settings.private_key,
                "contract_address": scenario.contract.address or "",
                "function_name": scenario.contract.function_name or "",
                "args_json": scenario.contract.args
                if scenario.kind == "write"
                else scenario.contract.constructor_args,
                "gaslimit": gaslimit,
                "contract_file": scenario.contract.contract_file or "",
            },
        )
        tx_hash = (
            payload.get("tx_hash")
            or payload.get("hash")
            or payload.get("transaction_hash")
        )
        if not tx_hash:
            raise RuntimeError(
                f"Could not extract tx hash from submit payload: {payload}"
            )
        contract_address = payload.get("contract_address") or scenario.contract.address
        return SubmissionResult(
            tx_hash=tx_hash,
            network=network,
            submitted_at=now_utc(),
            raw=payload,
            contract_address=contract_address,
        )

    def get_status(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        return self._run_template(
            self.settings.command_status,
            {
                "rpc_url": self._network_rpc(network or self.settings.default_network),
                "tx_hash": tx_hash,
            },
        )

    def get_receipt(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        return self._run_template(
            self.settings.command_receipt,
            {
                "rpc_url": self._network_rpc(network or self.settings.default_network),
                "tx_hash": tx_hash,
            },
        )

    def get_trace(self, tx_hash: str, network: str | None = None) -> Dict[str, Any]:
        return self._run_template(
            self.settings.command_trace,
            {
                "rpc_url": self._network_rpc(network or self.settings.default_network),
                "tx_hash": tx_hash,
                "trace_round": self.settings.trace_round,
            },
        )

    def read_state(
        self,
        contract_address: str,
        function_name: str,
        args: list[Any] | None = None,
        network: str | None = None,
    ) -> Dict[str, Any]:
        return self._run_template(
            self.settings.command_read_state,
            {
                "rpc_url": self._network_rpc(network or self.settings.default_network),
                "contract_address": contract_address,
                "function_name": function_name,
                "args_json": args or [],
            },
        )
