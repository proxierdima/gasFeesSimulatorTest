#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from _common import print_json, run_backend_template


def parse_args_json(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        return [raw]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--pk", default="")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--fn", required=True)
    parser.add_argument("--args", default="[]")
    parser.add_argument("--gaslimit", default="")
    args = parser.parse_args()

    fn_args = parse_args_json(args.args)

    payload = run_backend_template(
        "GLH_SUBMIT_WRITE_BACKEND_CMD",
        {
            "rpc_url": args.rpc,
            "contract_address": args.contract,
            "function_name": args.fn,
            "args_json": json.dumps(fn_args, ensure_ascii=False),
            "gaslimit": str(args.gaslimit),
            "private_key": args.pk or "",
        },
        allow_nonzero_with_tx_hash=True,
    )
    if payload.get("_backend_nonzero_salvaged"):
        payload["submit_warning"] = (
            "Backend exited non-zero, but tx_hash was recovered from stdout. "
            "Use status/receipt polling for the final verdict."
        )


    if not isinstance(payload, dict):
        payload = {"value": payload}

    print_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
