#!/bin/bash
set -e

echo "========================================="
echo "🎰 LottoBot Docker Container Starting..."
echo "========================================="
echo "Timezone: ${TZ}"
echo "Current time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Generate credentials file from environment variables
if [ -n "$DHLOTTERY_USERNAME" ] && [ -n "$DHLOTTERY_PASSWORD" ]; then
    echo "🔑 Configuring dhapi credentials..."
    mkdir -p /root/.dhapi
    cat > /root/.dhapi/credentials <<EOF
[default]
username = "$DHLOTTERY_USERNAME"
password = "$DHLOTTERY_PASSWORD"
EOF
    chmod 600 /root/.dhapi/credentials

    # Clear from environment
    unset DHLOTTERY_USERNAME
    unset DHLOTTERY_PASSWORD

    echo "✅ Credentials configured successfully"
elif [ ! -f /root/.dhapi/credentials ]; then
    echo "⚠️  WARNING: No credentials configured!"
    echo "Please set DHLOTTERY_USERNAME and DHLOTTERY_PASSWORD in credentials file"
    exit 1
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
