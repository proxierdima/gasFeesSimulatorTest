from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from typing import Any, List

_TX_HASH_RE = re.compile(r"0x[a-fA-F0-9]{32,}")
_ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")


def cli_binary() -> str:
    return shutil.which("genlayer") or "genlayer"


def require_cli() -> str:
    binary = cli_binary()
    if shutil.which(binary) is None and binary == "genlayer":
        raise RuntimeError(
            "genlayer CLI not found in PATH. Install it with `npm install -g genlayer` or set GLH_GENLAYER_CLI."
        )
    return binary


def parse_args_json(text: str) -> List[Any]:
    text = (text or "[]").strip()
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    return value if isinstance(value, list) else [value]


def cli_arg(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def run_cli(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        raise RuntimeError(
            f"CLI command failed ({proc.returncode}): {shlex.join(cmd)}\nSTDERR: {stderr}\nSTDOUT: {stdout}"
        )
    payload: dict[str, Any]
    if stdout:
        try:
            parsed = json.loads(stdout)
            payload = parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            payload = {"stdout": stdout}
    else:
        payload = {"stdout": ""}

    payload.setdefault("_command", shlex.join(cmd))
    if stderr:
        payload.setdefault("_stderr", stderr)

    merged = "\n".join(part for part in (stdout, stderr) if part)
    tx_match = _TX_HASH_RE.search(merged)
    if tx_match:
        payload.setdefault("tx_hash", tx_match.group(0))

    if "contract_address" not in payload:
        addresses = _ADDRESS_RE.findall(merged)
        if len(addresses) >= 1:
            payload.setdefault("possible_addresses", addresses)
    return payload
