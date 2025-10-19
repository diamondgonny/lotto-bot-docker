#!/bin/bash
set -e

echo "========================================="
echo "🎰 LottoBot Docker Container Starting..."
echo "========================================="
echo "Timezone: ${TZ}"
echo "Current time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Check if credentials file exists
if [ ! -f /root/.dhapi/credentials ]; then
    echo "⚠️  WARNING: /root/.dhapi/credentials not found!"
    echo "Please mount credentials file to /root/.dhapi/credentials"
fi

# Check if .env file exists
if [ ! -f /app/.env ]; then
    echo "⚠️  WARNING: /app/.env not found!"
    echo "Discord notifications will be disabled."
fi

echo ""
echo "📅 Cron schedule: Every Sunday at 09:20 AM KST"
echo "📁 Log directory: /app/log"
echo ""

# Start cron daemon in foreground
echo "🚀 Starting cron daemon..."
cron

# Keep container alive and show cron logs
echo "✅ Container is ready. Monitoring cron logs..."
echo "========================================="
echo ""

# Tail cron log to keep container running and show output
tail -f /var/log/cron.log
