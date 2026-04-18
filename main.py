#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

SUITE_GROUPS = [
    ("Group A", "scenarios/report_suite_group_a"),
    ("Group B", "scenarios/report_suite_group_b"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Deploy fresh fixture on Bradbury, then run the full gas test suite."
    )
    _ = p.add_argument(
        "--project-root", default=".", help="Path to glh_v4 project root"
    )
    _ = p.add_argument(
        "--password",
        default="",
        help="Legacy keystore password. Still accepted for read/debug helpers",
    )
    _ = p.add_argument(
        "--out",
        default="artifacts",
        help="Artifacts output dir relative to project root unless absolute",
    )
    _ = p.add_argument(
        "--skip-npm-install",
        action="store_true",
        help="Do not auto-install Node dependencies",
    )
    return p.parse_args()


def resolve_project_root(project_root: str) -> Path:
    root = Path(project_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"[error] project root does not exist: {root}")
    if not (root / "src").exists():
        raise SystemExit(f"[error] src directory not found under: {root}")
    return root


def resolve_password(cli_password: str) -> str:
    return (
        cli_password
        or os.getenv("GLH_KEYSTORE_PASSWORD", "")
        or os.getenv("PASSWORD", "")
    )


def load_env_file(project_root: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    env_file = project_root / ".env.bradbury"
    if not env_file.exists():
        env_file = project_root / ".env"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def ensure_node_deps(project_root: Path, *, skip: bool) -> None:
    if skip:
        return
    package_json = project_root / "package.json"
    if not package_json.exists():
        return
    node_modules = project_root / "node_modules"
    needs_install = (
        not node_modules.exists()
        or not (node_modules / "genlayer-js").exists()
        or not (node_modules / "viem").exists()
    )
    if not needs_install:
        return
    print("[info] installing Node dependencies (genlayer-js, viem)...", flush=True)
    try:
        proc = subprocess.run(["npm", "install"], cwd=project_root, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("npm is required to install genlayer-js and viem") from exc
    if proc.returncode != 0:
        raise RuntimeError("npm install failed")


def project_env(project_root: Path, password: str) -> Dict[str, str]:
    env: Dict[str, str] = os.environ.copy()
    env.update(load_env_file(project_root))
    _ = env.setdefault("HARNESS_DEFAULT_NETWORK", "bradbury")
    env["HARNESS_ADAPTER_MODE"] = "command"
    env["HARNESS_DEFAULT_WAIT_STATUS"] = "accepted"
    env["HARNESS_DEFAULT_DEBUG"] = env.get("HARNESS_DEFAULT_DEBUG", "on-fail")
    env["HARNESS_VERBOSE"] = env.get("HARNESS_VERBOSE", "1")
    env["HARNESS_PRINT_LOGS"] = env.get("HARNESS_PRINT_LOGS", "1")
    if password:
        env["GLH_KEYSTORE_PASSWORD"] = password

    if not env.get("HARNESS_PRIVATE_KEY", "").strip():
        raise SystemExit(
            "[error] HARNESS_PRIVATE_KEY is required for on-chain gas-controlled submissions"
        )

    py = sys.executable or "python3"
    backends_dir = project_root / "backends"
    scripts_dir = project_root / "scripts"

    env["HARNESS_CMD_SUBMIT_WRITE"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'submit_write.py'))} "
        f"--rpc {{rpc_url_sh}} --contract {{contract_address_sh}} --fn {{function_name_sh}} --args {{args_json_sh}} --gaslimit {{gaslimit_sh}}"
    )
    env["HARNESS_CMD_SUBMIT_DEPLOY"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'submit_deploy.py'))} "
        f"--rpc {{rpc_url_sh}} --contract-file {{contract_file_sh}} --constructor-args {{args_json_sh}} --gaslimit {{gaslimit_sh}}"
    )
    env["HARNESS_CMD_STATUS"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'get_status.py'))} --rpc {{rpc_url_sh}} --tx {{tx_hash_sh}}"
    )
    env["HARNESS_CMD_RECEIPT"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'get_receipt.py'))} --rpc {{rpc_url_sh}} --tx {{tx_hash_sh}}"
    )
    env["HARNESS_CMD_TRACE"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'get_trace.py'))} --rpc {{rpc_url_sh}} --tx {{tx_hash_sh}}"
    )
    env["HARNESS_CMD_READ_STATE"] = (
        f"{shlex.quote(py)} {shlex.quote(str(scripts_dir / 'read_state.py'))} --rpc {{rpc_url_sh}} --contract {{contract_address_sh}} --fn {{function_name_sh}} --args {{args_json_sh}}"
    )

    env["GLH_SUBMIT_DEPLOY_BACKEND_CMD"] = (
        f"node {str(backends_dir / 'onchain_submit_deploy.mjs').replace(chr(92), '/')} "
        f"--rpc {{rpc_url_sh}} --contract-file {{contract_file_sh}} --constructor-args {{args_json_sh}} --gaslimit {{gaslimit_sh}}"
    )
    env["GLH_SUBMIT_WRITE_BACKEND_CMD"] = (
        f"node {str(backends_dir / 'onchain_submit_write.mjs').replace(chr(92), '/')} "
        f"--rpc {{rpc_url_sh}} --contract {{contract_address_sh}} --fn {{function_name_sh}} --args {{args_json_sh}} --gaslimit {{gaslimit_sh}}"
    )
    env["GLH_READ_STATE_BACKEND_CMD"] = (
        f"{shlex.quote(py)} {shlex.quote(str(backends_dir / 'read_state_backend.py'))} "
        f"--rpc {{rpc_url_sh}} --contract {{contract_address_sh}} --fn {{function_name_sh}} --args {{args_json_sh}}"
    )

    old_pp = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = str(project_root) if not old_pp else f"{project_root}:{old_pp}"
    return env


