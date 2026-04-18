# Contributing to Gas Fees Simulator Tests

Thank you for your interest in contributing to the Gas Fees Simulator Tests project! This document provides guidelines and best practices for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Adding New Scenarios](#adding-new-scenarios)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm 8 or higher
- Git
- A GenLayer Bradbury testnet account with test tokens

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/glh_v4.git
   cd glh_v4
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/glh_v4.git
   ```

## Development Setup

### 1. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set required variables:

```env
HARNESS_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HARNESS_DEFAULT_NETWORK=bradbury
GLH_TEST_CONTRACT_FILE=contracts/fixtures/sample_contract.py
```

**⚠️ Security Warning**: Never commit your `.env` file or expose your private key!

### 4. Verify Setup

Run a simple test to verify everything works:

```bash
python -m src.main --scenario scenarios/deterministic_baseline.yaml --adapter mock
```

## Code Style

### Python

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Imports**: Organized with `isort`
- **Formatting**: Use `black` for automatic formatting
- **Type hints**: Required for all public functions

#### Example

```python
from __future__ import annotations

from typing import Any, Dict, List

def process_transaction(
    tx_hash: str,
    network: str,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Process a transaction and return its receipt.
    
    Args:
        tx_hash: Transaction hash (0x-prefixed hex string)
        network: Network name (e.g., 'bradbury')
        timeout: Maximum wait time in seconds
        
    Returns:
        Dictionary containing transaction receipt
        
    Raises:
        TimeoutError: If transaction not finalized within timeout
        ValueError: If tx_hash is invalid
    """
    # Implementation here
    pass
```

#### Pre-commit Hooks

Install pre-commit hooks to automatically format code:

```bash
pip install pre-commit
pre-commit install
```

This will run `black`, `isort`, and `flake8` before each commit.

### JavaScript/Node.js

- **Style**: Follow Airbnb JavaScript Style Guide
- **Formatting**: Use Prettier
- **Linting**: ESLint with recommended rules

#### Example

```javascript
export async function submitTransaction(client, params) {
  const { contractAddress, functionName, args, gasLimit } = params;
  
  const txHash = await client.writeContract({
    address: contractAddress,
    functionName,
    args,
    gas: BigInt(gasLimit),
  });
  
  return txHash;
}
```

### YAML Scenarios

- **Indentation**: 2 spaces
- **Naming**: Use snake_case for keys
- **Comments**: Explain non-obvious configurations

#### Example

```yaml
name: example_scenario
kind: write
network: bradbury

contract:
  address: "${GLH_TEST_CONTRACT_ADDRESS}"
  function_name: "update_value"
  args: ["test_value"]

run:
  repeat: 3
  concurrency: 1
  wait_status: finalized  # Wait for full finalization
  debug: on-fail          # Collect traces only on failure
  timeout_seconds: 60
  tags: [example, baseline]

gas_profile:
  mode: preset
  preset: normal  # 90 gas units

expect:
  allowed_final_statuses: [FINALIZED]
  allowed_execution_results: [FINISHED_WITH_RETURN]
  state_check:
    enabled: true
    function_name: "get_value"
    expected: "test_value"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_runner.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Writing Tests

#### Unit Tests

Place unit tests in `tests/` directory:

```python
# tests/test_gas_profiles.py
import pytest
from src.gas_profiles import resolve_gaslimit
from src.models import AppSettings, GasProfile, GasThresholds

def test_resolve_gaslimit_preset_low():
    settings = AppSettings(gas_thresholds=GasThresholds(fail_below=40))
    profile = GasProfile(mode="preset", preset="low")
    
    gaslimit, name = resolve_gaslimit(profile, settings)
    
    assert gaslimit == 35
    assert name == "preset:low"

def test_resolve_gaslimit_custom():
    settings = AppSettings()
    profile = GasProfile(mode="custom", gaslimit=123)
    
    gaslimit, name = resolve_gaslimit(profile, settings)
    
    assert gaslimit == 123
    assert name == "custom:123"
```

#### Integration Tests

Test end-to-end flows with mock adapter:

```python
# tests/test_integration.py
from pathlib import Path
from src.adapters.factory import create_adapter
from src.config import load_settings
from src.runner import ScenarioRunner
from src.scenario_loader import load_scenarios

def test_scenario_execution_mock():
    settings = load_settings(Path(__file__).parent.parent)
    settings.adapter_mode = "mock"
    
    adapter = create_adapter("mock", settings)
    scenarios = load_scenarios("scenarios/deterministic_baseline.yaml")
    
    runner = ScenarioRunner(settings, adapter, None)
    results = runner.run_scenarios(scenarios)
    
    assert len(results) > 0
    assert all(r.actual_pass for r in results)
```

### Test Coverage Requirements

- **Minimum coverage**: 80% for new code
- **Critical paths**: 100% coverage for adapters, runners
- **Edge cases**: Test error conditions, timeouts, retries

## Submitting Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-gas-estimation`
- `fix/timeout-handling`
- `docs/update-readme`
- `refactor/cleanup-common-py`

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(scenarios): add multi-sender concurrent test

Add scenario to test concurrent transactions from different senders
to validate nonce handling and gas limit application.

Closes #123
```

```
fix(adapter): handle non-zero exit with tx_hash salvage

Backend may exit non-zero even when transaction was submitted
successfully. Extract tx_hash from stdout to continue execution.

Fixes #456
```

### Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   pytest
   npm run check:node
   ```

3. **Update documentation** if needed

4. **Create pull request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots/logs if applicable
   - Checklist of changes

5. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No new warnings
   
   ## Related Issues
   Closes #123
   ```

6. **Address review feedback** promptly

7. **Squash commits** if requested before merge

## Reporting Issues

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. With scenario '...'
3. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Node.js version: [e.g., 18.16.0]
- Network: [e.g., Bradbury]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other relevant information
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about

**Additional Context**
Mockups, examples, references
```

## Adding New Scenarios

### 1. Create YAML File

Create a new file in `scenarios/`:

```yaml
name: my_new_scenario
kind: write
network: bradbury

contract:
  address: "${GLH_TEST_CONTRACT_ADDRESS}"
  function_name: "my_function"
  args: ["arg1", "arg2"]

run:
  repeat: 5
  concurrency: 1
  wait_status: finalized
  debug: on-fail
  timeout_seconds: 60
  tags: [custom, experimental]

gas_profile:
  mode: preset
  preset: normal

expect:
  allowed_final_statuses: [FINALIZED]
  allowed_execution_results: [FINISHED_WITH_RETURN]
  state_check:
    enabled: true
    function_name: "get_result"
    expected: "expected_value"

behavior:
  base_required_gas: 60
  nondeterministic: false
```

### 2. Test Locally

```bash
python -m src.main --scenario scenarios/my_new_scenario.yaml --adapter mock
```

### 3. Add to Test Suite

If part of a suite, add to appropriate group:

```bash
cp scenarios/my_new_scenario.yaml scenarios/report_suite_group_a/
```

### 4. Document

Add description to scenario file:

```yaml
# Description: Tests edge case where contract state is modified
# by concurrent transactions with different gas limits.
#
# Expected behavior: All transactions should succeed with proper
# gas limit application and state consistency.
name: my_new_scenario
# ... rest of config
```

### 5. Update Test Suite

If adding to orchestrator, update `main.py`:

```python
SUITE_GROUPS = [
    ("Group A", "scenarios/report_suite_group_a"),
    ("Group B", "scenarios/report_suite_group_b"),
    ("Group C", "scenarios/report_suite_group_c"),  # New group
]
```

## Code Review Guidelines

### For Authors

- Keep PRs focused and small (< 400 lines if possible)
- Write clear commit messages
- Add tests for new functionality
- Update documentation
- Respond to feedback constructively

### For Reviewers

- Be respectful and constructive
- Focus on code quality, not personal preferences
- Suggest improvements, don't demand
- Approve when ready, request changes when needed
- Test locally if possible

## Development Workflow

### Typical Development Cycle

1. **Pick an issue** or create one
2. **Create branch** from `main`
3. **Implement changes** with tests
4. **Run tests locally**
5. **Commit with conventional format**
6. **Push and create PR**
7. **Address review feedback**
8. **Merge when approved**

### Release Process

1. Update version in `pyproject.toml` (if exists)
2. Update `CHANGELOG.md`
3. Create release tag: `git tag -a v1.2.0 -m "Release v1.2.0"`
4. Push tag: `git push origin v1.2.0`
5. Create GitHub release with notes

## Getting Help

- **Documentation**: Check `ARCHITECTURE.md` and `README.md`
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join GenLayer Discord for real-time help

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project documentation

Thank you for contributing! 🎉