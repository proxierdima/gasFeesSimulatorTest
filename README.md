# Gas Fees Simulator Tests

A comprehensive testing framework for validating GenLayer's gas fee behavior on Bradbury Testnet. This project automates contract deployment, transaction execution, and detailed reporting across various gas limit configurations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

## 🎯 Overview

This testing framework reproduces and validates GenLayer's Gas Simulator scenarios through automated testing on Bradbury Testnet. It provides:

- **Automated Testing**: 18+ pre-configured test scenarios covering all gas configurations
- **Real Blockchain Validation**: Direct integration with GenLayer Bradbury Testnet
- **Comprehensive Reporting**: Detailed metrics in CSV, JSON, and Markdown formats
- **Edge Case Detection**: Identifies and documents boundary conditions and failure modes
- **Cross-Platform Support**: Works on Windows, Linux, and macOS

## ✨ Features

- ✅ Multiple gas configurations (low, borderline, normal, high)
- ✅ Concurrent transaction testing
- ✅ Automatic contract deployment per test run
- ✅ Transaction status monitoring with detailed logging
- ✅ State verification and trace collection
- ✅ Mock adapter for offline development
- ✅ Configurable timeouts and retry logic
- ✅ Windows-compatible execution

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher
- **npm**: 8 or higher
- **GenLayer Account**: Testnet account with private key

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/proxierdima/gasFeesSimulatorTest.git
cd gasFeesSimulatorTest
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Required
HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HARNESS_DEFAULT_NETWORK=bradbury

# Optional
GLH_TEST_CONTRACT_FILE=contracts/fixtures/sample_contract.py
HARNESS_ADAPTER_MODE=command
HARNESS_OUTPUT_DIR=artifacts
```

⚠️ **Security Warning**: Never commit your `.env` file! It's already in `.gitignore`.

### 4. Run Tests

**Windows:**
```bash
python main.py --project-root "C:\path\to\gasFeesSimulatorTest" --password 12345678
```

**Linux/Mac:**
```bash
python main.py --project-root ~/gasFeesSimulatorTest --password 12345678
```

**Using the wrapper script:**
```bash
./run.sh ~/gasFeesSimulatorTest
```

## 📊 Test Scenarios

### Gas Limit Tests
- `deterministic_baseline.yaml` - Normal gas baseline
- `low_gas.yaml` - Insufficient gas (OUT_OF_FEE expected)
- `borderline_gas.yaml` - Risky gas limit
- `high_gas.yaml` - Excessive gas
- `concurrent_same_sender.yaml` - Parallel transactions

### Edge Cases
- `report_01_baseline.yaml` - Basic validation
- `report_02_low_gas.yaml` - Low gas edge case
- `report_03_borderline.yaml` - Boundary behavior
- `report_04_high_gas.yaml` - High gas validation
- `report_05_invalid_fn.yaml` - Invalid function call
- `report_06_concurrent.yaml` - Concurrency testing

### Bootstrap
- `deploy_fixture.yaml` - Contract deployment

## 🔧 Advanced Usage

### Run Specific Scenario

```bash
python -m src.main \
  --scenario scenarios/low_gas.yaml \
  --adapter command
```

### Mock Mode (No Blockchain)

```bash
python -m src.main \
  --scenario scenarios/deterministic_baseline.yaml \
  --adapter mock
```

### Check Transaction Status

```bash
python scripts/get_status.py \
  --rpc https://rpc-bradbury.genlayer.com \
  --tx 0xYOUR_TX_HASH
```

### Run Unit Tests

```bash
pytest tests/
```

## 📁 Project Structure

```
gasFeesSimulatorTest/
├── main.py                    # Main orchestrator
├── src/
│   ├── main.py               # Test harness
│   ├── runner.py             # Scenario execution
│   ├── status_watcher.py     # Transaction monitoring
│   ├── report_writer.py      # Report generation
│   ├── adapters/             # Backend adapters
│   └── models.py             # Data models
├── scenarios/                # Test scenarios (YAML)
├── contracts/                # Smart contracts
├── backends/                 # Node.js backend
├── scripts/                  # Helper scripts
├── config/                   # Configuration files
├── tests/                    # Unit tests
└── artifacts/                # Test results (generated)
```

## 📈 Results and Reporting

After running tests, results are saved in `artifacts/`:

```
artifacts/
└── 2026-04-18_21-00-00/
    ├── runs.csv              # Detailed metrics
    ├── summary.json          # Summary statistics
    ├── summary.md            # Readable summary
    ├── full_report.md        # Complete report
    └── logs/
        └── live.log          # Execution log
```

## ⚙️ Configuration

Edit `config/defaults.yaml` to customize:

```yaml
timeout_seconds: 300          # Transaction timeout
poll_interval_seconds: 1.0    # Status polling frequency
command_retries: 3            # Retry attempts

gas_thresholds:
  fail_below: 40              # Very low gas
  borderline_below: 65        # Risky
  normal: 90                  # Safe
  high: 140                   # Excessive
```

## 🐛 Troubleshooting

### "Missing required environment variables"

Ensure `HARNESS_PRIVATE_KEY` is set in `.env`:

```bash
cat .env | grep HARNESS_PRIVATE_KEY
```

### "Transaction timed out"

This is normal for Bradbury Testnet (5-10 minutes confirmation time). Check status manually:

```bash
python scripts/get_status.py --rpc https://rpc-bradbury.genlayer.com --tx <TX_HASH>
```

### "npm install fails"

Ensure Node.js 18+ is installed:

```bash
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 8.0.0
```

### "ModuleNotFoundError"

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## ⏱️ Expected Execution Time

- **Contract deployment**: ~10 seconds
- **Transaction confirmation**: 5-10 minutes (network dependent)
- **Full test suite**: ~10-15 minutes per scenario

⚠️ **Note**: Bradbury Testnet can be slow. This is normal network behavior.

## 🌐 Network Configuration

### Bradbury Testnet (Default)
```
RPC URL: https://rpc-bradbury.genlayer.com
Network: bradbury
Chain ID: (automatic)
```

### Custom Network

To use a different network, update `.env`:

```env
HARNESS_DEFAULT_NETWORK=your_network_name
HARNESS_RPC_URL=https://your-rpc-url.com
```

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Contributing](CONTRIBUTING.md)** - Development guidelines
- **[Test Report](TEST_REPORT.md)** - Detailed testing results
- **[Changelog](CHANGELOG.md)** - Version history

## 🔐 Security

- ✅ Never commit `.env` files
- ✅ Use only testnet private keys
- ✅ Don't store real funds on test accounts
- ✅ Review code before running with real keys

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GenLayer Documentation**: https://docs.genlayer.com
- **Bradbury Testnet**: https://rpc-bradbury.genlayer.com
- **genlayer-js SDK**: https://github.com/yeagerai/genlayer-js

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## ✅ System Requirements

### Minimum
- Python 3.10+
- Node.js 18+
- npm 8+
- 2GB RAM
- 500MB disk space

### Recommended
- Python 3.11+
- Node.js 20+
- npm 10+
- 4GB RAM
- 1GB disk space

## 🎉 Getting Started Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt` and `npm install`)
- [ ] `.env` file created with `HARNESS_PRIVATE_KEY`
- [ ] Private key is valid (starts with `0x`)
- [ ] Internet connection available
- [ ] Ready to wait 5-10 minutes for transaction confirmation

---

**Version**: 1.0  
**Status**: ✅ Production Ready  
**Last Updated**: April 18, 2026