# Databricks Apps Custom Image - Wind Turbine Analytics
# Base image: Databricks Runtime compatible
FROM python:3.10-slim

# Install system dependencies for Kaleido/Chromium (avec root)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libnss3 \
        libgconf-2-4 \
        libfontconfig1 \
        libxss1 \
        libappindicator3-1 \
        libxtst6 \
        libgtk-3-0 \
        libgbm1 \
        libasound2 \
        libx11-xcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxshmfence1 \
        ca-certificates \
        fonts-liberation \
        libappindicator1 \
        lsb-release \
        xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by app.yaml
CMD ["python", "run_app.py"]
