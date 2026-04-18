#!/usr/bin/env python3
from __future__ import annotations

from _common import build_parser, print_json, rpc_call


def main() -> int:
    parser = build_parser("Call gen_dbg_traceTransaction")
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--tx", required=True)
    parser.add_argument("--round", type=int, default=0)
    args = parser.parse_args()

    result = rpc_call(args.rpc, "gen_dbg_traceTransaction", [{"txID": args.tx, "round": args.round}])
    if isinstance(result, dict):
        result.setdefault("_method", "gen_dbg_traceTransaction")
        print_json(result)
    else:
        print_json({"result": result, "_method": "gen_dbg_traceTransaction"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
