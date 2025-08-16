## Guide to Adding New Data Sources to FX-Cortex

This document will teach you how to connect your data source (such as an API or CSV files) to the FX-Cortex platform. Thanks to the project's **Event-Driven architecture**, you do not need to understand the internal complexities of Kafka or Debezium.

### Core Concept: Data Contract

All you need to do is write a Python script that reads your data, converts it to our standard format, and finally inserts (INSERT) it into the two main tables in our PostgreSQL database.

Once new data is committed to the database, our real-time pipeline automatically detects it and sends it for analysis and processing by AI models.

---

### 1. Database Structure (Schema)

Your data must conform to the structure of the two tables below. These tables are in the schema named `raw_data`.

#### Table raw\_data.traders

This table stores general information about each trader.

| Column Name        | Data Type    | Description                                                 |
| ------------------ | ------------ | ----------------------------------------------------------- |
| trader\_id         | INTEGER      | (Primary key) Unique identifier for the trader              |
| server             | VARCHAR(255) | The name of the server or broker where the trader is active |
| algo\_trading\_pct | INTEGER      | Percentage of trades executed by an algorithm (0-100)       |
| url                | VARCHAR(255) | Trader profile link (optional)                              |
| last\_updated      | TIMESTAMPTZ  | Date and time of last update (with timezone)                |

#### Table raw\_data.trades

This table stores the details of each trade.

| Column Name  | Data Type   | Description                                             |
| ------------ | ----------- | ------------------------------------------------------- |
| position\_id | BIGINT      | (Primary key) Unique identifier for each trade          |
| trader\_id   | INTEGER     | (Foreign key) References `trader_id` in `traders` table |
| symbol       | VARCHAR(50) | Standardized trading symbol (e.g., EURUSD, XAUUSD)      |
| type         | VARCHAR(10) | Trade type (e.g., buy or sell)                          |
| volume       | FLOAT       | Trade volume (lot)                                      |
| open\_time   | TIMESTAMPTZ | Trade opening time (with timezone)                      |
| open\_price  | FLOAT       | Opening price of the trade                              |
| close\_time  | TIMESTAMPTZ | Trade closing time (with timezone)                      |
| close\_price | FLOAT       | Closing price of the trade                              |
| commission   | FLOAT       | Commission fee                                          |
| swap         | FLOAT       | Swap fee (overnight interest)                           |
| profit       | FLOAT       | Final profit or loss of the trade                       |

---

### 2. Step-by-Step Guide

#### Step 1: Create a Script

Create a new Python file in `src/ingestion/`. Example: `src/ingestion/my_api_importer.py`.

#### Step 2: Fetch and Transform Data

Retrieve the data from your source and transform it to match the columns of the tables above. Using the `pandas` library is recommended.

**Important:** Make sure to use the `standardize_symbol` function in `etl_processor.py` to clean up your trading symbol names, or extend it yourself to standardize symbol names, e.g., `EURUSE.a -> EURUSD`, etc.

#### Step 3: Insert Data into Database

Use a script similar to the template below to connect to the database and insert data efficiently.

---

### 3. Template Script (`template_importer.py`)

```python
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
```

-----------------------------------------------------------------------------------------------


## راهنمای افزودن منابع داده جدید به FX-Cortex

این سند به شما آموزش می‌دهد که چگونه منبع داده خود (مانند یک API یا فایل‌های CSV) را به پلتفرم FX-Cortex متصل کنید. به لطف معماری **رویداد-محور (Event-Driven)** این پروژه، شما نیازی به درک پیچیدگی‌های داخلی Kafka یا Debezium ندارید.

### مفهوم اصلی: قرارداد داده

تنها کاری که باید انجام دهید، نوشتن یک اسکریپت پایتون است که داده‌ها را بخواند، به فرمت استاندارد ما تبدیل کند و در نهایت در دو جدول اصلی پایگاه داده PostgreSQL ما درج (INSERT) شود.

به محض اینکه داده جدید در پایگاه داده ثبت شود، خط لوله بلادرنگ ما به صورت خودکار آن را تشخیص داده و برای تحلیل و پردازش توسط مدل‌های هوش مصنوعی ارسال می‌کند.

