import os
import sys
import logging

# --- Path and Import Setup ---
# This adds the 'src' directory to the Python path, making imports clean.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

# Now we can use absolute imports from the 'src' root.
from scraper import url_collector
from scraper import scraper as downloader

# --- Configuration ---
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "logs/bootstrap.log")

# --- Logger Setup ---
def setup_logger():
    """Sets up the logger for the bootstrap process."""
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

# --- Main Bootstrap Function ---
def main():
    """
    Runs the initial data collection and download pipeline unconditionally.
    1. Collects signal URLs and metadata.
    2. Downloads the initial batch of trading history.
    """
    logger.info("=============================================")
    logger.info("===   STARTING INITIAL PROJECT BOOTSTRAP  ===")
    logger.info("=============================================")

    try:
        # Step 1: Run the URL Collector to get the latest list of signals
        logger.info("--- Step 1: Running URL Collector ---")
        url_collector.main()
        logger.info("--- URL Collector Finished ---")
        
        # Step 2: Run the Downloader to fetch the history for the collected signals
        logger.info("--- Step 2: Running Initial Downloader ---")
        downloader.main()
        logger.info("--- Initial Downloader Finished ---")
        
        logger.info("--- Bootstrap Process Completed Successfully ---")
    except Exception as e:
        logger.critical(f"A critical error occurred during the bootstrap process: {e}", exc_info=True)

    logger.info("=============================================")
    logger.info("===      PROJECT BOOTSTRAP COMPLETED      ===")
    logger.info("=============================================")


if __name__ == "__main__":
    main()
