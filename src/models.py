from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class GasThresholds:
    fail_below: int = 40
    borderline_below: int = 65
    normal: int = 90
    high: int = 140


@dataclass
class AppSettings:
    adapter_mode: str = "mock"
    output_dir: str = "artifacts"
    default_network: str = "bradbury"
    default_wait_status: str = "finalized"
    default_debug: str = "on-fail"
    poll_interval_seconds: float = 0.75
    timeout_seconds: float = 45.0
    random_seed: int = 42
    rpc_url: str = ""
    private_key: str = ""
    gas_thresholds: GasThresholds = field(default_factory=GasThresholds)
    command_submit_write: str = ""
    command_submit_deploy: str = ""
    command_status: str = ""
    command_receipt: str = ""
    command_trace: str = ""
    command_read_state: str = ""
    command_retries: int = 3
    command_retry_backoff_seconds: float = 1.0
    trace_round: int = 0
    networks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    verbose: bool = False
    print_logs: bool = False

    def sanitized(self) -> Dict[str, Any]:
        data = asdict(self)
        if data.get("private_key"):
            pk = str(data["private_key"])
            data["private_key"] = f"***{pk[-6:]}"
        return data


@dataclass
class ContractSpec:
    address: Optional[str] = None
    function_name: Optional[str] = None
    args: List[Any] = field(default_factory=list)
    contract_file: Optional[str] = None
    constructor_args: List[Any] = field(default_factory=list)


@dataclass
class RunSpec:
    repeat: int = 1
    concurrency: int = 1
    wait_status: str = "finalized"
    debug: str = "on-fail"
    timeout_seconds: float = 45.0
    poll_interval_seconds: float = 0.75
    tags: List[str] = field(default_factory=list)


@dataclass
class GasProfile:
    mode: str = "preset"
    preset: Optional[str] = None
    gaslimit: Optional[int] = None
    tip_for_appeal: int = 0
    note: str = ""


@dataclass
class StateCheck:
    enabled: bool = False
    function_name: Optional[str] = None
    args: List[Any] = field(default_factory=list)
    expected: Any = None


@dataclass
class ExpectSpec:
    allowed_final_statuses: List[str] = field(default_factory=lambda: ["FINALIZED"])
    allowed_execution_results: List[str] = field(default_factory=lambda: ["FINISHED_WITH_RETURN"])
    expect_out_of_fee: bool = False
    expect_possible_failure: bool = False
    state_check: StateCheck = field(default_factory=StateCheck)


@dataclass
class BehaviorSpec:
    base_required_gas: int = 60
    appeal_like: bool = False
    nondeterministic: bool = False
    force_revert: bool = False
    state_key: str = "storage"
    artificial_delay_ms: int = 500
    rpc_flaky: bool = False


@dataclass
class Scenario:
    name: str
    kind: str
    network: str
    contract: ContractSpec = field(default_factory=ContractSpec)
    run: RunSpec = field(default_factory=RunSpec)
    gas_profile: GasProfile = field(default_factory=GasProfile)
    expect: ExpectSpec = field(default_factory=ExpectSpec)
    behavior: BehaviorSpec = field(default_factory=BehaviorSpec)
    file_path: Optional[str] = None


@dataclass
class SubmissionResult:
    tx_hash: str
    network: str
    submitted_at: datetime
    raw: Dict[str, Any] = field(default_factory=dict)
    contract_address: Optional[str] = None


@dataclass
class RunResult:
    run_id: str
    scenario_name: str
    scenario_file: str
    network: str
    kind: str
    tx_hash: str
    contract_address: Optional[str]
    function_name: Optional[str]
    args_json: str
    gas_profile_name: str
    gaslimit: int
    wait_status: str
    debug_mode: str
    final_status: str
    execution_result: str
    result_code: Optional[int]
    gas_used: Optional[int]
    duration_ms: int
    trace_collected: bool
    expected_pass: bool
    actual_pass: bool
    state_match: Optional[bool]
    edge_case_tag: str
    error_message: str
    receipt_path: str
    trace_path: str
    state_path: str
    raw_path: str
    created_at: str
    tags: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
