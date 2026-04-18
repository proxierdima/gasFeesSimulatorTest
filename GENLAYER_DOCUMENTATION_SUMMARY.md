# GenLayer Documentation Summary
# Based on Official Documentation Study

**Date**: April 19, 2026  
**Source**: https://docs.genlayer.com/  
**Purpose**: Understanding transaction statuses and execution results

---

## 🎯 KEY FINDINGS

### Transaction Status vs Execution Result

**CRITICAL DISTINCTION:**

GenLayer transactions have **TWO separate indicators**:

1. **Transaction Status** (`status`) - Blockchain processing state
2. **Execution Result** (`txExecutionResult`) - Contract code execution outcome

**These are INDEPENDENT!**

A transaction can be:
- ✅ **Status: Accepted** (blockchain accepted it)
- ❌ **Execution: FINISHED_WITH_ERROR** (contract code failed)

---

## 📊 TRANSACTION STATUSES

### Status Flow

```
Pending → Proposing → Committing → Revealing → Accepted → Finalized
                                              ↓
                                         Undetermined
                                              ↓
                                          Canceled
```

### Status Definitions

| Status | Code | Description |
|--------|------|-------------|
| **Pending** | 0 | Transaction received, waiting in queue |
| **Proposing** | 1 | Leader selected, proposing receipt |
| **Committing** | 2 | Validators committing votes |
| **Revealing** | 3 | Validators revealing votes |
| **Accepted** | 5 | Majority consensus reached ✅ |
| **Finalized** | 6 | Appeal window passed, irreversible |
| **Undetermined** | 7 | No consensus after all rounds |
| **Canceled** | 8 | Transaction canceled |

### What "Accepted" Means

**Accepted (status=5)** means:
- ✅ Transaction validated by network
- ✅ Consensus reached among validators
- ✅ Transaction processed through all stages
- ✅ Waiting for appeal window to pass

**Accepted DOES NOT mean:**
- ❌ Contract code executed successfully
- ❌ No errors occurred
- ❌ Transaction achieved its goal

---

## 🔧 EXECUTION RESULTS

### Execution Result Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | NOT_EXECUTED | Transaction not executed yet |
| 1 | **FINISHED_WITH_RETURN** | ✅ **Success** - Code executed correctly |
| 2 | **FINISHED_WITH_ERROR** | ❌ **Error** - Code threw exception |
| 3 | OUT_OF_FEE | ❌ Insufficient gas |

### Our Transaction Analysis

**Transaction**: `0x2cec9c0c650f096108870e89095b009cb686a240fa925883c07b01dd2f7430f6`

```json
{
  "status": 5,              // Accepted ✅
  "txExecutionResult": 2    // FINISHED_WITH_ERROR ❌
}
```

**Interpretation:**
- Blockchain accepted the transaction
- Validators reached consensus
- **BUT** contract code execution failed

---

## 🎭 CONSENSUS MECHANISM

### Optimistic Democracy

GenLayer uses **Optimistic Democracy** consensus:

1. **Leader Selection**: Weighted random based on stake
2. **Proposal**: Leader proposes transaction receipt
3. **Commit**: Validators commit votes (hidden)
4. **Reveal**: Validators reveal votes
5. **Consensus**: Majority agreement required
6. **Appeal Window**: Time for appeals before finalization

### Validators

- Minimum 5 validators per transaction
- Weighted selection by stake
- AI models reach consensus on subjective decisions
- Equivalence Principle for non-deterministic operations

---

## 🧠 INTELLIGENT CONTRACTS

### Key Features

1. **Non-deterministic Operations**
   - LLM calls via `gl.nondet.exec_prompt()`
   - Web data access
   - Random operations

2. **Equivalence Principle**
   - `gl.eq_principle.prompt_comparative()`
   - Validators must agree on results
   - Consensus on AI outputs

3. **Python-based**
   - Written in Python
   - Extends `gl.Contract`
   - Type hints supported

### WizardOfCoin Contract

Our test contract uses:
- `gl.nondet.exec_prompt()` - Calls AI model
- `gl.eq_principle.prompt_comparative()` - Reaches consensus
- Constructor: `__init__(self, have_coin: bool)`

**Issue Found**: We deployed with empty constructor args `[]` instead of `[true]` or `[false]`

---

## 🔍 TRANSACTION RECEIPT FIELDS

### Key Fields

```json
{
  "id": "0x...",                    // Transaction hash
  "status": 5,                      // Transaction status
  "txExecutionResult": 2,           // Execution result ⚠️
  "result": 1,                      // Consensus result
  "txOrigin": "0x...",             // Sender address
  "recipient": "0x...",            // Contract address
  "timestamps": {
    "Created": 1776548596,
    "Pending": 1776548596,
    "Activated": 1776548597,
    "Proposed": 1776548598,
    "Committed": 1776548600,
    "LeaderRevealed": 1776548601,
    "LastVote": 1776548602
  },
  "roundData": [{
    "round": 0,
    "votesCommitted": 5,
    "votesRevealed": 5,
    "result": 1
  }]
}
```

