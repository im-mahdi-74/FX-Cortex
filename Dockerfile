# --- Stage 1: Builder & Tester ---
# This stage installs all dependencies (system and Python), copies all code, and runs tests.
FROM python:3.11-slim as builder

# --- Install System Dependencies for Selenium/Chrome ---
# Install prerequisites
RUN apt-get update && apt-get install -y wget gnupg

# Add Google's official key
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg

# Add the Chrome repository
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome and the matching Chromedriver
RUN apt-get update && apt-get install -y google-chrome-stable chromedriver

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code and tests
COPY ./src ./src
COPY ./tests ./tests

# Run tests to verify the application
# If tests fail, the build will stop here.
RUN pytest

# --- Stage 2: Final Production Image ---
# This stage creates a lightweight, clean image for production.
FROM python:3.11-slim

# --- Also install Chrome in the final image ---
# It's needed for the scraper to run in production.
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
# Use --no-install-recommends to keep the image smaller
RUN apt-get update && apt-get install -y google-chrome-stable chromedriver --no-install-recommends

WORKDIR /app

# Copy only the necessary installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy only the application source code (no tests)
COPY ./src ./src

# --- NEW: Copy template data into the image ---
# This ensures the application has some initial data to work with on first run.
COPY ./data/raw_files ./data/raw_files

# --- NEW: Set the default command to run the bootstrap script ---
# This will be executed when the container starts for the first time.
CMD ["python", "src/bootstrap.py"]