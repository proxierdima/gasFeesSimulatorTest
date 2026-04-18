from __future__ import annotations

from pathlib import Path

from src.adapters.factory import create_adapter
from src.config import load_settings
from src.report_writer import ReportWriter
from src.runner import ScenarioRunner
from src.scenario_loader import load_scenarios


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_mock_smoke(tmp_path: Path) -> None:
    settings = load_settings(PROJECT_ROOT)
    settings.adapter_mode = "mock"
    adapter = create_adapter("mock", settings)
    scenarios = load_scenarios(str(PROJECT_ROOT / "scenarios" / "deterministic_baseline.yaml"))
    writer = ReportWriter(tmp_path / "artifacts")
    writer.write_manifest(settings, scenarios, {"scenario": "deterministic_baseline.yaml"})
    runner = ScenarioRunner(settings, adapter, writer)
    results = runner.run_scenarios(scenarios)

    assert results
    assert writer.csv_path.exists()
    assert writer.summary_path.exists()
    assert writer.manifest_path.exists()
