# LottoBot Docker Image
FROM python:3.11-slim

# Set timezone to KST (Asia/Seoul)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install cron and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY lotto.py .
COPY crontab /etc/cron.d/lotto-cron
COPY entrypoint.sh /entrypoint.sh

# Set proper permissions for cron
RUN chmod 0644 /etc/cron.d/lotto-cron && \
    chmod +x /entrypoint.sh && \
    crontab /etc/cron.d/lotto-cron && \
    touch /var/log/cron.log

# Create log directory
RUN mkdir -p /app/log

# Entrypoint script to start cron daemon
ENTRYPOINT ["/entrypoint.sh"]
