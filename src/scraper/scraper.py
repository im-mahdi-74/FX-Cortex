import os
import time
import random
import logging
import requests
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from dotenv import load_dotenv

# --- Configuration and Setup ---
load_dotenv()
MQL5_USERNAME = os.getenv("MQL5_USERNAME")
MQL5_PASSWORD = os.getenv("MQL5_PASSWORD")
RAW_FILES_PATH = "data/raw_files/"
SIGNAL_CSV_PATH = "signals_to_track.csv"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/scraper.log")
LOCK_FILE_PATH = "logs/scraper.lock" # Path for the lock file

# --- Logger Setup ---
def setup_logger():
    """Sets up the logger for the application."""
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

# --- Helper Function ---
def sanitize_filename(name):
    """Removes characters that are invalid for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

# --- Main Scraper Class ---
class MQL5Downloader:
    """
    Logs into mql5.com, reads a list of signals from a CSV,
    and downloads their trading history, overwriting existing files.
    """
    LOGIN_URL = "https://www.mql5.com/en/auth_login"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.session = requests.Session()
        self.user_agent_rotator = UserAgent()
        self.session.headers.update({"User-Agent": self.user_agent_rotator.random})

    def _initialize_driver(self):
        """Initializes a headless Chrome WebDriver."""
        logger.info("Initializing headless Chrome driver...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={self.user_agent_rotator.random}")
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        """Logs into mql5.com and verifies the session."""
        if not self.username or not self.password:
            logger.error("Username or password not found. Please check your .env file.")
            return False
        self._initialize_driver()
        logger.info(f"Attempting to log in as {self.username}...")
        try:
            self.driver.get(self.LOGIN_URL)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'Login'))).send_keys(self.username)
            self.driver.find_element(By.ID, 'Password').send_keys(self.password)
            time.sleep(1)
            self.driver.find_element(By.ID, 'loginSubmit').click()
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{self.username}')]"))
            )
            logger.info("Login successful and verified.")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.driver.save_screenshot("downloader_login_failed.png")
            return False

    def _transfer_cookies_to_session(self):
        """Transfers cookies from the Selenium driver to the requests session."""
        logger.info("Transferring browser cookies to requests session...")
        selenium_cookies = self.driver.get_cookies()
        for cookie in selenium_cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])

    def download_history(self, signal_info):
        """Downloads the trading history, overwriting any existing file."""
        signal_url = signal_info['url']
        server_name = signal_info['server']
        algo_pct = signal_info.get('algo_trading_pct', '0')

        export_url = f"{signal_url.strip()}/export/history"
        signal_id = signal_url.strip().split('/')[-1]

        safe_server_name = sanitize_filename(server_name)
        filename = os.path.join(RAW_FILES_PATH, f"{signal_id}_{safe_server_name}_algo{algo_pct}.history.csv")

        # --- LOGIC CHANGE: The check for existing file is REMOVED ---
        # This ensures we always download the latest version.

        try:
            time.sleep(random.uniform(3, 7))
            logger.info(f"Requesting latest data for signal: {signal_id} on server: {server_name}")
            response = self.session.get(export_url, timeout=30)

            if response.status_code == 200 and 'text/csv' in response.headers.get('Content-Type', ''):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Successfully downloaded and updated '{filename}'.")
            else:
                logger.warning(f"Failed to download for signal {signal_id}. Status: {response.status_code}.")

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred while downloading for signal {signal_id}: {e}")

    def run(self):
        """Main method to run the downloader."""
        if not self.login():
            self.close()
            return

        self._transfer_cookies_to_session()

        with open(SIGNAL_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            signals_to_scrape = list(reader)

        if not signals_to_scrape:
            logger.warning(f"'{SIGNAL_CSV_PATH}' is empty. No signals to download.")
            return

        logger.info(f"Found {len(signals_to_scrape)} signals to process from CSV.")
        for signal_info in signals_to_scrape:
            if signal_info.get('url'):
                self.download_history(signal_info)
        
        self.close()

    def close(self):
        """Closes the Selenium WebDriver."""
        if self.driver:
            logger.info("Closing the browser driver.")
            self.driver.quit()

# --- Main Execution ---
def main():
    """The main function to execute the downloader."""
    logger.info("--- Scraper execution triggered ---")

    if os.path.exists(LOCK_FILE_PATH):
        logger.warning("Lock file exists. Another scraper process may be running. Aborting.")
        return
    
    try:
        with open(LOCK_FILE_PATH, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info("--- Starting Downloader ---")
        if not os.path.exists(SIGNAL_CSV_PATH) or os.path.getsize(SIGNAL_CSV_PATH) == 0:
            logger.error(f"'{SIGNAL_CSV_PATH}' not found or is empty. Please run the url_collector.py script first. Aborting.")
            return

        downloader = MQL5Downloader(MQL5_USERNAME, MQL5_PASSWORD)
        downloader.run()
        logger.info("--- Downloader Finished ---")

    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
    finally:
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)
            logger.info("Lock file removed.")

if __name__ == "__main__":
    main()
