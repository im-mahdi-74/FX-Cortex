# FX Cortex

## Project Overview
This project is an AI-powered platform designed to provide **deep, actionable insights into retail traders' behavior**.  
It goes beyond simple performance metrics, focusing on **how, why, and under what conditions traders operate**.

It enables **prop firms** and **brokers** to access **AI-driven behavioral metrics** that improve efficiency, manage risk, and understand chaotic market dynamics through **data-driven intelligence**.

This is not just a technical demo; it’s a **real-time business solution (MVP)** showcasing the value of applying advanced AI methodologies to real trading data.

---

## Core Solution: Real-Time Interactive Monitoring Dashboard
At its heart, the platform provides an **interactive, real-time monitoring dashboard** offering a comprehensive view of trading accounts:

- **Behavioral Archetype Detection:**  
  Automatically detect and classify trader patterns (e.g., "Cautious Scalper", "High-Risk Martingale", "News Gambler") using advanced clustering algorithms.
  
- **Anomaly & Fraud Detection:**  
  Identify unusual trading activities, such as sudden changes in volume, strategy, or risk profile, which may indicate account sharing or prohibited trading methods.
  
- **Advanced Time Series Analysis:**  
  Apply clustering techniques (hierarchical, density-based like DBSCAN) to uncover subtle patterns missed by traditional analytics.
  
- **Predictive Risk Analytics:**  
  Forecast expected trades, total volume, and potential PnL for groups of traders.

---

## Architecture & Technologies
- **Core Language:** Python  
- **Databases:**
  - SQLite for raw data storage
  - DuckDB for high-performance analytics  
  - Scalable to Kafka, ClickHouse, Hadoop, Spark for big data workloads
- **Data Processing & ML:** Machine Learning + Data Processing
- **API & Dashboard:** FastAPI backend, React frontend
- **Deployment:** Fully containerized with Docker for reproducibility

---


## Data Source & Our Approach to "Live" Data

In an ideal production environment, this platform would connect directly to a brokerage's live data feed or trade database. However, for this public demonstration, we needed a reliable source of real-world trading data.