---

### ۱. ساختار پایگاه داده (Schema)

داده‌های شما باید با ساختار دو جدول زیر مطابقت داشته باشند. این جداول در schema ای به نام `raw_data` قرار دارند.

#### جدول raw\_data.traders

این جدول اطلاعات کلی هر معامله‌گر را ذخیره می‌کند.

| نام ستون           | نوع داده     | توضیحات                                                 |
| ------------------ | ------------ | ------------------------------------------------------- |
| trader\_id         | INTEGER      | (کلید اصلی) شناسه منحصر به فرد معامله‌گر                |
| server             | VARCHAR(255) | نام سرور یا بروکری که معامله‌گر در آن فعال است          |
| algo\_trading\_pct | INTEGER      | درصد معاملاتی که توسط ربات انجام شده (0 تا 100)         |
| url                | VARCHAR(255) | لینک پروفایل معامله‌گر (اختیاری)                        |
| last\_updated      | TIMESTAMPTZ  | تاریخ و زمان آخرین به‌روزرسانی اطلاعات (با منطقه زمانی) |

#### جدول raw\_data.trades

این جدول جزئیات هر معامله را ذخیره می‌کند.

| نام ستون     | نوع داده    | توضیحات                                                  |
| ------------ | ----------- | -------------------------------------------------------- |
| position\_id | BIGINT      | (کلید اصلی) شناسه منحصر به فرد هر معامله                 |
| trader\_id   | INTEGER     | (کلید خارجی) به `trader_id` در جدول `traders` اشاره دارد |
| symbol       | VARCHAR(50) | نماد معاملاتی استاندارد شده (مثلاً EURUSD, XAUUSD)       |
| type         | VARCHAR(10) | نوع معامله (مثلاً buy یا sell)                           |
| volume       | FLOAT       | حجم معامله (لات)                                         |
| open\_time   | TIMESTAMPTZ | زمان باز شدن معامله (با منطقه زمانی)                     |
| open\_price  | FLOAT       | قیمت باز شدن معامله                                      |
| close\_time  | TIMESTAMPTZ | زمان بسته شدن معامله (با منطقه زمانی)                    |
| close\_price | FLOAT       | قیمت بسته شدن معامله                                     |
| commission   | FLOAT       | هزینه کمیسیون                                            |
| swap         | FLOAT       | هزینه سواپ (بهره شبانه)                                  |
| profit       | FLOAT       | سود یا زیان نهایی معامله                                 |

---

### ۲. راهنمای قدم به قدم

#### قدم اول: ایجاد اسکریپت

یک فایل پایتون جدید در مسیر `src/ingestion/` بسازید. مثال: `src/ingestion/my_api_importer.py`.

#### قدم دوم: دریافت و تبدیل داده

داده‌ها را از منبع خود دریافت کرده و به فرمتی تبدیل کنید که با ستون‌های جداول بالا مطابقت داشته باشد. استفاده از کتابخانه `pandas` توصیه می‌شود.

```markdown
**نکته مهم:** حتماً از تابع `standardize_symbol` که در `etl_processor.py` وجود دارد، برای پاک‌سازی نام نمادهای معاملاتی خود استفاده کنید یا خودتان تابع ساده ی توسعه دهید برای استاندارد شدن اسم نمادها مثلا  'EURUSE.a -> EURUSD' و ...
```

#### قدم سوم: درج داده در دیتابیس

از یک اسکریپت شبیه به الگوی زیر برای اتصال به دیتابیس و درج بهینه داده‌ها استفاده کنید.

---

### ۳. اسکریپت الگو (`template_importer.py`)

```python
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
DB_HOST = "db"  # همیشه از نام سرویس در داکر استفاده کنید
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def import_my_data():
    """
    یک تابع نمونه برای دریافت، تبدیل و بارگذاری داده.
    """
    logging.info("Starting custom data import...")

    # =================================================================
    # ۱. داده خود را اینجا دریافت و پردازش کنید
    # مثال: داده‌های ساختگی
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
    # ۲. داده‌ها را در دیتابیس درج کنید
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
```
