from __future__ import annotations

import argparse
from pathlib import Path

from .adapters.factory import create_adapter
from .config import load_settings
from .report_writer import ReportWriter
from .runner import ScenarioRunner
from .scenario_loader import load_scenarios
from .utils import ensure_dir, utc_timestamp_slug


PROJECT_ROOT = Path(__file__).resolve().parents[1]



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GenLayer gas harness")
    parser.add_argument("--scenario", required=True, help="Path to a scenario YAML or a folder with YAML files")
    parser.add_argument("--adapter", default=None, help="Adapter mode: mock or command")
    parser.add_argument("--debug", default=None, help="Debug mode override: never | on-fail | always")
    parser.add_argument("--repeat", type=int, default=None, help="Override repeat count for every scenario")
    parser.add_argument("--concurrency", type=int, default=None, help="Override concurrency for every scenario")
    parser.add_argument("--wait-status", default=None, help="Override wait status: accepted | finalized")
    parser.add_argument("--out", default=None, help="Output root directory")
    parser.add_argument("--verbose", action="store_true", help="Print intermediate steps to stdout")
    parser.add_argument("--print-logs", action="store_true", help="Echo command stdout/stderr to stdout")
    return parser



def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings(PROJECT_ROOT)
    settings.verbose = settings.verbose or args.verbose
    settings.print_logs = settings.print_logs or args.print_logs

    adapter = create_adapter(args.adapter or settings.adapter_mode, settings)
    scenarios = load_scenarios(args.scenario)

    output_root = Path(args.out or settings.output_dir)
    run_root = ensure_dir(output_root / utc_timestamp_slug())
    report_writer = ReportWriter(run_root, echo_logs=settings.verbose or settings.print_logs)
    report_writer.write_manifest(settings, scenarios, vars(args))
    report_writer.log_event(
        f"harness-start adapter={args.adapter or settings.adapter_mode} scenarios={len(scenarios)} out={run_root} verbose={settings.verbose} print_logs={settings.print_logs}"
    )

    runner = ScenarioRunner(settings, adapter, report_writer)
    results = runner.run_scenarios(
        scenarios,
        repeat_override=args.repeat,
        concurrency_override=args.concurrency,
        debug_override=args.debug,
        wait_status_override=args.wait_status,
    )

    passed = sum(1 for r in results if r.actual_pass)
    report_writer.log_event(f"harness-finish total={len(results)} passed={passed} failed={len(results) - passed}")
    print(f"Run root: {run_root}")
    print(f"Results: total={len(results)} passed={passed} failed={len(results) - passed}")
    print(f"CSV: {report_writer.csv_path}")
    print(f"Summary: {report_writer.summary_path}")
    print(f"Full report: {report_writer.full_report_path}")
    print(f"Summary JSON: {report_writer.summary_json_path}")
    print(f"Manifest: {report_writer.manifest_path}")
    print(f"Live log: {report_writer.live_log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
