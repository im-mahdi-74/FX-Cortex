import os
import sys
import logging
import polars as pl
import numpy as np
from sqlalchemy import create_engine, inspect, text, bindparam
from dotenv import load_dotenv
import glob
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
import psycopg2
import psycopg2.extras
from psycopg2.extensions import AsIs
from typing import List, Tuple, Optional
import hashlib
from datetime import datetime

# --- Path Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# --- Psycopg2 NumPy type adaptation ---
def adapt_numpy_types(numpy_type):
    return AsIs(numpy_type)

psycopg2.extensions.register_adapter(np.int64, adapt_numpy_types)
psycopg2.extensions.register_adapter(np.float64, adapt_numpy_types)
psycopg2.extensions.register_adapter(np.bool_, adapt_numpy_types)

# --- Configuration ---
load_dotenv()
RAW_FILES_PATH = os.path.join(PROJECT_ROOT, "data/raw_files/")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "logs/etl.log")

# Database connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Logger Setup ---
def setup_logger():
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s - %(levelname)s - %(message)s", 
        handlers=[
            logging.FileHandler(LOG_FILE_PATH, 'w'), 
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

# --- Database Engine ---
try:
    engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=30)
    logger.info("Successfully created SQLAlchemy engine with connection pooling.")
except Exception as e:
    logger.critical(f"Failed to create SQLAlchemy engine: {e}")
    sys.exit(1)

def create_tables_if_not_exist():
    """Creates schema and tables with explicit commits after each DDL operation."""
    logger.info("Checking for schema and tables...")
    try:
        with engine.connect() as connection:
            if not connection.dialect.has_schema(connection, 'raw_data'):
                logger.info("Schema 'raw_data' not found, creating it.")
                connection.execute(text("CREATE SCHEMA raw_data;"))
                connection.commit()
                logger.info("Schema 'raw_data' created and committed.")
            
            inspector = inspect(engine)
            if not inspector.has_table("traders", schema="raw_data"):
                logger.info("Table 'traders' not found, creating it...")
                connection.execute(text("""
                    CREATE TABLE raw_data.traders (
                        trader_id INTEGER PRIMARY KEY,
                        server VARCHAR(255),
                        algo_trading_pct INTEGER,
                        url VARCHAR(255),
                        last_updated TIMESTAMPTZ
                    );
                """))
                logger.info("Table 'traders' created.")

            if not inspector.has_table("trades", schema="raw_data"):
                logger.info("Table 'trades' not found, creating it...")
                connection.execute(text("""
                    CREATE TABLE raw_data.trades (
                        position_id BIGINT PRIMARY KEY,
                        trader_id INTEGER REFERENCES raw_data.traders(trader_id),
                        symbol VARCHAR(50),
                        type VARCHAR(10),
                        volume FLOAT,
                        open_time TIMESTAMPTZ,
                        open_price FLOAT,
                        close_time TIMESTAMPTZ,
                        close_price FLOAT,
                        commission FLOAT,
                        swap FLOAT,
                        profit FLOAT
                    );
                    
                    -- Create indexes for better performance
                    CREATE INDEX IF NOT EXISTS idx_trades_trader_id ON raw_data.trades(trader_id);
                    CREATE INDEX IF NOT EXISTS idx_trades_open_time ON raw_data.trades(open_time);
                    CREATE INDEX IF NOT EXISTS idx_trades_symbol ON raw_data.trades(symbol);
                """))
                logger.info("Table 'trades' and indexes created.")
            
            connection.commit()
            logger.info("Table creation process finished and committed. Schema and tables are ready.")

    except Exception as e:
        logger.error(f"An error occurred during schema/table setup: {e}", exc_info=True)
        raise

def extract_metadata_from_filename(filepath: str) -> Tuple[Optional[int], Optional[str], Optional[int]]:
    """Parses the filename to get trader_id, server, and algo_pct."""
    filename = os.path.basename(filepath)
    match = re.match(r'(\d+)_([^_]+)_algo(\d+)\.positions\.csv', filename)
    if match:
        trader_id, server, algo_pct = match.groups()
        return int(trader_id), server, int(algo_pct)
    logger.warning(f"Could not parse metadata from filename: {filename}")
    return None, None, None


def standardize_symbol(symbol: str) -> str:
    """Removes special characters and suffixes from a trading symbol."""
    if not isinstance(symbol, str):
        return symbol
    return re.sub(r'[^A-Z0-9]', '', symbol.upper())


def generate_position_id(trader_id: int, open_time: str, symbol: str, open_price: float) -> int:
    """Generate deterministic position ID using hash."""
    hash_input = f"{trader_id}_{open_time}_{symbol}_{open_price}"
    return int(hashlib.md5(hash_input.encode()).hexdigest()[:15], 16)


