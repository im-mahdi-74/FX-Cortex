import os
import json
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer
import redis
from clickhouse_driver import Client
from dotenv import load_dotenv
import numpy
from collections import Counter
import math

# --- Configuration ---
load_dotenv()
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TRADES_TOPIC = os.getenv("TRADES_TOPIC", "fx-cortex.raw_data.trades")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")

# --- Logger Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Database Connections ---
def connect_with_retry(connect_func, service_name, max_retries=5, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = connect_func()
            logger.info(f"Successfully connected to {service_name}.")
            return conn
        except Exception as e:
            retries += 1
            logger.warning(f"Could not connect to {service_name}. Retrying in {delay}s... ({retries}/{max_retries})")
            time.sleep(delay)
    logger.critical(f"Failed to connect to {service_name} after {max_retries} retries. Exiting.")
    exit(1)

def connect_to_clickhouse():
    client = Client(host=CLICKHOUSE_HOST)
    client.execute('SELECT 1')
    return client


redis_client = None
clickhouse_client = None

def setup_clickhouse_schema():
    """Creates all necessary tables in ClickHouse."""
    try:
        logger.info("Setting up ClickHouse schema...")
        clickhouse_client.execute("CREATE DATABASE IF NOT EXISTS analysis_results")
        
        # Table for raw trade data mirror
        clickhouse_client.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results.trades_mirror (
                position_id Int64,
                trader_id Int32,
                symbol String,
                type String,
                volume Float64,
                open_time DateTime,
                open_price Float64,
                close_time DateTime,
                close_price Float64,
                commission Float64,
                swap Float64,
                profit Float64
            ) ENGINE = MergeTree()
            ORDER BY (trader_id, close_time)
        """)

        # Table for calculated analytics per trade
        clickhouse_client.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results.trade_analytics (
                trade_id Int64,
                trader_id Int32,
                close_time DateTime,
                total_trades Int32,
                win_rate Float32,
                profit_factor Float32,
                total_profit_usd Float64,
                avg_profit_per_trade Float64,
                avg_holding_time_hours Float64,
                symbol_entropy Float32,
                avg_volume Float64,
                std_dev_volume Float64,
                max_drawdown_usd Float64
            ) ENGINE = MergeTree()
            ORDER BY (trader_id, close_time)
        """)
        logger.info("ClickHouse schema is ready.")
    except Exception as e:
        logger.critical(f"Failed to create ClickHouse tables: {e}", exc_info=True)
        exit(1)

def calculate_entropy(symbols_list):
    if not symbols_list: return 0.0
    counts = Counter(symbols_list)
    total = len(symbols_list)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())

def process_message(msg):
    """Processes a single trade event from Kafka."""
    try:
        payload = msg.value.get('payload', {})
        if not payload or payload.get('op') != 'c': return

        trade = payload.get('after')
        if not trade: return

        trader_id = trade['trader_id']
        redis_key = f"trader_state:{trader_id}"

        open_time = datetime.fromisoformat(trade['open_time'].replace('Z', '+00:00'))
        close_time = datetime.fromisoformat(trade['close_time'].replace('Z', '+00:00'))

        # 1. Insert raw trade data into ClickHouse mirror table
        raw_trade_data = {
            'position_id': trade['position_id'], 'trader_id': trader_id,
            'symbol': trade['symbol'], 'type': trade['type'],
            'volume': trade['volume'], 'open_time': open_time,
            'open_price': trade['open_price'], 'close_time': close_time,
            'close_price': trade['close_price'], 'commission': trade['commission'],
            'swap': trade['swap'], 'profit': trade['profit']
        }
        clickhouse_client.execute(
            'INSERT INTO analysis_results.trades_mirror (*) VALUES', [raw_trade_data]
        )

        # 2. Fetch and update state from Redis
        state_json = redis_client.get(redis_key)
        state = json.loads(state_json) if state_json else {
            'total_trades': 0, 'wins': 0, 'total_profit_usd': 0.0,
            'total_profit_positive': 0.0, 'total_loss_negative': 0.0,
            'total_holding_time_seconds': 0.0, 'volumes': [], 'symbols': [],
            'peak_equity': 0.0, 'max_drawdown': 0.0
        }

        profit = float(trade.get('profit', 0.0))
        state['total_trades'] += 1
        state['total_profit_usd'] += profit
        current_equity = state['total_profit_usd']
        state['peak_equity'] = max(state['peak_equity'], current_equity)
        drawdown = state['peak_equity'] - current_equity
        state['max_drawdown'] = max(state['max_drawdown'], drawdown)
        if profit > 0:
            state['wins'] += 1
            state['total_profit_positive'] += profit
        elif profit < 0:
            state['total_loss_negative'] += abs(profit)
        
        state['total_holding_time_seconds'] += (close_time - open_time).total_seconds()
        state['volumes'].append(float(trade.get('volume', 0.0)))
        state['symbols'].append(trade.get('symbol'))
        if len(state['volumes']) > 100: state['volumes'].pop(0)
        if len(state['symbols']) > 100: state['symbols'].pop(0)

        # 3. Recalculate analytical features
        analytics_data = {
            'trade_id': trade['position_id'], 'trader_id': trader_id, 'close_time': close_time,
            'total_trades': state['total_trades'],
            'win_rate': (state['wins'] / state['total_trades']) if state['total_trades'] > 0 else 0.0,
            'profit_factor': (state['total_profit_positive'] / state['total_loss_negative']) if state['total_loss_negative'] > 0 else 999.0,
            'total_profit_usd': state['total_profit_usd'],
            'avg_profit_per_trade': (state['total_profit_usd'] / state['total_trades']) if state['total_trades'] > 0 else 0.0,
            'avg_holding_time_hours': (state['total_holding_time_seconds'] / state['total_trades'] / 3600) if state['total_trades'] > 0 else 0.0,
            'symbol_entropy': calculate_entropy(state['symbols']),
            'avg_volume': numpy.mean(state['volumes']) if state['volumes'] else 0.0,
            'std_dev_volume': numpy.std(state['volumes']) if len(state['volumes']) > 1 else 0.0,
            'max_drawdown_usd': state['max_drawdown']
        }

        # 4. Save updated state back to Redis
        redis_client.set(redis_key, json.dumps(state))

        # 5. Insert final analytics into ClickHouse analytics table
        clickhouse_client.execute(
            'INSERT INTO analysis_results.trade_analytics (*) VALUES', [analytics_data]
        )
        
        logger.info(f"Processed and stored trade {analytics_data['trade_id']} for trader {trader_id}.")

    except Exception as e:
        logger.error(f"Error processing message: {msg.value}", exc_info=True)

def main():
    global redis_client, clickhouse_client
    redis_client = connect_with_retry(lambda: redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True), "Redis")
    clickhouse_client = connect_with_retry(connect_to_clickhouse, "ClickHouse")


    setup_clickhouse_schema()
    consumer = connect_with_retry(
        lambda: KafkaConsumer(
            TRADES_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            group_id='full-data-processor-group-v1', # Use a new group_id
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        ),
        "Kafka"
    )

    logger.info("Analyzer is running and waiting for new trade events...")
    for message in consumer:
        process_message(message)

if __name__ == "__main__":
    main()
