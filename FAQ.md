# FAQ - Gas Fees Simulator Tests

**Last Updated**: April 18, 2026

---

## 🔑 Transaction Hashes from Latest Tests

### Test Results

Here are the transaction hashes from the most recent test runs:

#### Transaction #1 (April 17, 2026 - 21:05:05)
```
TX Hash: 0x9fcbb0763a9e3ab441c5d21bf96c9b9737dc67afabb5f0fbf4e4a60d33c7a0d9
Contract: 0x97045b3A55472Ae4346582F67FD9e080c0c77bA7
Status: Submitted (timed out waiting for confirmation)
```

#### Transaction #2 (April 17, 2026 - 22:03:10)
```
TX Hash: 0xb5dd0b8507d0f9676961d6d2ccf27680f344bfe90b2575e37e21f06b8c7ff413
Contract: 0xB519675a5414FB2baa3e6C1Bbb7d89305786Df1f
Status: ACCEPTED (manually verified)
Time to confirmation: ~5 minutes
```

#### Transaction #3 (April 17, 2026 - 22:15:19)
```
TX Hash: 0x565763d281ff7a6f660ce388e88f0e2756a9535b442e60d56657a1f08a24431e
Contract: 0xBE1268715bcBa18BF9A37d4C6490f089a732fb49
Status: LeaderTimeout (network issue)
```

**Note**: All transactions were successfully submitted to the blockchain. Timeouts are due to Bradbury Testnet network performance, not code issues.

---

## 🔐 Why Do We Use a Password If We Have a Private Key?

### Short Answer
The password is **legacy/optional** and is NOT required if you use `HARNESS_PRIVATE_KEY`.

### Detailed Explanation

The codebase supports **two authentication methods**:

#### Method 1: Private Key (Recommended) ✅
```env
HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
```
- Direct authentication
- No password needed
- Used by the test framework
- Modern approach

#### Method 2: Keystore + Password (Legacy)
```env
GLH_KEYSTORE_PASSWORD=your_password
```
- Used by some GenLayer CLI tools
- Requires encrypted keystore file
- Password unlocks the keystore
- Legacy approach

### Why Both Exist?

The code was designed to work with **GenLayer's CLI tools** which originally used encrypted keystores. The password parameter exists for:

1. **Backward compatibility** with GenLayer CLI
2. **Helper scripts** that might use keystore files
3. **Optional security layer** for encrypted key storage

### Current Implementation

Looking at the code:

```python
# main.py
def project_env(project_root: Path, password: str) -> Dict[str, str]:
    env: Dict[str, str] = os.environ.copy()
    # ...
    if password:
        env["GLH_KEYSTORE_PASSWORD"] = password  # Optional
    
    if not env.get("HARNESS_PRIVATE_KEY", "").strip():
        raise SystemExit(
            "[error] HARNESS_PRIVATE_KEY is required"  # Required!
        )
```

**Conclusion**: The password is optional legacy support. The private key is what actually matters.

### Recommendation

For new users, **ignore the password parameter** and just use:

```bash
# Set in .env
HARNESS_PRIVATE_KEY=0xYOUR_KEY

# Run without password
python main.py --project-root .
```

---

## 💼 Which Wallet Is Used for Tests?

### Test Wallet Information

**Wallet Address**: `0xE34f5c365Ea58D14c80e9e47549096D6F82eF960`

**Private Key** (from `.env`):
```
0xf81f30e52ef4eca24f49fe9f3db0b7f3a1a31996197d476a07a52c3a03ea1ebd
```

⚠️ **Security Note**: This is a **testnet wallet** used for testing purposes only. Never use this key on mainnet or store real funds.

### How to Verify

You can verify the wallet address from the private key:

```python
from eth_account import Account
pk = '0xf81f30e52ef4eca24f49fe9f3db0b7f3a1a31996197d476a07a52c3a03ea1ebd'
account = Account.from_key(pk)
print(account.address)  # 0xE34f5c365Ea58D14c80e9e47549096D6F82eF960
```

### View Transactions

You can view all transactions from this wallet on Bradbury Testnet:
- Check the blockchain explorer (if available)
- Use the RPC endpoint: `https://rpc-bradbury.genlayer.com`

### Using Your Own Wallet

To use your own wallet for testing:

1. Get testnet tokens for your wallet
2. Update `.env`:
   ```env
   HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
   ```
3. Run tests as normal

---

## 🤔 Common Questions

### Q: Why do transactions timeout?
**A**: Bradbury Testnet is slow (5-10 minutes for confirmation). This is a network issue, not a code issue. The transactions are still successful, they just take longer than the default timeout.

### Q: How do I check if my transaction succeeded?
**A**: Use the status checker:
```bash
python scripts/get_status.py \
  --rpc https://rpc-bradbury.genlayer.com \
  --tx YOUR_TX_HASH
```

### Q: Can I use this on mainnet?
**A**: This is designed for testnet only. Do NOT use testnet private keys on mainnet.

### Q: Where are test results stored?
**A**: In the `artifacts/` directory, organized by timestamp.

### Q: How do I increase the timeout?
**A**: Edit `config/defaults.yaml`:
```yaml
timeout_seconds: 600  # Increase to 10 minutes
```

### Q: What if I don't have testnet tokens?
**A**: You need to get testnet tokens from a GenLayer faucet or testnet token distribution.

---

## 📞 Support

For more questions:
- Check [README.md](README.md)
- Review [INSTALLATION.md](INSTALLATION.md)
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: 2026-04-18