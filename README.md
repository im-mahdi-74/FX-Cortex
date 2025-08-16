# FX Cortex

[![Python CI](https://github.com/im-mahdi-74/FX-Cortex/actions/workflows/test.yml/badge.svg)](https://github.com/im-mahdi-74/FX-Cortex/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/im-mahdi-74/FX-Cortex/graph/badge.svg)]("https://codecov.io/gh/im-mahdi-74/FX-Cortex")

## Project Overview
FX Cortex is an AI-powered platform designed to deliver **deep, actionable insights into retail traders' behavior**. It goes beyond traditional performance metrics by analyzing **how, why, and under what conditions traders operate**.

The platform empowers **proprietary trading firms** and **brokers** with **AI-driven behavioral metrics** to enhance efficiency, manage risk, and navigate chaotic market dynamics through **data-driven intelligence**. It is built for **high-scale, real-time analytics**, processing large volumes of trading data with low latency.

This is not just a technical demo; it’s a **real-time business solution (MVP)** demonstrating the value of advanced AI methodologies applied to real-world trading data.

## Core Solution: Real-Time Interactive Monitoring Dashboard
At the heart of FX Cortex is an **interactive, real-time monitoring dashboard** providing a comprehensive view of trading accounts:

- **Behavioral Archetype Detection**: Automatically classify trader patterns (e.g., "Cautious Scalper", "High-Risk Martingale", "News Gambler") using advanced clustering algorithms.
- **Anomaly & Fraud Detection**: Identify unusual trading activities, such as sudden changes in volume, strategy, or risk profile, which may indicate account sharing or prohibited trading methods.
- **Advanced Time Series Analysis**: Leverage hierarchical and density-based clustering to uncover subtle patterns missed by traditional analytics.
- **Predictive Risk Analytics**: Forecast expected trades, total volume, and potential profit/loss for groups of traders.

## Architecture & Technologies
- **Core Language**: Python
- **Databases & Streaming**:
  - **PostgreSQL**: For robust storage with multi-read/write capabilities.
  - **ClickHouse**: For high-performance analytics on large datasets.
  - **Redis**: For caching and real-time state management.
  - **Kafka**: For scalable, real-time data streaming and processing.
- **Data Processing & ML**: Machine Learning + Data Processing with libraries like Polars for efficient data manipulation.
- **API & Dashboard**: FastAPI backend for high-performance APIs, React frontend for an interactive UI.
- **Deployment**: Fully containerized with Docker and orchestrated with Docker Compose for reproducibility and scalability.
- **CI/CD**: Automated testing and deployment pipelines using GitHub Actions, with code coverage reporting via Codecov.

## Data Source & Approach to Real-Time Data
In a production environment, FX Cortex connects directly to a brokerage’s live data feed or trade database via Kafka and PostgreSQL. For this public demonstration, we needed a reliable source of real-world trading data.

To address this, we implemented a **sophisticated web scraping module** that sources data from public signals on [mql5.com](https://www.mql5.com). The scraper runs periodically (e.g., every few hours), mimicking human behavior to ensure data freshness while respecting the site’s infrastructure and avoiding detection. This provides a **near-live stream of data** for analysis.

The platform is **built for your data**. Its modular architecture allows seamless integration with proprietary trading records. By modifying the scraper module, you can connect your own data sources (e.g., internal databases or APIs). As long as the data adheres to the project’s standard schema and is ingested into PostgreSQL, the entire analysis and visualization pipeline will function automatically with your internal data.

**To connect your own data source**:
1. Modify the `scraper` module to read from your internal database or API.
2. Ensure the data follows the project’s standard schema and is stored in PostgreSQL.

> **Note**: The text and documentation in this section were generated with assistance from a generative AI tool to efficiently articulate the data sourcing strategy for demonstration purposes. All content has been carefully reviewed and adjusted by the developer for accuracy and clarity, with the underlying technical logic fully authored by the developer.

## Installation
To set up the project locally:
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hist_analyser.git
   cd hist_analyser
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running with Docker Compose
To run the platform with all services (PostgreSQL, Kafka, debezium, ClickHouse, Redis, FastAPI, React):
1. Ensure Docker and Docker Compose are installed.
2. Start the services:
   ```bash
   docker-compose up -d
   curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @pg-connector.json
   ```
3. Access the dashboard at `http://localhost:3000` (or the configured port for the React frontend).
4. Stop the services:
   ```bash
   docker-compose down
   ```

## Testing
To run tests locally:
```bash
export TEST_ENV=true
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/
```

**Test Status**:  
[![Tests](https://github.com/your-username/hist_analyser/actions/workflows/test.yml/badge.svg)](https://github.com/your-username/hist_analyser/actions/workflows/test.yml)

## CI/CD
The project uses **GitHub Actions** for continuous integration and deployment. Tests are automatically run on every push or pull request to the `main`, `develop`, or `etl` branches, with code coverage reports uploaded to Codecov.

---

# پلتفرم تحلیل رفتار معامله‌گران فارکس مبتنی بر هوش مصنوعی FX Cortex

## معرفی پروژه
FX Cortex یک پلتفرم مبتنی بر هوش مصنوعی است که برای ارائه **دیدگاه‌های عمیق و کاربردی از رفتار معامله‌گران خرد** طراحی شده است. این سیستم فراتر از معیارهای عملکردی ساده عمل می‌کند و بر **چگونگی، چرایی، و شرایط انجام معاملات** تمرکز دارد.

این پلتفرم به **پراپ فرم‌ها** و **بروکرها** امکان می‌دهد تا **متریک‌های رفتاری مبتنی بر هوش مصنوعی** را به دست آورند که بهره‌وری را افزایش می‌دهد، ریسک را مدیریت می‌کند، و دینامیک‌های پیچیده بازار را از طریق **هوش داده‌محور** درک می‌کند. این سیستم برای **تحلیل بلادرنگ مقیاس بالا** طراحی شده و قادر به پردازش حجم زیادی از داده‌های معاملاتی با تأخیر کم است.

این پروژه صرفاً یک نمایش فنی نیست؛ بلکه یک **راه‌حل تجاری بلادرنگ (MVP)** است که ارزش استفاده از متدولوژی‌های پیشرفته هوش مصنوعی را روی داده‌های واقعی معاملات نشان می‌دهد.

## راه‌حل اصلی: داشبورد مانیتورینگ تعاملی بلادرنگ
هسته این پروژه یک **داشبورد نظارتی تعاملی و بلادرنگ** است که نمای جامعی از حساب‌های معاملاتی ارائه می‌دهد:

- **کشف الگوهای رفتاری**: شناسایی خودکار الگوهای معامله‌گران (مانند «اسکلپر محتاط»، «مارتینگل پرریسک»، «قمارباز خبری») با استفاده از الگوریتم‌های خوشه‌بندی پیشرفته.
- **تشخیص ناهنجاری و تقلب**: شناسایی فعالیت‌های غیرمتعارف مانند تغییرات ناگهانی در حجم، استراتژی، یا پروفایل ریسک که ممکن است نشان‌دهنده اشتراک‌گذاری حساب یا روش‌های معاملاتی ممنوعه باشد.
- **تحلیل پیشرفته سری‌های زمانی**: استفاده از خوشه‌بندی‌های سلسله‌مراتبی و مبتنی بر تراکم برای کشف الگوهایی که تحلیل‌های سنتی قادر به شناسایی آنها نیستند.
- **تحلیل پیش‌بینی‌کننده**: پیش‌بینی تعداد معاملات، حجم کل، و سود/زیان احتمالی برای گروه‌های معامله‌گران.

## معماری و فناوری‌ها
- **زبان اصلی**: Python
- **پایگاه داده و استریمینگ**:
  - **PostgreSQL**: برای ذخیره‌سازی مقاوم با قابلیت خواندن/نوشتن چندگانه.
  - **ClickHouse**: برای تحلیل‌های با عملکرد بالا روی داده‌های بزرگ.
  - **Redis**: برای کش کردن و مدیریت حالت بلادرنگ.
  - **Kafka**: برای استریمینگ و پردازش داده‌های بلادرنگ مقیاس‌پذیر.
- **پردازش داده و یادگیری ماشین**: استفاده از کتابخانه‌هایی مانند Polars برای پردازش کارآمد داده‌ها.
- **API و داشبورد**: Backend با FastAPI برای APIهای با عملکرد بالا و Frontend تعاملی با React.
- **استقرار**: کاملاً کانتینریزه‌شده با Docker و مدیریت‌شده با Docker Compose برای تکرارپذیری و مقیاس‌پذیری.
- **CI/CD**: خط لوله‌های خودکار تست و استقرار با استفاده از GitHub Actions و گزارش پوشش کد با Codecov.

## منبع داده و رویکرد به داده‌های زنده
در یک محیط تولیدی، FX Cortex به فید داده زنده یا پایگاه داده معاملات یک بروکر از طریق Kafka و PostgreSQL متصل می‌شود. برای این نسخه نمایشی عمومی، به یک منبع قابل اعتماد از داده‌های معاملاتی واقعی نیاز داشتیم.

برای حل این مشکل، یک **ماژول وب‌اسکرپینگ پیشرفته** پیاده‌سازی کردیم که داده‌ها را از سیگنال‌های عمومی سایت [mql5.com](https://www.mql5.com) استخراج می‌کند. این اسکرپر به‌صورت دوره‌ای (مثلاً هر چند ساعت یک‌بار) اجرا می‌شود و با شبیه‌سازی رفتار انسانی، از شناسایی شدن جلوگیری می‌کند و داده‌های تقریباً زنده را برای تحلیل فراهم می‌آورد.

این پلتفرم **برای داده‌های شما طراحی شده است**. معماری ماژولار آن امکان یکپارچه‌سازی آسان با سوابق معاملاتی اختصاصی شما را فراهم می‌کند. با تغییر ماژول اسکرپر، می‌توانید منابع داده داخلی خود (مانند پایگاه داده یا API) را متصل کنید. تا زمانی که داده‌ها طبق اسکیمای استاندارد پروژه در PostgreSQL ذخیره شوند، خط لوله تحلیل و بصری‌سازی به‌صورت خودکار با داده‌های شما کار خواهد کرد.

**برای اتصال منبع داده خود**:
1. ماژول `scraper` را برای خواندن از پایگاه داده یا API داخلی خود تغییر دهید.
2. اطمینان حاصل کنید که داده‌ها طبق اسکیمای استاندارد پروژه در PostgreSQL ذخیره می‌شوند.

> **توجه**:  
> متن و مستندات این بخش با کمک ابزار تولید محتوای مبتنی بر هوش مصنوعی ایجاد شده‌اند تا استراتژی استخراج داده‌ها به‌صورت کارآمد برای نسخه نمایشی بیان شود.  
> تمام محتوا توسط توسعه‌دهنده با دقت بازبینی و اصلاح شده تا از صحت و وضوح آن اطمینان حاصل شود، و منطق فنی زیربنایی به‌صورت کامل توسط توسعه‌دهنده نوشته شده است.

## نصب پروژه
برای راه‌اندازی پروژه به‌صورت محلی:
1. مخزن را کلون کنید:
   ```bash
   git clone https://github.com/your-username/hist_analyser.git
   cd hist_analyser
   ```
2. یک محیط مجازی ایجاد و فعال کنید:
   ```bash
   python -m venv env
   source env/bin/activate  # در ویندوز: env\Scripts\activate
   ```
3. وابستگی‌ها را نصب کنید:
   ```bash
   pip install -r requirements.txt
   ```

## اجرا با Docker Compose
برای اجرای پلتفرم با تمام سرویس‌ها (PostgreSQL، Kafka، debezium. ClickHouse، Redis، FastAPI، React):
1. اطمینان حاصل کنید که Docker و Docker Compose نصب شده‌اند.
2. سرویس‌ها را راه‌اندازی کنید:
   ```bash
   docker-compose up -d
   curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @pg-connector.json
   ```
3. به داشبورد در آدرس `http://localhost:3000` (یا پورت تنظیم‌شده برای frontend) دسترسی پیدا کنید.
4. برای توقف سرویس‌ها:
   ```bash
   docker-compose down
   ```

## تست پروژه
برای اجرای تست‌ها به‌صورت محلی:
```bash
export TEST_ENV=true
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/
```

**وضعیت تست‌ها**:  
[![Tests](https://github.com/your-username/hist_analyser/actions/workflows/test.yml/badge.svg)](https://github.com/your-username/hist_analyser/actions/workflows/test.yml)

## CI/CD
پروژه از **GitHub Actions** برای یکپارچه‌سازی و استقرار مداوم استفاده می‌کند. تست‌ها به‌صورت خودکار برای هر push یا pull request در شاخه‌های `main`، `develop`، یا `etl` اجرا می‌شوند و گزارش‌های پوشش کد به Codecov آپلود می‌شوند.