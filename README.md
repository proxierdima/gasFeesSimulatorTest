# Gas Fees Simulator Tests

Comprehensive testing framework for reproducing and validating GenLayer's Gas Simulator scenarios on Testnet Bradbury. This project tests various gas limit configurations, documents edge cases, and validates blockchain transaction execution behavior.

## 🎯 Project Goals

- **Reproduce** GenLayer Gas Simulator scenarios through automated testing
- **Validate** gas limit behavior across different configurations (low, borderline, normal, high)
- **Document** edge cases and failure modes in gas fee handling
- **Report** detailed execution metrics and transaction traces

## 📋 Features

- ✅ **Multiple Test Scenarios**: Low gas, borderline, high gas, concurrent transactions
- ✅ **Automated Deployment**: Fresh contract deployment for each test run
- ✅ **Comprehensive Reporting**: CSV, JSON, and Markdown reports with detailed metrics
- ✅ **State Verification**: Post-execution state validation
- ✅ **Trace Collection**: Automatic trace collection on failures
- ✅ **Flexible Execution**: Mock and command adapters for testing and production
- ✅ **Concurrent Testing**: Parallel scenario execution with configurable concurrency

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **npm**: 8 or higher
- **GenLayer Account**: Testnet account with test tokens

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd glh_v4
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your private key:
   ```env
   HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
   HARNESS_DEFAULT_NETWORK=bradbury
   GLH_TEST_CONTRACT_FILE=contracts/fixtures/sample_contract.py
   ```

   ⚠️ **Security**: Never commit your `.env` file!

### Running Tests

**Quick run with bash wrapper**:
```bash
./run.sh ~/glh_v4
```

**With custom password** (legacy):
```bash
PASSWORD='12345678' ./run.sh ~/glh_v4
```

**Direct Python execution**:
```bash
python main.py --project-root . --out artifacts
```

**Run specific scenario**:
```bash
python -m src.main --scenario scenarios/low_gas.yaml --adapter command
```

**Mock mode (no blockchain)**:
```bash
python -m src.main --scenario scenarios/deterministic_baseline.yaml --adapter mock
```

## 📊 Test Suites

### Group A: Gas Limit Tests
- `deterministic_baseline.yaml` - Normal gas baseline
- `low_gas.yaml` - Insufficient gas (OUT_OF_FEE expected)
- `borderline_gas.yaml` - Risky gas limit
- `high_gas.yaml` - Overprovision gas
- `concurrent_same_sender.yaml` - Concurrent transactions

### Group B: Edge Cases
- `report_01_baseline.yaml` - Baseline validation
- `report_02_low_gas.yaml` - Low gas edge case
- `report_03_borderline.yaml` - Borderline behavior
- `report_04_high_gas.yaml` - High gas validation
- `report_05_invalid_fn.yaml` - Invalid function call
- `report_06_concurrent.yaml` - Concurrency testing

## 📁 Project Structure

```
glh_v4/
├── artifacts/              # Test results and reports
├── backends/              # Node.js blockchain backends
├── config/                # Configuration files
├── contracts/             # Smart contracts for testing
├── scenarios/             # YAML test scenarios
├── scripts/               # Helper scripts
├── src/                   # Core harness implementation
│   ├── adapters/          # Execution adapters
│   ├── models.py          # Data models
│   ├── runner.py          # Scenario execution
│   └── report_writer.py   # Report generation
├── tests/                 # Unit tests
├── main.py                # Main orchestrator
└── run.sh                 # Quick run script
```

## 🔧 Configuration

### Gas Profiles

Configured in `config/defaults.yaml`:

```yaml
gas_thresholds:
  fail_below: 40        # Very likely OUT_OF_FEE
  borderline_below: 65  # Risky
  normal: 90            # Safe
  high: 140             # Overprovision
```

### Scenario Format

```yaml
name: my_scenario
kind: write  # or deploy
network: bradbury

contract:
  address: "${GLH_TEST_CONTRACT_ADDRESS}"
  function_name: "update_storage"
  args: ["test_value"]

run:
  repeat: 5
  concurrency: 1
  wait_status: finalized
  debug: on-fail
  timeout_seconds: 60

gas_profile:
  mode: preset  # or custom
  preset: normal  # low, borderline, normal, high

expect:
  allowed_final_statuses: [FINALIZED]
  allowed_execution_results: [FINISHED_WITH_RETURN]
  state_check:
    enabled: true
    function_name: "get_storage"
    expected: "test_value"
```

## 📈 Reports

After execution, find reports in `artifacts/<timestamp>/`:

- **runs.csv**: Detailed per-run metrics
- **summary.json**: Aggregated statistics
- **report.md**: Human-readable analysis
- **live.log**: Real-time event log
- **<run_id>/**: Per-run payloads (receipt, trace, state)

### Example Output

```
Run root: artifacts/2026-04-17_20-30-45
Results: total=15 passed=13 failed=2
CSV: artifacts/2026-04-17_20-30-45/runs.csv
Summary: artifacts/2026-04-17_20-30-45/summary.json
```

## 🧪 Testing

Run unit tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detailed system architecture
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development guidelines
- **[scenarios/](scenarios/)**: Scenario documentation

## 🐛 Troubleshooting

### Common Issues

**OUT_OF_FEE errors**:
- Increase gas limit in scenario or use higher preset

**Transaction not visible**:
- Increase `timeout_seconds` in scenario
- Check RPC endpoint health

**State mismatch**:
- Verify contract behavior is deterministic
- Check expected values in scenario

**npm install fails**:
- Ensure Node.js 18+ is installed
- Use `--skip-npm-install` if already installed

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

[Add license information here]

## 🔗 Links

- **GenLayer Docs**: https://docs.genlayer.com
- **Bradbury Testnet**: https://rpc-bradbury.genlayer.com
- **genlayer-js SDK**: https://github.com/yeagerai/genlayer-js

## ✨ Recent Improvements

- ✅ Fixed type annotations for better IDE support
- ✅ Removed legacy patch files
- ✅ Added environment validation
- ✅ Refactored common utilities
- ✅ Comprehensive documentation added

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-17  
**Network**: Bradbury Testnet