def run_harness(
    project_root: Path, env: Dict[str, str], scenario_path: str, out: str
) -> Path:
    cmd = [
        sys.executable or "python3",
        "-m",
        "src.main",
        "--scenario",
        scenario_path,
        "--adapter",
        "command",
        "--debug",
        env.get("HARNESS_DEFAULT_DEBUG", "on-fail"),
        "--repeat",
        "1",
        "--concurrency",
        "1",
        "--out",
        out,
        "--verbose",
        "--print-logs",
    ]
    print("CMD:", " ".join(shlex.quote(x) for x in cmd), flush=True)
    proc = subprocess.run(
        cmd, cwd=project_root, env=env, text=True, capture_output=True
    )
    if proc.stdout:
        print(proc.stdout, end="", flush=True)
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"harness failed rc={proc.returncode}")
    run_root = None
    for line in proc.stdout.splitlines():
        if line.startswith("Run root: "):
            run_root = line.split("Run root: ", 1)[1].strip()
    if not run_root:
        raise RuntimeError("Run root not found in harness output")
    return (project_root / run_root).resolve()


def read_summary(run_root: Path) -> Dict[str, Any]:
    path = run_root / "summary.json"
    if not path.exists():
        raise RuntimeError(f"summary.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_runs(run_root: Path) -> List[Dict[str, Any]]:
    path = run_root / "runs.csv"
    if not path.exists():
        raise RuntimeError(f"runs.csv not found: {path}")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def expect_pass(run_root: Path) -> None:
    summary = read_summary(run_root)
    total = int(summary.get("total") or summary.get("total_runs") or 0)
    passed = int(summary.get("passed") or 0)
    failed = int(summary.get("failed") or 0)
    print(f"[info] run_root={run_root}")
    print(f"[info] summary total={total} passed={passed} failed={failed}")
    if total <= 0 or failed != 0 or passed != total:
        raise RuntimeError("harness reported failure")


def extract_contract_address(run_root: Path) -> str:
    for row in read_runs(run_root):
        addr = (row.get("contract_address") or "").strip()
        ok = (row.get("actual_pass") or "").strip().lower() in {"true", "1"}
        if addr and ok:
            return addr
    raise RuntimeError("contract_address not found in successful deploy runs.csv")


def print_mermaid() -> None:
    lines = [
        "```mermaid",
        "flowchart TD",
        '    runsh["./run.sh"] --> orchestrator["main.py"]',
        '    orchestrator --> bootstrap["scenarios/report_bootstrap/deploy_fixture.yaml"]',
        '    orchestrator --> groupA["scenarios/report_suite_group_a/"]',
        '    groupA --> deterministic_baseline["scenarios/report_suite_group_a/deterministic_baseline.yaml"]',
        '    groupA --> low_gas["scenarios/report_suite_group_a/low_gas.yaml"]',
        '    groupA --> borderline_gas["scenarios/report_suite_group_a/borderline_gas.yaml"]',
        '    groupA --> high_gas["scenarios/report_suite_group_a/high_gas.yaml"]',
        '    groupA --> concurrent_same_sender["scenarios/report_suite_group_a/concurrent_same_sender.yaml"]',
        '    orchestrator --> groupB["scenarios/report_suite_group_b/"]',
        '    groupB --> report_01_baseline["scenarios/report_suite_group_b/report_01_baseline.yaml"]',
        '    groupB --> report_02_low_gas["scenarios/report_suite_group_b/report_02_low_gas.yaml"]',
        '    groupB --> report_03_borderline["scenarios/report_suite_group_b/report_03_borderline.yaml"]',
        '    groupB --> report_04_high_gas["scenarios/report_suite_group_b/report_04_high_gas.yaml"]',
        '    groupB --> report_05_invalid_fn["scenarios/report_suite_group_b/report_05_invalid_fn.yaml"]',
        '    groupB --> report_06_concurrent["scenarios/report_suite_group_b/report_06_concurrent.yaml"]',
        "```",
    ]

    print("Scenarios invoked:")
    print("".join(lines))


def validate_environment() -> None:
    """Validate that all required environment variables are set."""
    required_vars = {
        "HARNESS_PRIVATE_KEY": "Private key for signing transactions",
    }

    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var, "").strip():
            missing.append(f"  - {var}: {description}")

    if missing:
        error_msg = (
            "[error] Missing required environment variables:\n"
            + "\n".join(missing)
            + "\n\nPlease set these variables in your .env file or environment."
        )
        raise SystemExit(error_msg)


