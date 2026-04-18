#!/usr/bin/env python3
from __future__ import annotations

from _common import build_parser, print_json, rpc_call

STATUS_MAP = {
    0: "UNINITIALIZED",
    1: "PENDING",
    2: "PROPOSING",
    3: "COMMITTING",
    4: "REVEALING",
    5: "ACCEPTED",
    6: "UNDETERMINED",
    7: "FINALIZED",
    8: "CANCELED",
    9: "APPEAL_REVEALING",
    10: "APPEAL_COMMITTING",
    11: "READY_TO_FINALIZE",
    12: "VALIDATORS_TIMEOUT",
    13: "LEADER_TIMEOUT",
}
EXECUTION_RESULT_MAP = {
    0: "NOT_VOTED",
    1: "FINISHED_WITH_RETURN",
    2: "FINISHED_WITH_ERROR",
    3: "VM_ERROR",
}
CONSENSUS_RESULT_MAP = {
    0: "DISAGREE",
    1: "AGREE",
}


def main() -> int:
    parser = build_parser("Call gen_getTransactionReceipt")
    parser.add_argument("--rpc", required=True)
    parser.add_argument("--tx", required=True)
    args = parser.parse_args()

    result = rpc_call(args.rpc, "gen_getTransactionReceipt", [{"txId": args.tx}])
    if not isinstance(result, dict):
        print_json({"result": result, "_method": "gen_getTransactionReceipt"})
        return 0

    status_code = result.get("status")
    consensus_code = result.get("result")
    execution_code = result.get("txExecutionResult")

    status_name = result.get("statusName") or result.get("status_name") or STATUS_MAP.get(status_code, status_code)
    consensus_name = result.get("resultName") or result.get("consensusResultName") or CONSENSUS_RESULT_MAP.get(consensus_code, consensus_code)
    execution_name = result.get("txExecutionResultName") or result.get("executionResultName") or EXECUTION_RESULT_MAP.get(execution_code, execution_code)
    contract_address = result.get("contract_address") or result.get("contractAddress") or (result.get("txDataDecoded") or {}).get("contractAddress") or result.get("recipient")

    flattened = {
        **result,
        "tx_hash": result.get("id") or args.tx,
        "status_code": status_code,
        "status": status_name,
        "consensus_code": consensus_code,
        "consensus_result": consensus_name,
        "execution_code": execution_code,
        "execution_result": execution_name,
        "contract_address": contract_address,
        "_method": "gen_getTransactionReceipt",
    }
    print_json(flattened)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
