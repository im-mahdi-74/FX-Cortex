import pytest
import polars as pl
from unittest.mock import patch, MagicMock
from src.analysis.etl_processor import (
    extract_metadata_from_filename,
    standardize_symbol,
    generate_position_id,
    process_single_file,
    get_existing_position_ids,
)

# Tests for extract_metadata_from_filename
def test_extract_metadata_from_filename_valid():
    """Test valid filename parsing."""
    # FIX: Used a filename that matches the required regex pattern (_algo)
    filename = "123_testserver_algo50.positions.csv"
    trader_id, server, algo_pct = extract_metadata_from_filename(filename)
    assert trader_id == 123
    assert server == "testserver"
    assert algo_pct == 50

def test_extract_metadata_from_filename_invalid():
    """Test invalid filename parsing."""
    # FIX: Used a filename that is genuinely invalid (missing '_algo')
    filename = "123_invalidformat_50.positions.csv"
    trader_id, server, algo_pct = extract_metadata_from_filename(filename)
    # FIX: When parsing fails, all returned values should be None
    assert trader_id is None
    assert server is None
    assert algo_pct is None

# Tests for standardize_symbol
def test_standardize_symbol():
    """Test symbol standardization."""
    assert standardize_symbol("EUR/USD") == "EURUSD"
    assert standardize_symbol("eurusd#") == "EURUSD"
    assert standardize_symbol("GBPUSD") == "GBPUSD"
    assert standardize_symbol("") == ""
    assert standardize_symbol(None) is None

# Tests for generate_position_id
def test_generate_position_id():
    """Test deterministic position ID generation."""
    pos_id1 = generate_position_id(123, "2023.01.01 10:00:00", "EURUSD", 1.0700)
    pos_id2 = generate_position_id(123, "2023.01.01 10:00:00", "EURUSD", 1.0700)
    pos_id_diff = generate_position_id(123, "2023.01.01 10:00:00", "GBPUSD", 1.0700)
    
    assert isinstance(pos_id1, int)
    assert pos_id1 == pos_id2
    assert pos_id1 != pos_id_diff

# Tests for process_single_file
def test_process_single_file_valid(tmp_path):
    """Test processing a valid CSV file."""
    # FIX: Create a predictable, self-contained CSV for this test
    valid_content = (
        "Time;Type;Volume;Symbol;Price;Time;Price;Commission;Swap;Profit\n"
        "2023.01.01 10:00:00;Buy;0.1;EURUSD;1.1;2023.01.01 11:00:00;1.2;-1;-0.1;100\n"
        "2023.01.02 10:00:00;Sell;0.2;GBPUSD;1.3;2023.01.02 11:00:00;1.4;-1;-0.1;200\n"
        "2023.01.03 10:00:00;Balance;0;...;0;...;0;0;0;5000\n"
    )
    valid_csv_path = tmp_path / "123_testserver_algo50.positions.csv"
    valid_csv_path.write_text(valid_content)

    df = process_single_file(str(valid_csv_path))
    
    assert df is not None
    assert df.height == 2, "Should filter out Balance rows, leaving 2 trades"
    assert "trader_id" in df.columns
    assert df["trader_id"][0] == 123
    assert df["server"][0] == "testserver"
    assert df["algo_trading_pct"][0] == 50

def test_process_single_file_empty(tmp_path):
    """Test processing a CSV file that is empty after filtering."""
    empty_csv_content = (
        "Time;Type;Volume;Symbol;Price;Time;Price;Commission;Swap;Profit\n"
        "2023.01.03 10:00:00;Balance;0;...;0;...;0;0;0;5000\n"
    )
    empty_csv = tmp_path / "456_server_algo20.positions.csv"
    empty_csv.write_text(empty_csv_content)
    df = process_single_file(str(empty_csv))
    assert df is None

def test_process_single_file_invalid_filename(tmp_path):
    """Test processing a file with an invalid filename."""
    # FIX: Renamed test for clarity
    invalid_csv = tmp_path / "invalid-filename.csv"
    invalid_csv.write_text("Time;Type\n2023.01.01 10:00:00;Buy")
    df = process_single_file(str(invalid_csv))
    # FIX: The function SHOULD return None for a file with an invalid name
    assert df is None

# Mock database connection for integration-like testing
@patch("src.analysis.etl_processor.engine")
def test_get_existing_position_ids(mock_engine):
    """Test fetching existing position IDs from database."""
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value = [(1001,), (1002,)]

    trader_ids = [123, 456]
    existing_ids = get_existing_position_ids(trader_ids)
    assert existing_ids == {1001, 1002}