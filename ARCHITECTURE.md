# Gas Fees Simulator Tests - Architecture Documentation

## Overview

The Gas Fees Simulator Tests project is a comprehensive testing framework designed to reproduce and validate GenLayer's Gas Simulator scenarios on the Bradbury Testnet. The system tests various gas limit configurations and documents edge cases in blockchain transaction execution.

## Project Structure

```
glh_v4/
├── artifacts/              # Test execution results and reports
├── backends/              # Node.js backends for blockchain interaction
│   ├── onchain_common.mjs           # Shared utilities for blockchain ops
│   ├── onchain_submit_deploy.mjs    # Contract deployment backend
│   ├── onchain_submit_write.mjs     # Contract write operations backend
│   └── read_state_backend.py        # State reading utilities
├── config/                # Configuration files
│   ├── defaults.yaml      # Default harness settings
│   └── networks.yaml      # Network configurations (Bradbury, Asimov)
├── contracts/             # Smart contracts for testing
│   └── fixtures/
│       └── sample_contract.py       # WizardOfCoin test contract
├── scenarios/             # Test scenario definitions (YAML)
│   ├── report_bootstrap/            # Initial deployment scenarios
│   ├── report_suite_group_a/        # Gas limit test suite A
│   └── report_suite_group_b/        # Gas limit test suite B
├── scripts/               # Helper scripts for RPC operations
│   ├── _common.py         # Shared utilities and backend runner
│   ├── submit_deploy.py   # Deploy transaction submission
│   ├── submit_write.py    # Write transaction submission
│   ├── get_status.py      # Transaction status polling
│   ├── get_receipt.py     # Receipt retrieval
│   ├── get_trace.py       # Execution trace retrieval
│   └── read_state.py      # Contract state reading
├── src/                   # Core harness implementation
│   ├── adapters/          # Adapter pattern for execution backends
│   │   ├── base.py        # Abstract adapter interface
│   │   ├── command.py     # Command-line adapter (production)
│   │   ├── mock.py        # Mock adapter (testing)
│   │   └── factory.py     # Adapter factory
│   ├── config.py          # Configuration loading
│   ├── gas_profiles.py    # Gas limit profile resolution
│   ├── main.py            # Harness entry point
│   ├── models.py          # Data models (Scenario, RunResult, etc.)
│   ├── report_writer.py   # Report generation (CSV, JSON, Markdown)
│   ├── runner.py          # Scenario execution orchestration
│   ├── scenario_loader.py # YAML scenario parsing
│   ├── state_verifier.py  # Post-execution state validation
│   ├── status_watcher.py  # Transaction status polling
│   └── utils.py           # Utility functions
├── tests/                 # Unit tests
├── main.py                # Orchestrator script (deploy + run suites)
├── run.sh                 # Bash wrapper for quick execution
└── requirements.txt       # Python dependencies

```

## Architecture Layers

### 1. Orchestration Layer (`main.py`)

**Responsibility**: High-level test execution flow

**Key Functions**:
- Environment validation
- Node.js dependency installation
- Fresh contract deployment
- Sequential execution of test suite groups
- Result aggregation and reporting

**Flow**:
```
1. Validate environment (HARNESS_PRIVATE_KEY, etc.)
2. Install npm dependencies (genlayer-js, viem)
3. Deploy fixture contract → extract contract address
4. Run Group A scenarios (low_gas, borderline, high_gas, concurrent)
5. Run Group B scenarios (baseline, edge cases)
6. Generate consolidated reports
```

### 2. Harness Core (`src/`)

#### 2.1 Scenario Loader (`scenario_loader.py`)
- Parses YAML scenario files
- Supports environment variable interpolation (`${VAR}`)
- Validates scenario structure
- Loads single files or entire directories

#### 2.2 Runner (`runner.py`)
- Executes scenarios with configurable repeat/concurrency
- Implements ThreadPoolExecutor for parallel execution
- Calculates risk scores based on gas limits
- Handles retries and error recovery
- Collects execution metrics (duration, gas used, etc.)

