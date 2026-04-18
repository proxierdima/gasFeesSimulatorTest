#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
from typing import Any

_TX_HASH_RE = re.compile(r"0x[a-fA-F0-9]{32,}")
_ADDR_RE = re.compile(r"0x[a-fA-F0-9]{40}")

def require_cli() -> str:
    return shutil.which("genlayer") or "genlayer"

def parse_args_json(text: str) -> list[Any]:
    text = (text or "[]").strip()
    if not text:
        return []
    try:
        value = json.loads(text)
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        return [text]

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

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rpc", required=True)
    p.add_argument("--contract-file", required=True)
    p.add_argument("--constructor-args", default="[]")
    p.add_argument("--gaslimit", default="") # Принимаем, но не передаем в CLI
    args = p.parse_args()

    password = os.getenv("GLH_KEYSTORE_PASSWORD", "")
    if not password:
        raise SystemExit("GLH_KEYSTORE_PASSWORD is required")

    cmd = [require_cli(), "deploy", "--contract", args.contract_file, "--rpc", args.rpc]

    ctor_args = parse_args_json(args.constructor_args)
    if ctor_args:
        cmd.append("--args")
        cmd.extend(cli_arg(item) for item in ctor_args)

    proc = subprocess.run(cmd, input=password + "\n", text=True, capture_output=True)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    merged = "\n".join(part for part in (stdout, stderr) if part)

    if proc.returncode != 0:
        raise SystemExit(
            f"CLI command failed ({proc.returncode}): {shlex.join(cmd)}\nSTDERR: {stderr}\nSTDOUT: {stdout}"
        )

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

    tx = _TX_HASH_RE.search(merged)
    if tx:
        payload.setdefault("tx_hash", tx.group(0))

    addrs = _ADDR_RE.findall(merged)
    if addrs:
        payload.setdefault("possible_addresses", addrs)
        payload.setdefault("contract_address", addrs[-1])

    payload.setdefault("backend", "custom-deploy-backend")
    print(json.dumps(payload, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