To solve this, we implemented a sophisticated **web scraping module** that sources data from public signals on [mql5.com](https://www.mql5.com). To ensure data freshness while respecting the site's infrastructure and avoiding detection, the scraper is designed to run periodically (e.g., every few hours), mimicking human behavior. This approach provides a **near-live stream of data** for analysis.

This platform is **built for your data**. The architecture is intentionally modular to allow for seamless integration with your proprietary trading records. By modifying the scraper module, you can easily connect your own data sources. As long as the data is written to the database following the project's standard schema, the entire analysis and visualization pipeline will function automatically with your internal data.
↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
<!-- AI-assisted generation disclosure -->
> **Note:** The text and documentation in this section were generated with assistance from a generative AI tool. The intention was to efficiently articulate the data sourcing strategy primarily for demonstration purposes. All content has been carefully reviewed by the developer and adjusted for accuracy and clarity, and the underlying technical logic was fully authored mensch-style.


**To connect your own data source:**
1. Modify the `scraper` module to read from your internal DB/API.
2. Ensure the data follows the project’s standard schema and is stored in SQLite.

---

# پلتفرم بلارنگ تحلیل رفتار معامله‌گران فارکس مبتنی بر هوش مصنوعی FX Cortex

## معرفی پروژه
این پروژه یک پلتفرم مبتنی بر هوش مصنوعی است که برای ارائه دیدگاه‌های عمیق و کاربردی از رفتار معامله‌گران خرد طراحی شده است.  
سیستم فراتر از معیارهای عملکردی ساده رفته و بررسی می‌کند که **معامله‌گران چگونه، چرا و در چه شرایطی معامله می‌کنند**.  

این ابزار به پراپ‌ فرم‌ها و بروکرها کمک می‌کند تا **متریک‌های رفتاری واقعی** (تنظیم‌شده و کشف‌شده توسط هوش مصنوعی) به دست آورند که باعث افزایش بهره‌وری، مدیریت ریسک اتومات مبتنی بر هوش مصنوعی و درک عمیق‌تر دینامیک بازار می‌شود.

این پلتفرم تنها یک نمایش فنی نیست؛ بلکه یک **راه‌حل تجاری بلادرنگ (Real-time)** است که به‌عنوان **MVP مینیمال** برای اثبات ارزش متدولوژی‌های پیشرفته هوش مصنوعی روی داده‌های واقعی ساخته شده است.

---

## راه‌حل اصلی: داشبورد مانیتورینگ تعاملی بلادرنگ
قلب این پروژه یک داشبورد نظارتی تعاملی است که نمای جامعی از فعالیت‌های معاملاتی ارائه می‌دهد:

- **کشف رفتار و شناسایی الگوهای معاملاتی (Archetypes):**  
  شناسایی خودکار الگوهای معامله‌گران (مثل «اسکلپر محتاط»، «شباهت معنایی در پارامتر ها»، «مارتینگل پرریسک»، «قمارباز خبری») با استفاده از الگوریتم‌های خوشه‌بندی پیشرفته.
  
- **کشف ناهنجاری و تقلب:**  
  شناسایی فعالیت‌های غیرمتعارف (تغییرات ناگهانی حجم، استراتژی یا ریسک وانواع روش های سواستفاده) که می‌تواند نشانه اشتراک‌گذاری حساب یا معاملات ممنوعه باشد.
  
- **تحلیل پیشرفته سری‌های زمانی:**  
  استفاده از خوشه‌بندی‌های سلسله‌مراتبی و مبتنی بر تراکم (مثل DBSCAN) برای کشف الگوهای ظریف که تحلیل سنتی قادر به یافتن آنها نیست.

- **تحلیل پیش‌بینی‌کننده:**  
  پیش‌بینی سود/زیان احتمالی و تعداد معاملات آینده برای مدیریت بهتر ریسک.

---

## معماری و فناوری
- **زبان اصلی:** Python 
- **پایگاه داده:**
  - SQLite برای ذخیره داده خام
  - DuckDB برای پردازش تحلیلی و کوئری‌های پیچیده  
  - قابلیت ارتقاء به Kafka, ClickHouse, Hadoop, Spark برای Big Data
- **تحلیل داده و ML:** Machine Learning + Data Processing
- **API و داشبورد:** Backend با FastAPI و Frontend تعاملی با React
- **استقرار:** Docker برای کانتینریزه‌کردن کل سیستم

---


## منبع داده و رویکرد ما به داده‌های زنده

در یک محیط تولیدی ایده‌آل، این پلتفرم باید مستقیماً به فید داده زنده یا پایگاه داده معاملات یک بروکر متصل شود. با این حال، برای این نسخه نمایشی عمومی، ما به یک منبع قابل اعتماد از داده‌های معاملاتی واقعی نیاز داشتیم.

برای حل این مشکل، ما یک ماژول **وب اسکرپینگ پیشرفته** پیاده‌سازی کردیم که داده‌ها را از سیگنال‌های عمومی سایت [mql5.com](https://www.mql5.com) استخراج می‌کند. برای تضمین تازگی داده‌ها و در عین حال احترام به زیرساخت سایت و جلوگیری از شناسایی شدن، اسکرپر طوری طراحی شده که به صورت دوره‌ای (مثلاً هر چند ساعت یک بار) اجرا شود و **رفتار انسان را شبیه‌سازی** کند. این رویکرد یک جریان داده تقریباً زنده را برای تحلیل فراهم می‌کند.

این پلتفرم **برای داده‌های شما ساخته شده** است. معماری آن به صورت کاملاً ماژولار طراحی شده تا امکان یکپارچه‌سازی آسان با سوابق معاملاتی اختصاصی شما را فراهم کند. با تغییر دادن ماژول scraper، شما می‌توانید به راحتی منابع داده داخلی خود را به سیستم متصل کنید. تا زمانی که داده‌ها طبق اسکیمای استاندارد پروژه در پایگاه داده نوشته شوند، کل خط لوله تحلیل و بصری‌سازی به صورت خودکار با داده‌های شما کار خواهد کرد.
↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
<!-- افشای تولید با کمک هوش مصنوعی -->
> **توجه:**  
> متن و مستندات این بخش با کمک یک ابزار تولید محتوا مبتنی بر هوش مصنوعی ایجاد شده‌اند.  
> هدف اصلی، بیان کارآمد و سریع استراتژی استخراج داده‌ها به منظور ارائه نسخه نمایشی بوده است.  
> تمامی محتوا با دقت توسط توسعه‌دهنده بازبینی و اصلاح شده تا از صحت و وضوح آن اطمینان حاصل شود،  
> و منطق فنی زیربنایی به صورت کامل به سبک انسانی نوشته شده است.




**برای اتصال منبع داده خود:**
1. ماژول `scraper` را برای خواندن داده از پایگاه داده یا API داخلی خود تغییر دهید.
2. داده‌ها را طبق اسکیمای استاندارد پروژه در SQLite ذخیره کنید.

---

