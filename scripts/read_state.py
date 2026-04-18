#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any

from _common import build_parser, print_json, run_backend_template


def _normalize_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text.startswith("Result:"):
        text = text[len("Result:"):].strip()
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"null", "none"}:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def _fallback_cli_read(rpc: str, contract: str, fn: str, fn_args: list[Any]) -> dict[str, Any]:
    cmd = ["/usr/bin/genlayer", "call", contract, fn, "--rpc", rpc]
    for arg in fn_args:
        if isinstance(arg, bool):
            cmd.append("true" if arg else "false")
        elif arg is None:
            cmd.append("null")
        elif isinstance(arg, (dict, list)):
            cmd.append(json.dumps(arg, ensure_ascii=False))
        else:
            cmd.append(str(arg))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        raise RuntimeError(
            f"Read backend command failed ({proc.returncode}): {' '.join(shlex.quote(x) for x in cmd)}\n"
            f"STDERR: {stderr}\nSTDOUT: {stdout}"
        )

    return {
        "stdout": stdout,
        "_command": " ".join(shlex.quote(x) for x in cmd),
        "_stderr": stderr,
        "contract_address": contract,
        "function_name": fn,
        "backend": "genlayer-cli",
        "value": stdout,
    }


def main() -> int:
    parser = build_parser("Read contract state via backend")
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--fn", required=True)
    parser.add_argument("--args", default="[]")
    args = parser.parse_args()

    try:
        fn_args = json.loads(args.args)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid --args JSON: {e}") from e

    if not isinstance(fn_args, list):
        raise SystemExit("--args must be a JSON array")

    if os.getenv("GLH_READ_STATE_BACKEND_CMD", "").strip():
        payload = run_backend_template(
            "GLH_READ_STATE_BACKEND_CMD",
            {
                "rpc_url": args.rpc,
                "contract_address": args.contract,
                "function_name": args.fn,
                "args_json": json.dumps(fn_args, ensure_ascii=False),
            },
        )
    else:
        payload = _fallback_cli_read(args.rpc, args.contract, args.fn, fn_args)

    if not isinstance(payload, dict):
        payload = {"value": payload}

    raw_value = payload.get("value")
    if raw_value is None and "stdout" in payload:
        raw_value = payload.get("stdout")
    normalized = _normalize_value(raw_value)

    result = {
        **payload,
        "contract_address": args.contract,
        "function_name": args.fn,
        "value": normalized,
        "backend": payload.get("backend", "custom"),
    }
    result.pop("tx_hash", None)
    result.pop("possible_addresses", None)
    print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
