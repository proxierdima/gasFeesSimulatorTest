# Gas Fees Simulator Tests v1.0.0

🎉 **First Production Release**

A comprehensive testing framework for validating GenLayer's gas fee behavior on Bradbury Testnet.

## 🚀 What's New

This is the first stable release of the Gas Fees Simulator Tests framework, providing:

- ✅ **18+ Test Scenarios** covering all gas configurations
- ✅ **Automated Testing** from deployment to reporting
- ✅ **Real Blockchain Integration** with GenLayer Bradbury Testnet
- ✅ **Comprehensive Reporting** in CSV, JSON, and Markdown
- ✅ **Cross-Platform Support** (Windows, Linux, macOS)
- ✅ **Transaction Monitoring** with real-time status tracking

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/proxierdima/gasFeesSimulatorTest.git
cd gasFeesSimulatorTest

# Install dependencies
pip install -r requirements.txt
npm install

# Configure environment
cp .env.example .env
# Edit .env and add your HARNESS_PRIVATE_KEY

# Run tests
python main.py --project-root . --password 12345678
```

## 📋 Requirements

- Python 3.10+
- Node.js 18+
- npm 8+
- GenLayer testnet account with private key

## 📚 Documentation

- [README.md](README.md) - Complete guide
- [INSTALLATION.md](INSTALLATION.md) - Installation instructions
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [RELEASE_NOTES.md](RELEASE_NOTES.md) - Detailed release notes

## ✨ Key Features

### Test Scenarios
- Gas limit tests (low, borderline, normal, high)
- Concurrent transaction testing
- Edge case detection
- Invalid function handling

### Reporting
- Detailed CSV metrics
- JSON summary statistics
- Markdown reports
- Real-time execution logs

### Adapters
- **Command Adapter**: Real blockchain interaction
- **Mock Adapter**: Offline testing

## ⚠️ Known Limitations

- Bradbury Testnet can take 5-10 minutes to confirm transactions (network issue, not code)
- Default timeout is 300 seconds; adjust if needed

## 🔐 Security

- Never commit `.env` files
- Use only testnet private keys
- Don't store real funds on test accounts

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

- **Issues**: https://github.com/proxierdima/gasFeesSimulatorTest/issues
- **GenLayer Docs**: https://docs.genlayer.com
- **Bradbury Testnet**: https://rpc-bradbury.genlayer.com

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Full Changelog**: https://github.com/proxierdima/gasFeesSimulatorTest/commits/v1.0.0