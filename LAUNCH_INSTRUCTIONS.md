# LAUNCH INSTRUCTIONS
# Gas Fees Simulator Tests

**Date**: April 17, 2026  
**Version**: 1.0  
**Status**: ✅ Ready to use

---

## 🎯 QUICK START (5 MINUTES)

### Step 1: Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### Step 2: Configure Environment

Create or edit the `.env` file in the project root:

```env
# Required parameters
HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HARNESS_DEFAULT_NETWORK=bradbury

# Optional parameters
GLH_TEST_CONTRACT_FILE=contracts/fixtures/sample_contract.py
HARNESS_ADAPTER_MODE=command
HARNESS_OUTPUT_DIR=artifacts
```

⚠️ **IMPORTANT**: Replace `0xYOUR_PRIVATE_KEY_HERE` with your actual private key!

### Step 3: Run Tests

```bash
# Windows
python main.py --project-root "G:\glh_v4" --password 12345678

# Linux/Mac
python main.py --project-root ~/glh_v4 --password 12345678
```

---

## ⏱️ EXPECTED EXECUTION TIME

- **Contract deployment**: ~10 seconds
- **Transaction confirmation**: ~5-10 minutes (depends on network)
- **Full test**: ~10-15 minutes

⚠️ **NOTE**: Bradbury Testnet confirms transactions slowly. This is normal!

---

## 📊 WHAT HAPPENS DURING EXECUTION

1. ✅ Environment check (variables, dependencies)
2. ✅ Test contract deployment
3. ✅ Waiting for transaction confirmation (may take 5-10 minutes)
4. ✅ Executing test scenarios
5. ✅ Generating reports

---

## 📁 WHERE TO FIND RESULTS

After test execution, results will be in the `artifacts/` directory:

```
artifacts/
└── 2026-04-17_22-15-19/          # Results folder
    ├── runs.csv                   # Detailed metrics
    ├── summary.json               # Summary statistics
    ├── summary.md                 # Readable summary
    ├── full_report.md             # Full report
    └── logs/
        └── live.log               # Execution log
```

---

## 🔧 ADDITIONAL COMMANDS

### Run Single Scenario

```bash
python -m src.main \
  --scenario scenarios/deterministic_baseline.yaml \
  --adapter command
```

### Run in Mock Mode (Without Blockchain)

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

---

## ⚙️ CONFIGURING TIMEOUTS

If transactions don't confirm in time, increase the timeout in `config/defaults.yaml`:

```yaml
timeout_seconds: 600  # Increase to 10 minutes
poll_interval_seconds: 1.0
```

Or in a specific scenario (`scenarios/*/your_scenario.yaml`):

```yaml
run:
  timeout_seconds: 600
  wait_status: accepted  # Faster than finalized
```

---

## 🐛 TROUBLESHOOTING

### Problem: "Missing required environment variables"

**Solution**: Make sure `HARNESS_PRIVATE_KEY` is set in the `.env` file

```bash
# Check .env contents
cat .env | grep HARNESS_PRIVATE_KEY
```

### Problem: "Transaction timed out"

**Solution**: This is normal for Bradbury Testnet. Check status manually:

```bash
python scripts/get_status.py --rpc https://rpc-bradbury.genlayer.com --tx <TX_HASH>
```

If status is "Accepted" or "Finalized" - transaction succeeded!

### Problem: "npm install fails"

**Solution**: Make sure Node.js 18+ is installed

```bash
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 8.0.0
```

### Problem: "ModuleNotFoundError: No module named 'yaml'"

**Solution**: Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## 📋 SYSTEM REQUIREMENTS

### Minimum
- **Python**: 3.10+
- **Node.js**: 18+
- **npm**: 8+
- **RAM**: 2GB
- **Disk**: 500MB free space

### Recommended
- **Python**: 3.11+
- **Node.js**: 20+
- **npm**: 10+
- **RAM**: 4GB
- **Disk**: 1GB free space

---

## 🌐 NETWORK SETTINGS

### Bradbury Testnet (Default)
```
RPC URL: https://rpc-bradbury.genlayer.com
Network: bradbury
Chain ID: (automatic)
```

### Other Networks

To use a different network, change in `.env`:

```env
HARNESS_DEFAULT_NETWORK=your_network_name
HARNESS_RPC_URL=https://your-rpc-url.com
```

---

## 📊 MONITORING EXECUTION

### Real-time

Open a second terminal and watch the log:

```bash
tail -f artifacts/*/logs/live.log
```

### Transaction Progress

You will see messages like:

```
[2026-04-17T22:15:25] status run_id=... status=FOUND_PROPOSING
[2026-04-17T22:15:26] status run_id=... status=PROPOSING
[2026-04-17T22:15:56] status run_id=... status=PROPOSING_PROGRESS (Still processing after 30s)
```

This is normal! The transaction is being processed.

---

## 🎓 USAGE EXAMPLES

### Example 1: Basic Test

```bash
python main.py --project-root "G:\glh_v4" --password 12345678
```

### Example 2: Low Gas Test

```bash
python -m src.main \
  --scenario scenarios/low_gas.yaml \
  --adapter command \
  --repeat 3
```

### Example 3: Concurrent Transactions

```bash
python -m src.main \
  --scenario scenarios/concurrent_same_sender.yaml \
  --adapter command \
  --concurrency 3
```

### Example 4: Mock Mode (Fast)

```bash
python -m src.main \
  --scenario scenarios/deterministic_baseline.yaml \
  --adapter mock \
  --repeat 10
```

---

## 📈 INTERPRETING RESULTS

### Successful Test

```
[2026-04-17T22:20:30] result run_id=... final_status=ACCEPTED pass=True
```

✅ Transaction confirmed, test passed

### Timeout (But Transaction May Be Successful)

```
[2026-04-17T22:20:30] run-error ... Timed out waiting for tx ...
```

⚠️ Check status manually - transaction may be confirmed later

### Gas Error

```
[2026-04-17T22:20:30] result run_id=... final_status=OUT_OF_FEE
```

❌ Insufficient gas (this may be expected for some scenarios)

---

## 🔐 SECURITY

### Private Key

⚠️ **NEVER COMMIT THE `.env` FILE TO GIT!**

The `.env` file is already added to `.gitignore`, but be careful:

```bash
# Check that .env is not tracked
git status | grep .env  # Should have no output
```

### Test Network

✅ Use only test private keys  
✅ Don't use mainnet keys  
✅ Don't store real funds on test keys

---

## 📞 SUPPORT

### Documentation
- `README.md` - Complete guide
- `ARCHITECTURE.md` - Architecture
- `QUICK_START.md` - Quick start
- `FINAL_REPORT.md` - Testing results
- `QUICK_SUMMARY.md` - Brief summary

### Useful Links
- GenLayer Docs: https://docs.genlayer.com
- Bradbury Testnet: https://rpc-bradbury.genlayer.com
- genlayer-js SDK: https://github.com/yeagerai/genlayer-js

---

## ✅ PRE-LAUNCH CHECKLIST

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] `pip install -r requirements.txt` executed
- [ ] `npm install` executed
- [ ] `.env` file created and contains `HARNESS_PRIVATE_KEY`
- [ ] Private key is valid (starts with `0x`)
- [ ] Free disk space available (500MB+)
- [ ] Internet access available
- [ ] Ready to wait 5-10 minutes for transaction confirmation

---

## 🎉 READY!

After completing all steps, run:

```bash
python main.py --project-root "G:\glh_v4" --password 12345678
```

And watch the tests execute!

---

**Version**: 1.0  
**Date**: 2026-04-17  
**Status**: ✅ Ready to use