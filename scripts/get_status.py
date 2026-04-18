#!/usr/bin/env python3
import argparse
import json

from _common import rpc_call


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--tx", required=True)
    args = parser.parse_args()

    result = rpc_call(
        args.rpc,
        "gen_getTransactionStatus",
        [{"txId": args.tx}],
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
