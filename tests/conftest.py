import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def sample_valid_csv_path(project_root: Path) -> Path:
    """Returns the path to the pre-made valid sample CSV file."""
    return project_root / "tests" / "fixtures" / "123_validtestserver_algo50.positions.csv"

@pytest.fixture(scope="session")
def sample_invalid_csv_path(project_root: Path) -> Path:
    """Returns the path to the pre-made invalid sample CSV file."""
    return project_root / "tests" / "fixtures" / "123_sampleinvalid_algo10.positions.csv"