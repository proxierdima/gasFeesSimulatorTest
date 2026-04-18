from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RpcHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8"))
        method = payload.get("method")
        result = {}
        if method == "gen_getTransactionStatus":
            result = {"status": "FINALIZED", "statusCode": 7}
        elif method == "gen_getTransactionReceipt":
            result = {"id": "0xabc", "status": 7, "result": 0, "recipient": "0x111"}
        elif method == "gen_dbg_traceTransaction":
            result = {"transaction_id": "0xabc", "result_code": 0, "stderr": "", "genvm_log": []}
        elif method == "gen_getContractState":
            result = "0x68656c6c6f"
        response = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def test_helper_scripts_against_fake_rpc(tmp_path: Path) -> None:
    server = HTTPServer(("127.0.0.1", 0), RpcHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rpc_url = f"http://127.0.0.1:{server.server_port}"
    try:
        out = subprocess.check_output(
            [sys.executable, "scripts/get_status.py", "--rpc", rpc_url, "--tx", "0xabc"],
            cwd=PROJECT_ROOT,
            text=True,
        )
        assert json.loads(out)["status"] == "FINALIZED"

        out = subprocess.check_output(
            [sys.executable, "scripts/get_receipt.py", "--rpc", rpc_url, "--tx", "0xabc"],
            cwd=PROJECT_ROOT,
            text=True,
        )
        assert json.loads(out)["execution_result"] == "FINISHED_WITH_RETURN"

        out = subprocess.check_output(
            [sys.executable, "scripts/get_trace.py", "--rpc", rpc_url, "--tx", "0xabc"],
            cwd=PROJECT_ROOT,
            text=True,
        )
        assert json.loads(out)["result_code"] == 0

        out = subprocess.check_output(
            [sys.executable, "scripts/read_state.py", "--rpc", rpc_url, "--contract", "0x111"],
            cwd=PROJECT_ROOT,
            text=True,
        )
        assert json.loads(out)["value"] == "hello"
    finally:
        server.shutdown()
        thread.join(timeout=2)
