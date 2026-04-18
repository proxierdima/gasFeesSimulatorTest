# Changelog

All notable changes to the Gas Fees Simulator Tests project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-17

### Added
- **Environment Validation**: Added `validate_environment()` function to check required environment variables at startup
- **Comprehensive Documentation**:
  - `ARCHITECTURE.md`: Detailed system architecture with data flow diagrams
  - `CONTRIBUTING.md`: Development guidelines and contribution process
  - Updated `README.md` with quick start guide and troubleshooting
  - `CHANGELOG.md`: Version history tracking
- **Enhanced Docstrings**: Added comprehensive docstrings to all public functions in `runner.py`
- **Type Safety**: Added proper type hints throughout the codebase
  - Fixed `Dict[str, Any]` and `List[Dict[str, Any]]` annotations in `main.py`
  - Added `Optional` type hints in `_common.py`
  - Improved type annotations for better IDE support

### Changed
- **Code Quality Improvements**:
  - Fixed unused return value warnings by assigning to `_` variable
  - Improved error handling in `_resolve_backend_template_symbol()`
  - Added null check for `inspect.currentframe()` to prevent potential errors
  - Refactored long lines for better readability (PEP 8 compliance)

### Removed
- **Technical Debt Cleanup**:
  - Deleted obsolete patch files: `fix_submit_patch_v2.py` through `fix_submit_patch_v6.py`
  - Removed `patch_false_fail_submit.py`
  - Cleaned up backup files: `_common.py.bak.*`, `submit_*.py.bak.*`
  - Removed duplicate function definitions in `_common.py`

### Fixed
- **Type Annotations**: Corrected type hints in `main.py` to resolve Pylance/mypy errors
- **Import Organization**: Moved imports to top of file in `_common.py`
- **Frame Handling**: Added safety check for `inspect.currentframe()` returning `None`

### Security
- **Environment Variable Validation**: Ensures `HARNESS_PRIVATE_KEY` is set before execution
- **Documentation**: Added security warnings about private key management in README

## [0.9.0] - 2026-04-11 (Pre-audit)

### Added
- Initial project structure with Python harness and Node.js backends
- YAML-based scenario configuration system
- Mock and Command adapters for flexible execution
- Comprehensive reporting (CSV, JSON, Markdown)
- Gas profile system (low, borderline, normal, high)
- State verification after transaction execution
- Trace collection on failures
- Concurrent scenario execution with ThreadPoolExecutor

### Features
- **Test Suites**:
  - Group A: Gas limit tests (low, borderline, high, concurrent)
  - Group B: Edge case validation
  - Bootstrap: Automated contract deployment
- **Backends**:
  - `onchain_submit_deploy.mjs`: Contract deployment
  - `onchain_submit_write.mjs`: Write operations
  - `onchain_common.mjs`: Shared utilities
- **Scripts**:
  - Transaction submission wrappers
  - Status/receipt/trace retrieval
  - State reading utilities

## [Unreleased]

### Planned
- [ ] Parallel test suite execution (Group A + B concurrently)
- [ ] PostgreSQL integration for historical analysis
- [ ] Grafana dashboard for real-time metrics
- [ ] CI/CD integration with GitHub Actions
- [ ] Pre-flight gas estimation
- [ ] Multi-network support (simultaneous testnet testing)
- [ ] Contract fuzzing with randomized inputs
- [ ] Performance benchmarking over time

### Under Consideration
- [ ] Web UI for test execution and reporting
- [ ] Slack/Discord notifications for test results
- [ ] Automated regression detection
- [ ] Gas optimization recommendations
- [ ] Smart contract mutation testing

---

## Version History Summary

| Version | Date       | Key Changes                                      |
|---------|------------|--------------------------------------------------|
| 1.0.0   | 2026-04-17 | Documentation, type safety, technical debt cleanup |
| 0.9.0   | 2026-04-11 | Initial release with core functionality          |

---

## Migration Guide

### Upgrading from 0.9.0 to 1.0.0

**Breaking Changes**: None

**New Requirements**:
- `HARNESS_PRIVATE_KEY` environment variable is now validated at startup
- Ensure `.env` file is properly configured before running tests

**Deprecated**:
- Legacy patch files have been removed (no longer needed)

**Recommended Actions**:
1. Review new documentation in `ARCHITECTURE.md` and `CONTRIBUTING.md`
2. Update any custom scripts to use improved type hints
3. Run `pytest` to ensure all tests pass with new changes

---

## Contributors

- GenLayer QA Team - Initial development and maintenance
- Community contributors - Bug reports and feature suggestions

---

**Note**: For detailed commit history, see the Git log or GitHub repository.