### Important Fields for Debugging

1. **txExecutionResult** - Most important for success/failure
2. **status** - Transaction processing state
3. **result** - Consensus outcome
4. **timestamps** - Performance analysis
5. **roundData** - Validator voting details

---

## ✅ CORRECT INTERPRETATION

### How to Check Transaction Success

**WRONG** ❌:
```python
if status == "Accepted":
    print("Transaction successful!")  # WRONG!
```

**CORRECT** ✅:
```python
if status == "Accepted" and txExecutionResult == 1:
    print("Transaction successful!")  # CORRECT!
elif status == "Accepted" and txExecutionResult == 2:
    print("Transaction accepted but execution failed!")
elif status == "Accepted" and txExecutionResult == 3:
    print("Transaction accepted but out of gas!")
```

### Status Checking Best Practice

```python
def check_transaction_success(receipt):
    status = receipt.get("status")
    exec_result = receipt.get("txExecutionResult")
    
    # Check blockchain acceptance
    if status not in [5, 6]:  # Accepted or Finalized
        return False, "Transaction not accepted by blockchain"
    
    # Check execution result
    if exec_result == 1:
        return True, "Success"
    elif exec_result == 2:
        return False, "Execution error"
    elif exec_result == 3:
        return False, "Out of gas"
    else:
        return False, "Unknown execution result"
```

---

## 🔧 FIXING OUR TEST

### Problem Identified

**Current deployment**:
```bash
--constructor-args []  # Empty array ❌
```

**Contract constructor**:
```python
def __init__(self, have_coin: bool):
    self.have_coin = have_coin
```

**Error**: Missing required parameter `have_coin`

### Solution

**Correct deployment**:
```bash
--constructor-args [true]   # With coin ✅
# or
--constructor-args [false]  # Without coin ✅
```

---

## 📚 KEY TAKEAWAYS

### For Testing

1. ✅ Always check **both** `status` AND `txExecutionResult`
2. ✅ "Accepted" ≠ "Successful execution"
3. ✅ Read transaction receipt for full details
4. ✅ Verify constructor parameters match contract
5. ✅ Monitor execution time via timestamps

### For Gas Thresholds

1. ✅ Gas limit affects transaction processing
2. ✅ OUT_OF_FEE (txExecutionResult=3) means insufficient gas
3. ✅ FINISHED_WITH_ERROR (txExecutionResult=2) means code error
4. ✅ Our gas limit (90) was sufficient - error was in code

### For Monitoring

1. ✅ Use `gen_getTransactionReceipt` for full details
2. ✅ Use `gen_getTransactionStatus` for quick status
3. ✅ Check `txExecutionResult` field for success/failure
4. ✅ Parse timestamps for performance analysis

---

## 🎯 RECOMMENDATIONS

### Update Test Framework

1. **Add execution result checking**
   ```python
   if receipt["txExecutionResult"] != 1:
       print(f"⚠️ Execution failed: {receipt['txExecutionResult']}")
   ```

2. **Add constructor args parameter**
   ```python
   parser.add_argument("--constructor-args", default="[true]")
   ```

3. **Improve status reporting**
   ```python
   print(f"Status: {status_name}")
   print(f"Execution: {execution_result_name}")
   ```

### Update Documentation

1. Clarify difference between status and execution result
2. Add examples of failed executions
3. Document all execution result codes
4. Provide debugging guide

---

## 📖 REFERENCES

### Official Documentation

- **Main**: https://docs.genlayer.com/
- **Transaction Statuses**: https://docs.genlayer.com/core-concepts/transactions/transaction-statuses
- **Transaction Execution**: https://docs.genlayer.com/core-concepts/transactions/transaction-execution
- **API Reference**: https://docs.genlayer.com/api-references/genlayer-node-api

### RPC Methods

- `gen_getTransactionStatus` - Quick status check
- `gen_getTransactionReceipt` - Full transaction details
- `gen_getContractState` - Read contract state
- `gen_call` - Call contract methods (read-only)

---

## ✅ CONCLUSION

### What We Learned

1. **Transaction Status** and **Execution Result** are separate
2. "Accepted" means blockchain accepted, not code succeeded
3. Must check `txExecutionResult` for actual success
4. Our test had correct gas but wrong constructor args
5. GenLayer documentation is comprehensive and accurate

### Next Steps

1. ✅ Fix constructor args in deployment
2. ✅ Update test framework to check execution results
3. ✅ Re-run test with correct parameters
4. ✅ Verify `txExecutionResult == 1` (success)
5. ✅ Document findings for future reference

---

**Summary Prepared**: 2026-04-19 00:55:00 UTC  
**Version**: 1.0  
**Status**: ✅ COMPLETE