def process_single_file(filepath: str) -> Optional[pl.DataFrame]:
    """Process a single CSV file and return Polars DataFrame."""
    trader_id, server, algo_pct = extract_metadata_from_filename(filepath)
    if trader_id is None:
        return None
    
    try:
        # Read with Polars - much faster than pandas
        df = pl.read_csv(
            filepath, 
            separator=';',
            infer_schema_length=1000,
            try_parse_dates=True
        )
        
        # Filter out Balance rows immediately
        df = df.filter(pl.col("Type") != "Balance")
        
        if df.height == 0:  # No data after filtering
            return None
            
        # Add metadata columns
        df = df.with_columns([
            pl.lit(trader_id).alias("trader_id"),
            pl.lit(server).alias("server"),
            pl.lit(algo_pct).alias("algo_trading_pct")
        ])
        
        # Force cast numeric columns to Float64 to resolve schema mismatches across files
        numeric_cols = ['Volume', 'Price', 'Commission', 'Swap', 'Profit']
        if 'Volume_duplicated_0' in df.columns:
            numeric_cols.append('Volume_duplicated_0')
        if 'Price_duplicated_0' in df.columns:
            numeric_cols.append('Price_duplicated_0')
        
        df = df.with_columns([
            pl.col(col).cast(pl.Float64, strict=False) for col in numeric_cols if col in df.columns
        ])
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to process file {filepath}: {e}")
        return None


