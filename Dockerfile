# LottoBot Docker Image
FROM python:3.11-slim

# Set timezone to KST (Asia/Seoul)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install cron, git and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for running application
RUN groupadd -g 1000 lottobot && \
    useradd -u 1000 -g lottobot -m -s /bin/bash lottobot

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY lotto.py .
COPY entrypoint.sh /entrypoint.sh

# Set proper permissions
RUN chmod +x /entrypoint.sh && \
    touch /var/log/cron.log && \
    chmod 644 /var/log/cron.log

# Create log directory
RUN mkdir -p /app/log

# Set ownership for application directories
RUN chown -R lottobot:lottobot /app

# Entrypoint script to start cron daemon
ENTRYPOINT ["/entrypoint.sh"]
