import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
import math

# FIX: Import the main functions to be tested
from src.analysis.stream_analyzer import calculate_entropy, process_message, connect_with_retry

# FIX: A mock class to simulate the Kafka message object structure
class MockKafkaMessage:
    def __init__(self, value):
        self.value = value

@pytest.fixture
def sample_kafka_message():
    """Sample Kafka message for testing, now returns a mock object."""
    message_value = {
        "payload": {
            "op": "c",
            "after": {
                "position_id": 1001,
                "trader_id": 123,
                "symbol": "EURUSD",
                "type": "Buy",
                "volume": 0.1,
                "open_time": "2023-01-01T10:00:00Z",
                "open_price": 1.0700,
                "close_time": "2023-01-01T12:00:00Z",
                "close_price": 1.0750,
                "commission": -0.5,
                "swap": 0.0,
                "profit": 50.0
            }
        }
    }
    # Return an object with a .value attribute instead of a dict
    return MockKafkaMessage(message_value)

@pytest.fixture
def redis_mock():
    """Mock Redis client instance."""
    # This fixture correctly mocks the Redis instance
    with patch('src.analysis.stream_analyzer.redis.Redis') as mock_redis_class:
        mock_instance = mock_redis_class.return_value
        yield mock_instance

@pytest.fixture
def clickhouse_mock():
    """Mock ClickHouse client instance."""
    with patch("src.analysis.stream_analyzer.Client") as mock_client:
        yield mock_client.return_value

# Tests for calculate_entropy (No changes needed here)
def test_calculate_entropy_empty():
    assert calculate_entropy([]) == 0.0

def test_calculate_entropy_single():
    assert calculate_entropy(["EURUSD"]) == 0.0

def test_calculate_entropy_multiple():
    symbols = ["EURUSD", "GBPUSD"]
    expected_entropy = 1.0
    assert abs(calculate_entropy(symbols) - expected_entropy) < 1e-6

def test_calculate_entropy_repeated():
    symbols = ["EURUSD", "EURUSD", "GBPUSD"]
    expected_entropy = -((2/3 * math.log2(2/3)) + (1/3 * math.log2(1/3)))
    assert abs(calculate_entropy(symbols) - expected_entropy) < 1e-6

# Tests for process_message
def test_process_message_valid(sample_kafka_message, redis_mock, clickhouse_mock, monkeypatch):
    monkeypatch.setattr("src.analysis.stream_analyzer.clickhouse_client", clickhouse_mock)
    monkeypatch.setattr("src.analysis.stream_analyzer.redis_client", redis_mock)

    redis_mock.get.return_value = None
    
    process_message(sample_kafka_message)

    assert clickhouse_mock.execute.call_count == 2
    redis_mock.set.assert_called_once()
    state = json.loads(redis_mock.set.call_args[0][1])
    assert state["total_trades"] == 1
    assert state["wins"] == 1

def test_process_message_invalid_op(sample_kafka_message, redis_mock, clickhouse_mock, monkeypatch):
    monkeypatch.setattr("src.analysis.stream_analyzer.clickhouse_client", clickhouse_mock)
    monkeypatch.setattr("src.analysis.stream_analyzer.redis_client", redis_mock)
    
    sample_kafka_message.value["payload"]["op"] = "u"
    
    process_message(sample_kafka_message)
    
    redis_mock.get.assert_not_called()
    clickhouse_mock.execute.assert_not_called()

def test_process_message_missing_payload(sample_kafka_message, redis_mock, clickhouse_mock, monkeypatch):
    monkeypatch.setattr("src.analysis.stream_analyzer.clickhouse_client", clickhouse_mock)
    monkeypatch.setattr("src.analysis.stream_analyzer.redis_client", redis_mock)

    sample_kafka_message.value = {}
    
    process_message(sample_kafka_message)

    redis_mock.get.assert_not_called()
    clickhouse_mock.execute.assert_not_called()

# Tests for connect_with_retry (No changes needed here)
def test_connect_with_retry_success():
    mock_connect_func = MagicMock(return_value="connected")
    result = connect_with_retry(mock_connect_func, "TestService", max_retries=3, delay=0.1)
    assert result == "connected"
    mock_connect_func.assert_called_once()

def test_connect_with_retry_failure():
    mock_connect_func = MagicMock(side_effect=Exception("Connection failed"))
    with pytest.raises(SystemExit):
        connect_with_retry(mock_connect_func, "TestService", max_retries=2, delay=0.1)
    assert mock_connect_func.call_count == 2

# Test for state evolution
def test_process_message_state_evolution(redis_mock, clickhouse_mock, monkeypatch):
    monkeypatch.setattr("src.analysis.stream_analyzer.clickhouse_client", clickhouse_mock)
    monkeypatch.setattr("src.analysis.stream_analyzer.redis_client", redis_mock)

    def _create_trade_message(position_id, profit, symbol):
        message_value = { "payload": { "op": "c", "after": {
            "position_id": position_id, "trader_id": 123, "symbol": symbol,
            "type": "Buy", "volume": 0.1, "open_time": "2023-01-01T10:00:00Z",
            "open_price": 1.1, "close_time": "2023-01-01T11:00:00Z", "close_price": 1.2,
            "commission": 0, "swap": 0, "profit": profit
        }}}
        return MockKafkaMessage(message_value)

    # --- Trade 1: Initial Win (+50 profit) ---
    trade1_msg = _create_trade_message(1001, 50.0, "EURUSD")
    redis_mock.get.return_value = None
    process_message(trade1_msg)
    state_after_trade1_json = redis_mock.set.call_args[0][1]
    state_after_trade1 = json.loads(state_after_trade1_json)
    assert state_after_trade1['total_profit_usd'] == 50.0
    assert state_after_trade1['max_drawdown'] == 0.0

    # --- Trade 2: A Loss (-30 profit) ---
    trade2_msg = _create_trade_message(1002, -30.0, "GBPUSD")
    redis_mock.get.return_value = state_after_trade1_json
    process_message(trade2_msg)
    state_after_trade2_json = redis_mock.set.call_args[0][1]
    state_after_trade2 = json.loads(state_after_trade2_json)
    assert state_after_trade2['total_profit_usd'] == 20.0
    assert state_after_trade2['max_drawdown'] == 30.0

    # --- Trade 3: A bigger Win (+100 profit) ---
    trade3_msg = _create_trade_message(1003, 100.0, "EURUSD")
    redis_mock.get.return_value = state_after_trade2_json
    process_message(trade3_msg)
    state_after_trade3_json = redis_mock.set.call_args[0][1]
    state_after_trade3 = json.loads(state_after_trade3_json)
    assert state_after_trade3['total_profit_usd'] == 120.0
    assert state_after_trade3['peak_equity'] == 120.0
    assert state_after_trade3['max_drawdown'] == 30.0

    assert clickhouse_mock.execute.call_count == 6