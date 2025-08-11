import os
import time
import random
import logging
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
from dotenv import load_dotenv

# --- Configuration and Setup ---
load_dotenv()
MQL5_USERNAME = os.getenv("MQL5_USERNAME")
MQL5_PASSWORD = os.getenv("MQL5_PASSWORD")
OUTPUT_CSV_PATH = "signals_to_track.csv"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/collector.log")
MAX_SIGNALS_TO_COLLECT = 50

# --- Logger Setup ---
def setup_logger():
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

# --- Main Collector Class ---
class URLCollector:
    LOGIN_URL = "https://www.mql5.com/en/auth_login"
    SIGNALS_BASE_URL = "https://www.mql5.com/en/signals/mt5/page{}"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.user_agent_rotator = UserAgent()
        self.collected_signals = []

    def _initialize_driver(self):
        logger.info("Initializing headless Chrome driver...")
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={self.user_agent_rotator.random}")
        self.driver = webdriver.Chrome(options=options)

    def login(self):
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
            self.driver.save_screenshot("collector_login_failed.png")
            return False

    def collect_signals(self):
        page_number = 1
        while len(self.collected_signals) < MAX_SIGNALS_TO_COLLECT:
            list_page_url = self.SIGNALS_BASE_URL.format(page_number)
            logger.info(f"Scraping signal list page: {list_page_url}")
            self.driver.get(list_page_url)
            time.sleep(random.uniform(2, 4))

            signal_cards = self.driver.find_elements(By.CSS_SELECTOR, "a.signal-card__wrapper")
            if not signal_cards:
                logger.info("No more signal cards found. Ending collection.")
                break

            signal_urls_on_page = [card.get_attribute('href').split('?')[0] for card in signal_cards]

            for url in signal_urls_on_page:
                if len(self.collected_signals) >= MAX_SIGNALS_TO_COLLECT:
                    break
                
                logger.info(f"Visiting signal page: {url}")
                self.driver.get(url)
                time.sleep(random.uniform(2, 5))

                try:
                    server_element = self.driver.find_element(By.XPATH, "//form[input[@name='substring_filter']]//a")
                    server_name = server_element.text.strip()
                    
                    # --- NEW: Extract Algo Trading Percentage ---
                    algo_trading_pct = "0" # Default value
                    try:
                        # Find the text element that contains "Algo trading:"
                        algo_element = self.driver.find_element(By.XPATH, "//*[local-name()='svg']//*[local-name()='text' and contains(text(), 'Algo trading:')]")
                        # Extract the number from the text
                        match = re.search(r'(\d+)', algo_element.text)
                        if match:
                            algo_trading_pct = match.group(1)
                    except NoSuchElementException:
                        logger.warning(f"Algo trading percentage not found for {url}. Defaulting to 0.")

                    logger.info(f"Found Server: {server_name}, Algo Trading: {algo_trading_pct}%")
                    self.collected_signals.append({'url': url, 'server': server_name, 'algo_trading_pct': algo_trading_pct})
                
                except NoSuchElementException:
                    logger.warning(f"Could not find server name for URL: {url}")
            
            page_number += 1

    def save_to_csv(self):
        if not self.collected_signals:
            logger.warning("No signals were collected. CSV file will not be created.")
            return

        logger.info(f"Saving {len(self.collected_signals)} signals to {OUTPUT_CSV_PATH}...")
        # Add the new fieldname to the list
        with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'server', 'algo_trading_pct'])
            writer.writeheader()
            writer.writerows(self.collected_signals)
        logger.info("Successfully saved to CSV.")

    def run(self):
        if not self.login():
            self.close()
            return
        self.collect_signals()
        self.save_to_csv()
        self.close()

    def close(self):
        if self.driver:
            logger.info("Closing the browser driver.")
            self.driver.quit()

# --- Main Execution ---
def main():
    logger.info("--- Starting URL Collector ---")
    collector = URLCollector(MQL5_USERNAME, MQL5_PASSWORD)
    collector.run()
    logger.info("--- URL Collector Finished ---")

if __name__ == "__main__":
    main()