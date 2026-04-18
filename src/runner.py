from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from .adapters.base import BaseAdapter
from .gas_profiles import resolve_gaslimit
from .models import AppSettings, RunResult, Scenario
from .report_writer import ReportWriter
from .state_verifier import verify_state
from .status_watcher import wait_for_status
from .utils import now_utc, slugify


class ScenarioRunner:
    """Orchestrates the execution of test scenarios.

    The ScenarioRunner manages the lifecycle of scenario execution, including:
    - Parallel execution with ThreadPoolExecutor
    - Risk assessment based on gas limits
    - Error handling and retry logic
    - Metric collection and reporting

    Attributes:
        settings: Application configuration settings
        adapter: Execution adapter (mock or command)
        report_writer: Report generation handler
    """

    def __init__(
        self, settings: AppSettings, adapter: BaseAdapter, report_writer: ReportWriter
    ):
        self.settings = settings
        self.adapter = adapter
        self.report_writer = report_writer

    def run_scenarios(
        self,
        scenarios: List[Scenario],
        repeat_override: int | None = None,
        concurrency_override: int | None = None,
        debug_override: str | None = None,
        wait_status_override: str | None = None,
    ) -> List[RunResult]:
        """Execute a list of scenarios with optional configuration overrides.

        Args:
            scenarios: List of scenarios to execute
            repeat_override: Override scenario repeat count (default: use scenario config)
            concurrency_override: Override concurrency level (default: use scenario config)
            debug_override: Override debug mode (never|on-fail|always)
            wait_status_override: Override wait status (accepted|finalized)

        Returns:
            List of RunResult objects containing execution metrics and status

        Note:
            Scenarios are executed with ThreadPoolExecutor for parallel execution.
            Results are written incrementally to reports as they complete.
        """
        results: List[RunResult] = []
        for scenario in scenarios:
            repeat = (
                repeat_override if repeat_override is not None else scenario.run.repeat
            )
            concurrency = (
                concurrency_override
                if concurrency_override is not None
                else scenario.run.concurrency
            )
            self.report_writer.log_event(
                f"scenario-start name={scenario.name} file={scenario.file_path or ''} repeat={repeat} concurrency={concurrency} risk={self._risk_label(scenario)}"
            )
            futures = []
            with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
                for index in range(repeat):
                    futures.append(
                        pool.submit(
                            self._run_once_safe,
                            scenario,
                            index,
                            debug_override,
                            wait_status_override,
                        )
                    )
                for future in as_completed(futures):
                    result = future.result()
                    self.report_writer.append_result(result)
                    results.append(result)
        self.report_writer.write_summary()
        return results

    def _risk_label(self, scenario: Scenario) -> str:
        """Calculate risk label for a scenario based on configuration.

        Risk factors include:
        - Very low gas limits (likely OUT_OF_FEE)
        - Borderline gas limits (risky)
        - Forced revert behavior
        - Nondeterministic execution
        - Concurrent execution
        - Expected failures

        Args:
            scenario: Scenario to assess

        Returns:
            Comma-separated risk labels (e.g., "risky-gas,concurrency")
        """
        flags = []
        gaslimit, _ = resolve_gaslimit(scenario.gas_profile, self.settings)
        if gaslimit <= self.settings.gas_thresholds.fail_below:
            flags.append("very-likely-error")
        elif gaslimit <= self.settings.gas_thresholds.borderline_below:
            flags.append("risky-gas")
        if scenario.behavior.force_revert:
            flags.append("forced-revert")
        if scenario.behavior.nondeterministic:
            flags.append("nondeterministic")
        if (scenario.run.concurrency or 1) > 1:
            flags.append("concurrency")
        if scenario.expect.expect_possible_failure or scenario.expect.expect_out_of_fee:
            flags.append("expected-failure")
        return ",".join(flags) or "normal"

    def _run_once_safe(
        self,
        scenario: Scenario,
        iteration: int,
        debug_override: str | None,
        wait_status_override: str | None,
    ) -> RunResult:
        """Execute a single scenario iteration with exception handling.

        Wraps _run_once() to catch and convert exceptions into RunResult
        objects with error information. This ensures that one failed scenario
        doesn't crash the entire test suite.

        Args:
            scenario: Scenario to execute
            iteration: Iteration number (0-based)
            debug_override: Optional debug mode override
            wait_status_override: Optional wait status override

        Returns:
            RunResult with execution status or error information
        """
        try:
            return self._run_once(
                scenario, iteration, debug_override, wait_status_override
            )
        except Exception as exc:
            run_id = f"{slugify(scenario.name)}-{iteration + 1:03d}"
            error_payload = {"error": str(exc), "scenario": scenario.name}
            self.report_writer.log_event(
                f"run-error run_id={run_id} scenario={scenario.name} error={exc}"
            )
            paths = self.report_writer.write_payloads(
                run_id, error_payload, None, None, {"error": str(exc)}
            )
            return RunResult(
                run_id=run_id,
                scenario_name=scenario.name,
                scenario_file=scenario.file_path or "",
                network=scenario.network or self.settings.default_network,
                kind=scenario.kind,
                tx_hash="",
                contract_address=scenario.contract.address,
                function_name=scenario.contract.function_name,
                args_json=json.dumps(
                    scenario.contract.args
                    if scenario.kind == "write"
                    else scenario.contract.constructor_args
                ),
                gas_profile_name=scenario.gas_profile.preset
                or scenario.gas_profile.mode,
                gaslimit=scenario.gas_profile.gaslimit or 0,
                wait_status=wait_status_override
                or scenario.run.wait_status
                or self.settings.default_wait_status,
                debug_mode=debug_override
                or scenario.run.debug
                or self.settings.default_debug,
                final_status="HARNESS_ERROR",
                execution_result="HARNESS_ERROR",
                result_code=None,
                gas_used=None,
                duration_ms=0,
                trace_collected=False,
                expected_pass=False,
                actual_pass=False,
                state_match=None,
                edge_case_tag="harness_error",
                error_message=str(exc),
                receipt_path=paths["receipt_path"],
                trace_path="",
                state_path="",
                raw_path=paths["raw_path"],
                created_at=now_utc().isoformat(),
                tags=",".join(scenario.run.tags),
            )

    def _run_once(
        self,
        scenario: Scenario,
        iteration: int,
        debug_override: str | None,
        wait_status_override: str | None,
    ) -> RunResult:
        """Execute a single scenario iteration.

        Execution flow:
        1. Resolve gas limit from profile
        2. Submit transaction via adapter
        3. Poll transaction status until target state
        4. Retrieve receipt and optional trace
        5. Verify contract state if configured
        6. Determine pass/fail status
        7. Write payloads to disk

        Args:
            scenario: Scenario to execute
            iteration: Iteration number (0-based)
            debug_override: Optional debug mode override
            wait_status_override: Optional wait status override

        Returns:
            RunResult containing all execution metrics and status

        Raises:
            RuntimeError: If submission fails or required data is missing
            TimeoutError: If transaction doesn't reach target status in time
        """
        gaslimit, gas_profile_name = resolve_gaslimit(
            scenario.gas_profile, self.settings
        )
        run_id = f"{slugify(scenario.name)}-{iteration + 1:03d}"
        network = scenario.network or self.settings.default_network
        debug_mode = debug_override or scenario.run.debug or self.settings.default_debug
        wait_status = (
            wait_status_override
            or scenario.run.wait_status
            or self.settings.default_wait_status
        )
        timeout_seconds = scenario.run.timeout_seconds or self.settings.timeout_seconds
        poll_interval_seconds = (
            scenario.run.poll_interval_seconds or self.settings.poll_interval_seconds
        )

        self.report_writer.log_event(
            f"run-start run_id={run_id} scenario={scenario.name} network={network} gaslimit={gaslimit} wait_status={wait_status} debug={debug_mode}"
        )
        started_at = now_utc()
        submission = self.adapter.submit(scenario, network, gaslimit)
        self.report_writer.log_event(
            f"submitted run_id={run_id} tx_hash={submission.tx_hash} contract={submission.contract_address or scenario.contract.address or ''}"
        )
        timeline, status_payload = wait_for_status(
            self.adapter,
            submission.tx_hash,
            wait_status,
            timeout_seconds,
            poll_interval_seconds,
            network=network,
            on_status=lambda status, payload: self.report_writer.log_event(
                f"status run_id={run_id} tx_hash={submission.tx_hash} status={status} execution_result={payload.get('execution_result', '')}"
            ),
        )
        receipt = self.adapter.get_receipt(submission.tx_hash, network=network)
        final_status = str(
            receipt.get("status") or status_payload.get("status") or "UNKNOWN"
        ).upper()
        execution_result = str(
            receipt.get("execution_result")
            or status_payload.get("execution_result")
            or "UNKNOWN"
        ).upper()
        result_code = receipt.get("result_code", status_payload.get("result_code"))
        gas_used = receipt.get("gas_used", status_payload.get("gas_used"))
        should_trace = debug_mode == "always" or (
            debug_mode == "on-fail" and execution_result != "FINISHED_WITH_RETURN"
        )
        trace = (
            self.adapter.get_trace(submission.tx_hash, network=network)
            if should_trace
            else None
        )
        if trace is not None:
            self.report_writer.log_event(
                f"trace-collected run_id={run_id} tx_hash={submission.tx_hash}"
            )
        state_match, state_payload, state_note = verify_state(
            self.adapter,
            scenario,
            submission.contract_address or receipt.get("contract_address"),
            network=network,
        )

        actual_pass = final_status in {
            s.upper() for s in scenario.expect.allowed_final_statuses
        }
        actual_pass = actual_pass and execution_result in {
            s.upper() for s in scenario.expect.allowed_execution_results
        }
        if state_match is False and execution_result == "FINISHED_WITH_RETURN":
            actual_pass = False
        duration_ms = int((now_utc() - started_at).total_seconds() * 1000)

        edge_case_tag = ""
        if final_status == "OUT_OF_FEE":
            edge_case_tag = "out_of_fee"
        elif execution_result == "FINISHED_WITH_ERROR":
            edge_case_tag = "execution_error"
        elif scenario.behavior.nondeterministic:
            edge_case_tag = "nondeterministic"
        elif (scenario.run.concurrency or 1) > 1:
            edge_case_tag = "concurrency"

        raw = {
            "submission": submission.raw,
            "timeline": timeline,
            "status_payload": status_payload,
            "receipt": receipt,
            "trace": trace,
            "state": state_payload,
        }
        payload_paths = self.report_writer.write_payloads(
            run_id, receipt, trace, state_payload, raw
        )

        error_message = ""
        if not actual_pass:
            error_message = (
                state_note
                if state_match is False
                else f"unexpected final_status={final_status} execution_result={execution_result}"
            )
        self.report_writer.log_event(
            f"run-finish run_id={run_id} tx_hash={submission.tx_hash} final_status={final_status} execution_result={execution_result} gas_used={gas_used} pass={actual_pass}"
        )

        return RunResult(
            run_id=run_id,
            scenario_name=scenario.name,
            scenario_file=scenario.file_path or "",
            network=network,
            kind=scenario.kind,
            tx_hash=submission.tx_hash,
            contract_address=submission.contract_address
            or receipt.get("contract_address"),
            function_name=scenario.contract.function_name,
            args_json=json.dumps(
                scenario.contract.args
                if scenario.kind == "write"
                else scenario.contract.constructor_args,
                ensure_ascii=False,
            ),
            gas_profile_name=gas_profile_name,
            gaslimit=gaslimit,
            wait_status=wait_status,
            debug_mode=debug_mode,
            final_status=final_status,
            execution_result=execution_result,
            result_code=result_code,
            gas_used=gas_used,
            duration_ms=duration_ms,
            trace_collected=trace is not None,
            expected_pass=not scenario.expect.expect_possible_failure
            and not scenario.expect.expect_out_of_fee,
            actual_pass=actual_pass,
            state_match=state_match,
            edge_case_tag=edge_case_tag,
            error_message=error_message,
            receipt_path=payload_paths["receipt_path"],
            trace_path=payload_paths["trace_path"],
            state_path=payload_paths["state_path"],
            raw_path=payload_paths["raw_path"],
            created_at=now_utc().isoformat(),
            tags=",".join(scenario.run.tags),
        )
