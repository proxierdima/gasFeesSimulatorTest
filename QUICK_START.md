# Quick Start Guide - Gas Fees Simulator Tests

**Last Updated**: 2026-04-17  
**Version**: 1.0.0

---

## 🚀 5-Minute Setup

### 1. Prerequisites Check
```bash
python --version  # Need 3.10+
node --version    # Need 18+
npm --version     # Need 8+
```

### 2. Install Dependencies
```bash
# Python
pip install -r requirements.txt

# Node.js
npm install
```

### 3. Configure Environment
```bash
# Create .env file
cat > .env << EOF
HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HARNESS_DEFAULT_NETWORK=bradbury
GLH_TEST_CONTRACT_FILE=contracts/fixtures/sample_contract.py
EOF
```

⚠️ **Replace `0xYOUR_PRIVATE_KEY_HERE` with your actual testnet private key!**

### 4. Run Tests
```bash
# Quick run (all suites)
./run.sh .

# Or with Python
python main.py --project-root . --out artifacts
```

---

## 📋 Common Commands

### Run Specific Scenario
```bash
python -m src.main --scenario scenarios/low_gas.yaml --adapter command
```

### Mock Mode (No Blockchain)
```bash
python -m src.main --scenario scenarios/deterministic_baseline.yaml --adapter mock
```

### Run Tests
```bash
pytest                    # All tests
pytest -v                 # Verbose
pytest --cov=src          # With coverage
```

### Check Code Quality
```bash
black src/ scripts/       # Format code
flake8 src/ scripts/      # Lint
npm run check:node        # Check Node.js backends
```

---

## 📊 Understanding Results

After running tests, check `artifacts/<timestamp>/`:

```
artifacts/2026-04-17_20-30-45/
├── runs.csv              # Detailed metrics (gas_used, duration, etc.)
├── summary.json          # Pass/fail counts
├── report.md             # Human-readable analysis
├── live.log              # Real-time event log
└── <run_id>/             # Per-run data
    ├── receipt.json
    ├── trace.json        # (if debug enabled)
    └── state.json
```

### Quick Analysis
```bash
# View summary
cat artifacts/*/summary.json | jq

# Check failures
grep "actual_pass.*false" artifacts/*/runs.csv

# Gas usage stats
awk -F',' '{sum+=$13; count++} END {print "Avg gas:", sum/count}' artifacts/*/runs.csv
```

---

## 🎯 Test Scenarios Overview

| Scenario | Gas Limit | Expected Result |
|----------|-----------|-----------------|
| `deterministic_baseline.yaml` | 90 (normal) | ✅ FINALIZED |
| `low_gas.yaml` | 35 (low) | ⚠️ OUT_OF_FEE |
| `borderline_gas.yaml` | 65 (risky) | ⚠️ May fail |
| `high_gas.yaml` | 140 (high) | ✅ FINALIZED |
| `concurrent_same_sender.yaml` | 90 (normal) | ✅ FINALIZED |

---

## 🔧 Troubleshooting

### Error: "Missing required environment variables"
**Solution**: Set `HARNESS_PRIVATE_KEY` in `.env` file

### Error: "npm install failed"
**Solution**: 
```bash
# Check Node.js version
node --version  # Must be 18+

# Manual install
npm install genlayer-js viem
```

### Error: "Transaction not visible"
**Solution**: Increase timeout in scenario YAML:
```yaml
run:
  timeout_seconds: 120  # Increase from 60
```

### Error: "OUT_OF_FEE"
**Solution**: This is expected for `low_gas.yaml`. For other scenarios, increase gas:
```yaml
gas_profile:
  mode: preset
  preset: high  # or normal
```

### Tests Fail with State Mismatch
**Solution**: Check if contract behavior is deterministic:
```yaml
behavior:
  nondeterministic: true  # Set if contract uses randomness/AI
```

---

## 📚 Next Steps

1. **Read Architecture**: `ARCHITECTURE.md` - Understand system design
2. **Contribute**: `CONTRIBUTING.md` - Development guidelines
3. **Customize**: Create your own scenarios in `scenarios/`
4. **Extend**: Add new backends in `backends/`

---

## 🆘 Getting Help

- **Documentation**: Check `README.md`, `ARCHITECTURE.md`
- **Issues**: Search existing issues on GitHub
- **Logs**: Check `artifacts/*/live.log` for detailed execution logs
- **Discord**: Join GenLayer Discord for community support

---

## ✅ Verification Checklist

Before running production tests:

- [ ] `.env` file configured with valid private key
- [ ] Python dependencies installed (`pip list | grep -E "pytest|requests|PyYAML"`)
- [ ] Node.js dependencies installed (`npm list genlayer-js viem`)
- [ ] Can run mock test: `python -m src.main --scenario scenarios/deterministic_baseline.yaml --adapter mock`
- [ ] Network accessible: `curl https://rpc-bradbury.genlayer.com`
- [ ] Have testnet tokens in account

---

## 🎓 Example Workflow

```bash
# 1. Setup (one-time)
pip install -r requirements.txt
npm install
cp .env.example .env
# Edit .env with your private key

# 2. Validate setup
python main.py --help

# 3. Run single scenario (test)
python -m src.main --scenario scenarios/deterministic_baseline.yaml --adapter command

# 4. Run full suite
python main.py --project-root . --out artifacts

# 5. Analyze results
cat artifacts/*/summary.json
```

---

## 📈 Performance Tips

- **Parallel Execution**: Increase `concurrency` in scenarios (careful with nonce conflicts)
- **Skip npm Install**: Use `--skip-npm-install` if dependencies already installed
- **Reduce Repeats**: Lower `repeat` count during development
- **Mock Mode**: Use `--adapter mock` for fast iteration

---

**Happy Testing! 🚀**

For detailed information, see [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md).