#### 2.3 Adapters (`adapters/`)

**Adapter Pattern**: Abstracts execution backend

- **MockAdapter**: In-memory simulation for unit tests
- **CommandAdapter**: Executes real blockchain operations via shell commands
- **Factory**: Creates appropriate adapter based on configuration

**CommandAdapter Flow**:
```
1. Expand template with scenario parameters
2. Execute shell command (Python script or Node.js backend)
3. Parse JSON output from stdout
4. Extract tx_hash, contract_address, etc.
5. Retry on failure (configurable retries + backoff)
```

#### 2.4 Status Watcher (`status_watcher.py`)
- Polls transaction status until target state (ACCEPTED/FINALIZED)
- Implements exponential backoff
- Timeout handling
- Timeline tracking for debugging

#### 2.5 State Verifier (`state_verifier.py`)
- Reads contract state after transaction
- Compares actual vs expected values
- Supports nested object comparison
- Returns match status + diagnostic notes

#### 2.6 Report Writer (`report_writer.py`)
- Generates multiple output formats:
  - **CSV**: Tabular data for analysis
  - **JSON**: Machine-readable summary
  - **Markdown**: Human-readable report
  - **Live log**: Real-time event stream
- Writes per-run payloads (receipt, trace, state)

### 3. Backend Layer

#### 3.1 Node.js Backends (`backends/*.mjs`)

**Technology**: genlayer-js SDK + viem

**onchain_submit_deploy.mjs**:
- Reads contract bytecode from file
- Creates deployment transaction with gas overrides
- Waits for transaction visibility
- Verifies gas limit was applied correctly
- Returns tx_hash + contract_address

**onchain_submit_write.mjs**:
- Calls contract function with specified args
- Applies gas limit overrides
- Verifies gas on-chain via RPC
- Returns tx_hash + gas verification status

**onchain_common.mjs**:
- Shared utilities (JSON parsing, gas extraction, etc.)
- Chain resolution (Bradbury vs Asimov)
- Private key management
- Transaction polling with retries

#### 3.2 Python Scripts (`scripts/*.py`)

**Purpose**: Wrapper layer between harness and Node.js backends

**_common.py**:
- `run_backend_template()`: Template expansion + subprocess execution
- `rpc_call()`: Direct JSON-RPC calls with curl fallback
- `add_shell_vars()`: Shell-safe variable quoting
- `_extract_last_json_payload()`: Robust JSON parsing from stdout

**submit_deploy.py / submit_write.py**:
- Parse command-line arguments
- Call Node.js backend via `run_backend_template()`
- Handle non-zero exit codes with tx_hash salvage
- Output JSON to stdout

**get_status.py / get_receipt.py / get_trace.py**:
- RPC wrappers for transaction queries
- Hex decoding for error messages
- Structured JSON output

### 4. Configuration Layer

#### 4.1 YAML Scenarios

**Structure**:
```yaml
name: scenario_name
kind: write | deploy
network: bradbury

contract:
  address: "${GLH_TEST_CONTRACT_ADDRESS}"  # Env var interpolation
  function_name: "ask_for_coin"
  args: ["argument1", "argument2"]

run:
  repeat: 5                    # Number of executions
  concurrency: 1               # Parallel execution count
  wait_status: accepted        # ACCEPTED | FINALIZED
  debug: on-fail               # never | on-fail | always
  timeout_seconds: 120
  poll_interval_seconds: 1.0
  tags: [low-gas, edge-case]

gas_profile:
  mode: preset | custom
  preset: low | borderline | normal | high
  gaslimit: 40                 # Custom gas limit

expect:
  allowed_final_statuses: [FINALIZED, OUT_OF_FEE]
  allowed_execution_results: [FINISHED_WITH_RETURN, FINISHED_WITH_ERROR]
  expect_possible_failure: true
  state_check:
    enabled: true
    function_name: "get_storage"
    expected: "expected_value"

behavior:
  base_required_gas: 60
  nondeterministic: false
```