def get_existing_position_ids(trader_ids: List[int]) -> set:
    """Get existing position IDs from database for given traders."""
    if not trader_ids:
        return set()
    
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT position_id 
                FROM raw_data.trades 
                WHERE trader_id IN :trader_ids
            """).bindparams(bindparam('trader_ids', expanding=True))
            result = connection.execute(query, {'trader_ids': trader_ids})
            existing_ids = {row[0] for row in result}
            logger.info(f"Found {len(existing_ids)} existing position IDs in database")
            return existing_ids
    except Exception as e:
        logger.error(f"Failed to get existing position IDs: {e}")
        return set()


def process_and_load_data():
    """Main ETL function using optimized bulk processing with Polars."""
    logger.info("Starting OPTIMIZED ETL process with Polars...")
    
    csv_files = glob.glob(os.path.join(RAW_FILES_PATH, "*.positions.csv"))
    if not csv_files:
        logger.warning("No '.positions.csv' files found. Aborting ETL process.")
        return

    logger.info(f"Found {len(csv_files)} files to process.")

    # Process files in parallel using ProcessPoolExecutor
    logger.info("Processing files in parallel...")
    processed_dfs = []
    
    with ProcessPoolExecutor(max_workers=min(8, len(csv_files))) as executor:
        # Submit all files for processing
        future_to_file = {
            executor.submit(process_single_file, filepath): filepath 
            for filepath in csv_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                result_df = future.result()
                if result_df is not None and result_df.height > 0:
                    processed_dfs.append(result_df)
                    logger.info(f"Processed {filepath}: {result_df.height} rows")
            except Exception as e:
                logger.error(f"File {filepath} generated an exception: {e}")

    if not processed_dfs:
        logger.error("No valid data could be loaded from CSV files. Aborting.")
        return

    # Combine all DataFrames efficiently
    logger.info("Combining all processed files...")
    master_df = pl.concat(processed_dfs, rechunk=True)
    logger.info(f"Combined dataset has {master_df.height} rows")

    # Data transformation using Polars (much faster than pandas)
    logger.info("Cleaning and transforming data...")
    
    # Rename columns to match database schema (updated for Polars duplicate handling)
    column_mapping = {
        'Time': 'open_time_str',
        'Type': 'type',
        'Volume': 'volume_str', 
        'Symbol': 'symbol',
        'Price': 'open_price_str',
        'Time_duplicated_0': 'close_time_str',
        'Price_duplicated_0': 'close_price_str',
        'Commission': 'commission_str',
        'Swap': 'swap_str',
        'Profit': 'profit_str'
    }
    
    # Get current column names and map them
    current_cols = master_df.columns
    rename_dict = {}
    for old_col in current_cols:
        if old_col in column_mapping:
            rename_dict[old_col] = column_mapping[old_col]
    
    if rename_dict:
        master_df = master_df.rename(rename_dict)
    
    # Data cleaning and transformation with Polars
    master_df = master_df.with_columns([
        # Standardize symbols
        pl.col("symbol").map_elements(standardize_symbol, return_dtype=pl.Utf8).alias("symbol"),
        
        # Parse datetime columns
        pl.col("open_time_str").str.strptime(pl.Datetime, format="%Y.%m.%d %H:%M:%S", strict=False).alias("open_time"),
        pl.col("close_time_str").str.strptime(pl.Datetime, format="%Y.%m.%d %H:%M:%S", strict=False).alias("close_time"),
        
        # Convert numeric columns (already Float64, but re-cast if needed for consistency)
        pl.col("volume_str").cast(pl.Float64, strict=False).alias("volume"),
        pl.col("open_price_str").cast(pl.Float64, strict=False).alias("open_price"),
        pl.col("close_price_str").cast(pl.Float64, strict=False).alias("close_price"),
        pl.col("commission_str").cast(pl.Float64, strict=False).alias("commission"),
        pl.col("swap_str").cast(pl.Float64, strict=False).alias("swap"),
        pl.col("profit_str").cast(pl.Float64, strict=False).alias("profit")
    ])
    
    # Filter out rows with null essential fields
    master_df = master_df.filter(
        pl.col("open_time").is_not_null() &
        pl.col("trader_id").is_not_null() &
        pl.col("symbol").is_not_null() &
        pl.col("open_price").is_not_null()
    )
    
    logger.info(f"After cleaning: {master_df.height} rows remain")
    
    # Generate position IDs
    master_df = master_df.with_columns([
        pl.struct(["trader_id", "open_time_str", "symbol", "open_price"])
        .map_elements(
            lambda x: generate_position_id(x["trader_id"], x["open_time_str"], x["symbol"], x["open_price"]),
            return_dtype=pl.Int64
        ).alias("position_id")
    ])
    
    # Get unique trader IDs to check existing data
    unique_trader_ids = master_df["trader_id"].unique().to_list()
    
    # Get existing position IDs from database
    existing_position_ids = get_existing_position_ids(unique_trader_ids)
    
    # Filter out existing positions - only keep new ones
    if existing_position_ids:
        master_df = master_df.filter(
            ~pl.col("position_id").is_in(list(existing_position_ids))
        )
        logger.info(f"After filtering existing data: {master_df.height} new rows to insert")
    
    if master_df.height == 0:
        logger.info("No new data to insert. ETL process completed.")
        return
    
    # --- Load Stage ---
    
    # 1. Upsert Trader Info using psycopg2
    traders_df = (master_df
                 .select(["trader_id", "server", "algo_trading_pct"])
                 .unique(subset=["trader_id"])
                 .with_columns([
                     pl.col("trader_id").map_elements(
                         lambda x: f"https://www.mql5.com/en/signals/{x}",
                         return_dtype=pl.Utf8
                     ).alias("url"),
                     pl.lit(datetime.now()).alias("last_updated")
                 ]))
    
    logger.info(f"Upserting info for {traders_df.height} traders...")
    
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                data_tuples = traders_df.rows()
                insert_query = """
                    INSERT INTO raw_data.traders (trader_id, server, algo_trading_pct, url, last_updated)
                    VALUES %s
                    ON CONFLICT (trader_id) DO UPDATE SET
                        server = EXCLUDED.server,
                        algo_trading_pct = EXCLUDED.algo_trading_pct,
                        url = EXCLUDED.url,
                        last_updated = EXCLUDED.last_updated;
                """
                psycopg2.extras.execute_values(
                    cursor, insert_query, data_tuples, 
                    template='(%s, %s, %s, %s, %s)',
                    page_size=1000
                )
            conn.commit()
        logger.info("Trader info upserted successfully.")
    except Exception as e:
        logger.error(f"Failed to upsert trader info: {e}", exc_info=True)
        return

    # 2. Bulk Insert New Trades Only
    trades_df = master_df.select([
        "position_id", "trader_id", "symbol", "type", "volume", 
        "open_time", "open_price", "close_time", "close_price", 
        "commission", "swap", "profit"
    ]).drop_nulls()
    
    logger.info(f"Inserting {trades_df.height} NEW trades into the database...")
    
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                data_tuples = trades_df.rows()
                insert_query = """
                    INSERT INTO raw_data.trades (
                        position_id, trader_id, symbol, type, volume, open_time, 
                        open_price, close_time, close_price, commission, swap, profit
                    )
                    VALUES %s ON CONFLICT (position_id) DO NOTHING;
                """
                psycopg2.extras.execute_values(
                    cursor, insert_query, data_tuples, 
                    page_size=1000
                )
                inserted_rows = cursor.rowcount
                logger.info(f"Successfully inserted {inserted_rows} new trades.")
            conn.commit()
    except Exception as e:
        logger.error(f"Bulk insert failed: {e}", exc_info=True)
        return

    logger.info("Optimized ETL process completed successfully.")


def main():
    """Main function to run the ETL process."""
    start_time = datetime.now()
    logger.info(f"ETL process started at {start_time}")
    
    create_tables_if_not_exist()
    process_and_load_data()
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"ETL process completed at {end_time}. Total duration: {duration}")


if __name__ == "__main__":
    main()