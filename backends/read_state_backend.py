#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess


def normalize_result(stdout: str):
    text = stdout.strip()
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--fn", required=True)
    parser.add_argument("--args", default="[]")
    args = parser.parse_args()

    fn_args = json.loads(args.args)
    if not isinstance(fn_args, list):
        raise SystemExit("--args must be a JSON array")

    cmd = [
        "/usr/bin/genlayer",
        "call",
        args.contract,
        args.fn,
        "--rpc",
        args.rpc,
    ]

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
            f"Read command failed ({proc.returncode}): {' '.join(shlex.quote(x) for x in cmd)}\n"
            f"STDERR: {stderr}\nSTDOUT: {stdout}"
        )

    payload = {
        "stdout": stdout,
        "_command": " ".join(shlex.quote(x) for x in cmd),
        "_stderr": stderr,
        "contract_address": args.contract,
        "function_name": args.fn,
        "value": normalize_result(stdout),
        "backend": "genlayer-cli",
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