#### 4.2 Gas Profiles (`gas_profiles.py`)

**Presets**:
- `low`: 35 (likely OUT_OF_FEE)
- `borderline`: 65 (risky)
- `normal`: 90 (safe)
- `high`: 140 (overprovision)

**Custom**: Explicit gaslimit value

### 5. Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (Orchestrator)                  │
│  1. Deploy fixture contract                                  │
│  2. Extract contract_address → env var                       │
│  3. Run test suites sequentially                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   src/main.py (Harness)                      │
│  - Load scenarios from YAML                                  │
│  - Create adapter (mock | command)                           │
│  - Execute scenarios with runner                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  ScenarioRunner (runner.py)                  │
│  - ThreadPoolExecutor for concurrency                        │
│  - Per-scenario execution loop                               │
│  - Error handling + retry logic                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              CommandAdapter (adapters/command.py)            │
│  1. Expand template: {rpc_url}, {gaslimit}, etc.            │
│  2. Execute: python scripts/submit_write.py ...             │
│  3. Parse JSON from stdout                                   │
│  4. Extract tx_hash                                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Python Script (scripts/submit_write.py)            │
│  1. Parse args (--rpc, --contract, --fn, --args, --gaslimit)│
│  2. Call run_backend_template() with Node.js backend        │
│  3. Output JSON: {tx_hash, gaslimit_verified, ...}          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│      Node.js Backend (backends/onchain_submit_write.mjs)     │
│  1. Create genlayer-js client with private key              │
│  2. Call client.writeContract() with gas overrides          │
│  3. Wait for transaction visibility                         │
│  4. Verify gas limit via RPC                                │
│  5. Return JSON: {tx_hash, gaslimit_onchain, ...}           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              GenLayer Bradbury Testnet (RPC)                 │
│  - Process transaction                                       │
│  - Execute smart contract                                    │
│  - Return status: ACCEPTED → FINALIZED                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           StatusWatcher (status_watcher.py)                  │
│  - Poll transaction status every N seconds                   │
│  - Wait for target status (ACCEPTED | FINALIZED)             │
│  - Timeout after configured duration                         │
│  - Return timeline + final status payload                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           StateVerifier (state_verifier.py)                  │
│  - Read contract state via read_state backend               │
│  - Compare actual vs expected values                         │
│  - Return match status + diagnostic notes                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            ReportWriter (report_writer.py)                   │
│  - Write CSV row: run_id, tx_hash, gas_used, pass/fail      │
│  - Write JSON payloads: receipt, trace, state                │
│  - Generate summary.json: total, passed, failed              │
│  - Generate markdown report with analysis                    │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Adapter Pattern
- **Purpose**: Abstract execution backend (mock vs real blockchain)
- **Benefits**: Testability, flexibility, separation of concerns

### 2. Template Method Pattern
- **Purpose**: Command template expansion with variable substitution
- **Example**: `--rpc {rpc_url_sh} --gaslimit {gaslimit_sh}`

### 3. Strategy Pattern
- **Purpose**: Gas profile resolution (preset vs custom)
- **Benefits**: Extensible gas limit strategies

### 4. Observer Pattern
- **Purpose**: Status polling with callbacks
- **Benefits**: Real-time logging, progress tracking

## Error Handling Strategy

### 1. Retry Logic
- **Location**: `CommandAdapter._run_template()`
- **Configuration**: `command_retries`, `command_retry_backoff_seconds`
- **Strategy**: Exponential backoff

### 2. Non-Zero Exit Code Salvage
- **Purpose**: Extract tx_hash even if backend exits non-zero
- **Use Case**: Transaction submitted but backend crashes
- **Implementation**: `allow_nonzero_with_tx_hash=True`

### 3. Timeout Handling
- **Transaction Polling**: Configurable per-scenario timeout
- **RPC Calls**: 60-second default timeout with curl fallback

