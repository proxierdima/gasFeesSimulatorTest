from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from .models import AppSettings, RunResult, Scenario
from .utils import ensure_dir, json_dump, now_utc


class ReportWriter:
    def __init__(self, run_root: Path, *, echo_logs: bool = False):
        self.run_root = run_root
        self.receipts_dir = ensure_dir(run_root / "receipts")
        self.traces_dir = ensure_dir(run_root / "traces")
        self.states_dir = ensure_dir(run_root / "states")
        self.raw_dir = ensure_dir(run_root / "raw")
        self.logs_dir = ensure_dir(run_root / "logs")
        self.live_log_path = self.logs_dir / "live.log"
        self.csv_path = run_root / "runs.csv"
        self.summary_path = run_root / "summary.md"
        self.full_report_path = run_root / "full_report.md"
        self.summary_json_path = run_root / "summary.json"
        self.manifest_path = run_root / "run_manifest.json"
        self._results: List[RunResult] = []
        self.echo_logs = echo_logs

    def log_event(self, message: str, *, echo: bool | None = None) -> None:
        stamp = now_utc().isoformat()
        line = f"[{stamp}] {message}"
        with self.live_log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        should_echo = self.echo_logs if echo is None else echo
        if should_echo:
            print(line, flush=True)

    def write_manifest(self, settings: AppSettings, scenarios: List[Scenario], cli_args: Dict[str, Any]) -> None:
        json_dump(
            self.manifest_path,
            {
                "settings": settings.sanitized(),
                "cli_args": cli_args,
                "scenarios": [
                    {
                        "name": s.name,
                        "kind": s.kind,
                        "network": s.network,
                        "file_path": s.file_path,
                        "tags": s.run.tags,
                    }
                    for s in scenarios
                ],
            },
        )

    def write_payloads(
        self,
        run_id: str,
        receipt: Dict[str, Any],
        trace: Dict[str, Any] | None,
        state: Dict[str, Any] | None,
        raw: Dict[str, Any],
    ) -> Dict[str, str]:
        receipt_path = self.receipts_dir / f"{run_id}.json"
        trace_path = self.traces_dir / f"{run_id}.json"
        state_path = self.states_dir / f"{run_id}.json"
        raw_path = self.raw_dir / f"{run_id}.json"

        json_dump(receipt_path, receipt)
        json_dump(raw_path, raw)
        if trace is not None:
            json_dump(trace_path, trace)
        if state is not None:
            json_dump(state_path, state)

        return {
            "receipt_path": str(receipt_path),
            "trace_path": str(trace_path if trace is not None else ""),
            "state_path": str(state_path if state is not None else ""),
            "raw_path": str(raw_path),
        }

    def append_result(self, result: RunResult) -> None:
        row = result.as_dict()
        fieldnames = list(row.keys())
        write_header = not self.csv_path.exists()
        with self.csv_path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        self._results.append(result)
        self.log_event(
            f"result run_id={result.run_id} scenario={result.scenario_name} final_status={result.final_status} execution_result={result.execution_result} pass={result.actual_pass}"
        )

    def write_summary(self) -> None:
        total = len(self._results)
        passed = sum(1 for r in self._results if r.actual_pass)
        failed = total - passed
        statuses = Counter(r.final_status for r in self._results)
        edge_cases = Counter(r.edge_case_tag for r in self._results if r.edge_case_tag)
        scenarios = Counter(r.scenario_name for r in self._results)
        failing = [r for r in self._results if not r.actual_pass]
        by_scenario: dict[str, list[RunResult]] = defaultdict(list)
        for result in self._results:
            by_scenario[result.scenario_name].append(result)

        summary_payload = {
            "total": total,
            "total_runs": total,
            "passed": passed,
            "failed": failed,
            "statuses": dict(statuses),
            "edge_cases": dict(edge_cases),
            "scenarios": dict(scenarios),
            "failing_runs": [
                {
                    "run_id": r.run_id,
                    "scenario_name": r.scenario_name,
                    "final_status": r.final_status,
                    "execution_result": r.execution_result,
                    "error_message": r.error_message,
                }
                for r in failing[:50]
            ],
        }
        json_dump(self.summary_json_path, summary_payload)

        lines = [
            "# Harness Summary",
            "",
            f"- Total runs: {total}",
            f"- Passed: {passed}",
            f"- Failed: {failed}",
            f"- CSV: `{self.csv_path.name}`",
            f"- Full report: `{self.full_report_path.name}`",
            f"- Summary JSON: `{self.summary_json_path.name}`",
            f"- Manifest: `{self.manifest_path.name}`",
            f"- Live log: `{self.live_log_path.relative_to(self.run_root)}`",
            "",
            "## Final statuses",
            "",
        ]
        for status, count in statuses.most_common():
            lines.append(f"- {status}: {count}")

        lines.extend(["", "## Scenarios", ""])
        for name, count in scenarios.most_common():
            lines.append(f"- {name}: {count}")

        lines.extend(["", "## Edge cases", ""])
        if edge_cases:
            for tag, count in edge_cases.most_common():
                lines.append(f"- {tag}: {count}")
        else:
            lines.append("- none")

        lines.extend(["", "## Failing runs", ""])
        if failing:
            for result in failing[:20]:
                lines.append(f"- {result.run_id}: {result.error_message or result.final_status}")
        else:
            lines.append("- none")

        self.summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        full = [
            "# Full Transaction Test Report",
            "",
            f"- Total runs: **{total}**",
            f"- Passed: **{passed}**",
            f"- Failed: **{failed}**",
            f"- CSV: `{self.csv_path.name}`",
            f"- Summary JSON: `{self.summary_json_path.name}`",
            f"- Manifest: `{self.manifest_path.name}`",
            f"- Live log: `{self.live_log_path.relative_to(self.run_root)}`",
            "",
            "## Scenario Breakdown",
            "",
        ]
        for scenario_name, items in sorted(by_scenario.items()):
            sc_passed = sum(1 for r in items if r.actual_pass)
            sc_failed = len(items) - sc_passed
            full.extend([
                f"### {scenario_name}",
                "",
                f"- Runs: {len(items)}",
                f"- Passed: {sc_passed}",
                f"- Failed: {sc_failed}",
                "",
                "| run_id | network | final_status | execution_result | gaslimit | gas_used | trace | state | receipt |",
                "|---|---|---|---|---:|---:|---|---|---|",
            ])
            for r in items:
                trace = "yes" if r.trace_collected else "no"
                state = "n/a" if r.state_match is None else ("match" if r.state_match else "mismatch")
                receipt = Path(r.receipt_path).name if r.receipt_path else ""
                full.append(
                    f"| {r.run_id} | {r.network} | {r.final_status} | {r.execution_result} | {r.gaslimit} | {r.gas_used or 0} | {trace} | {state} | `{receipt}` |"
                )
            full.append("")

        full.extend(["## Failing Runs Details", ""])
        if failing:
            for r in failing:
                full.extend([
                    f"### {r.run_id}",
                    "",
                    f"- Scenario: `{r.scenario_name}`",
                    f"- Network: `{r.network}`",
                    f"- tx_hash: `{r.tx_hash}`",
                    f"- Final status: `{r.final_status}`",
                    f"- Execution result: `{r.execution_result}`",
                    f"- Gas limit: `{r.gaslimit}`",
                    f"- Gas used: `{r.gas_used}`",
                    f"- Trace collected: `{r.trace_collected}`",
                    f"- Error: `{r.error_message}`",
                    f"- Receipt: `{r.receipt_path}`",
                    f"- Trace: `{r.trace_path}`",
                    f"- State: `{r.state_path}`",
                    f"- Raw: `{r.raw_path}`",
                    "",
                ])
        else:
            full.append("- none\n")

        full.extend([
            "## Artifact Layout",
            "",
            "- `receipts/` raw receipt payloads",
            "- `traces/` debug traces",
            "- `states/` state-read payloads",
            "- `raw/` merged submission/status/receipt/trace snapshots",
            "- `logs/live.log` live execution stream",
            "",
        ])
        self.full_report_path.write_text("\n".join(full) + "\n", encoding="utf-8")
