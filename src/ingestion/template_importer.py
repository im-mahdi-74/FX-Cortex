import os
import sys
import logging
import pandas as pd
import numpy
import psycopg2
import psycopg2.extras
from psycopg2.extensions import AsIs
from dotenv import load_dotenv

# --- Path Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# --- Psycopg2 NumPy type adaptation ---
def adapt_numpy_types(numpy_type):
    return AsIs(numpy_type)

psycopg2.extensions.register_adapter(numpy.int64, adapt_numpy_types)
psycopg2.extensions.register_adapter(numpy.float64, adapt_numpy_types)

# --- Configuration ---
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "db"  # Always use the service name in Docker
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def import_my_data():
    """
    Sample function to fetch, transform, and load data.
    """
    logging.info("Starting custom data import...")

    # =================================================================
    # 1. Fetch and process your data here
    # Example: Generating dummy data
    # =================================================================
    trades_data = {
        'position_id': [999001, 999002],
        'trader_id': [12345, 12345],
        'symbol': ['BTCUSD', 'ETHUSD'],
        'type': ['buy', 'sell'],
        'volume': [0.1, 1.5],
        'open_time': [pd.Timestamp.now(tz='UTC'), pd.Timestamp.now(tz='UTC')],
        'open_price': [60000.0, 3000.0],
        'close_time': [pd.Timestamp.now(tz='UTC'), pd.Timestamp.now(tz='UTC')],
        'close_price': [61000.0, 2950.0],
        'commission': [-1.5, -2.0],
        'swap': [0.0, -0.5],
        'profit': [100.0, -75.0]
    }
    trades_df = pd.DataFrame(trades_data)

    # =================================================================
    # 2. Insert data into the database
    # =================================================================
    insert_query = """
        INSERT INTO raw_data.trades (position_id, trader_id, symbol, type, volume, open_time, open_price, close_time, close_price, commission, swap, profit)
        VALUES %s ON CONFLICT (position_id) DO NOTHING;
    """
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                data_tuples = [tuple(x) for x in trades_df.to_records(index=False)]
                psycopg2.extras.execute_values(cursor, insert_query, data_tuples)
                conn.commit()
                logging.info("Data successfully inserted into raw_data.trades.")
    except Exception as e:
        logging.error(f"Error inserting data: {e}")

if __name__ == "__main__":
    import_my_data()