### 4. State Mismatch
- **Detection**: Compare actual vs expected state
- **Action**: Mark test as failed, log diagnostic note
- **Reporting**: Include in CSV + JSON output

## Security Considerations

### 1. Private Key Management
- **Storage**: Environment variable (`HARNESS_PRIVATE_KEY`)
- **Never logged**: Sanitized in reports
- **Validation**: Required at startup

### 2. Shell Injection Prevention
- **Method**: `shlex.quote()` for all user inputs
- **Scope**: Template expansion, command execution

### 3. RPC Endpoint Validation
- **Configuration**: Hardcoded in `networks.yaml`
- **No user input**: Prevents malicious RPC URLs

## Performance Optimization

### 1. Concurrency
- **ThreadPoolExecutor**: Parallel scenario execution
- **Configuration**: Per-scenario `concurrency` setting
- **Limitation**: Same sender = sequential (nonce conflicts)

### 2. Caching
- **Node modules**: Check before npm install
- **Contract deployment**: Reuse address across test suites

### 3. Incremental Reporting
- **CSV append**: Write results as they complete
- **Live log**: Real-time event stream
- **Summary**: Generated at end

## Testing Strategy

### 1. Unit Tests
- **Location**: `tests/`
- **Coverage**: Adapters, parsers, utilities
- **Framework**: pytest

### 2. Integration Tests
- **Mock Adapter**: End-to-end without blockchain
- **Scenario Validation**: YAML parsing + execution

### 3. E2E Tests
- **Command Adapter**: Real blockchain transactions
- **Test Suites**: Group A + Group B scenarios

## Deployment

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm packages: `genlayer-js`, `viem`
- Environment: `.env` with `HARNESS_PRIVATE_KEY`

### Execution
```bash
# Quick run
./run.sh ~/glh_v4

# Custom configuration
python main.py --project-root . --out artifacts --password <pwd>

# Direct harness invocation
python -m src.main --scenario scenarios/low_gas.yaml --adapter command
```

## Monitoring & Observability

### 1. Logs
- **Live log**: `artifacts/<timestamp>/live.log`
- **Stdout**: Real-time command output (if `--print-logs`)

### 2. Metrics
- **CSV**: Per-run metrics (gas_used, duration_ms, etc.)
- **Summary JSON**: Aggregated pass/fail counts

### 3. Traces
- **Collection**: On failure or `debug: always`
- **Storage**: `artifacts/<timestamp>/<run_id>/trace.json`

## Future Enhancements

1. **Parallel Test Suites**: Run Group A + B concurrently
2. **Database Storage**: PostgreSQL for historical analysis
3. **Grafana Dashboard**: Real-time metrics visualization
4. **CI/CD Integration**: GitHub Actions for automated testing
5. **Gas Estimation**: Pre-flight gas estimation before submission
6. **Multi-Network**: Support for multiple testnets simultaneously
7. **Contract Fuzzing**: Randomized input generation
8. **Performance Benchmarking**: Gas optimization tracking over time

## Troubleshooting

### Common Issues

**1. OUT_OF_FEE errors**
- **Cause**: Gas limit too low
- **Solution**: Increase `gaslimit` or use higher preset

**2. Transaction not visible**
- **Cause**: Network congestion or RPC lag
- **Solution**: Increase `timeout_seconds`, check RPC health

**3. State mismatch**
- **Cause**: Nondeterministic contract behavior
- **Solution**: Set `behavior.nondeterministic: true`

**4. npm install fails**
- **Cause**: Network issues or missing Node.js
- **Solution**: Use `--skip-npm-install` if already installed

## References

- **GenLayer Docs**: https://docs.genlayer.com
- **genlayer-js SDK**: https://github.com/yeagerai/genlayer-js
- **Bradbury Testnet**: https://rpc-bradbury.genlayer.com

---

**Last Updated**: 2026-04-17  
**Version**: 1.0.0  
**Maintainer**: GenLayer QA Team