def main() -> int:
    args = parse_args()
    project_root = resolve_project_root(args.project_root)
    password = resolve_password(args.password)

    # Load .env file first
    from dotenv import load_dotenv

    env_file = project_root / ".env.bradbury"
    if not env_file.exists():
        env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Validate environment before proceeding
    validate_environment()

    ensure_node_deps(project_root, skip=args.skip_npm_install)
    env = project_env(project_root, password)

    print("=== Bradbury Gas Simulator tests ===")
    print(f"project_root={project_root}")
    print(f"out={args.out}")

    deploy_run_root = run_harness(
        project_root, env, "scenarios/report_bootstrap/deploy_fixture.yaml", args.out
    )
    expect_pass(deploy_run_root)
    contract_address = extract_contract_address(deploy_run_root)
    env["GLH_TEST_CONTRACT_ADDRESS"] = contract_address
    print(f"[info] deployed contract_address={contract_address}")

    suite_roots: list[Path] = []
    for group_name, rel_path in SUITE_GROUPS:
        suite_dir = project_root / rel_path
        print(f"[info] running {group_name}: {suite_dir}")
        suite_run_root = run_harness(project_root, env, rel_path, args.out)
        expect_pass(suite_run_root)
        suite_roots.append(suite_run_root)

    print("All steps completed successfully.")
    print(f"Deploy run root: {deploy_run_root}")
    for idx, suite_root in enumerate(suite_roots, start=1):
        print(f"Suite {idx} run root: {suite_root}")
    print_mermaid()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
