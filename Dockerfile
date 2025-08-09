# --- Stage 1: Builder & Tester ---
# این مرحله برای نصب تمام وابستگی‌ها، کپی کردن کل کد و اجرای تست‌هاست
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code and tests
COPY ./src ./src
COPY ./tests ./tests

# Run tests
# اگر تست‌ها شکست بخورن، ساخت ایمیج متوقف می‌شه
RUN pytest

# --- Stage 2: Final Production Image ---
# این مرحله یک ایمیج تمیز و نهایی می‌سازه
FROM python:3.11-slim

WORKDIR /app

# Copy only the necessary production dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy only the application source code
COPY ./src ./src

# Command to run the application (you will define this later)
# CMD ["python", "src/main.py"]