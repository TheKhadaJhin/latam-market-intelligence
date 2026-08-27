from pathlib import Path

from typer.testing import CliRunner

from market_intel.cli import app

runner = CliRunner()


def test_catalog_command_lists_all_indicators() -> None:
    result = runner.invoke(app, ["catalog"])
    assert result.exit_code == 0
    assert result.stdout.count("\n") == 8
    assert "GDP growth" in result.stdout


def test_init_db_creates_local_database(tmp_path: Path) -> None:
    database_path = tmp_path / "cli.db"
    result = runner.invoke(
        app,
        ["init-db"],
        env={"MARKET_INTEL_DATABASE_URL": f"sqlite:///{database_path}"},
    )
    assert result.exit_code == 0
    assert database_path.exists()
    assert "initialized" in result.stdout.lower()


def test_pipeline_command_rejects_reversed_dates() -> None:
    result = runner.invoke(app, ["pipeline", "--start-year", "2025", "--end-year", "2024"])
    assert result.exit_code != 0
    assert "start-year" in result.output
