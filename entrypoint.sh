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
    echo "✅ Credentials configured successfully"
elif [ ! -f /root/.dhapi/credentials ]; then
    echo "⚠️  WARNING: No credentials configured!"
    echo "Please set DHLOTTERY_USERNAME and DHLOTTERY_PASSWORD in credentials file"
    exit 1
fi

echo ""

# Setup cron schedule from environment variable
CRON_SCHEDULE="${CRON_SCHEDULE:-20 9 * * 0}"
echo "📅 Configuring cron schedule: ${CRON_SCHEDULE}"

# Validate CRON_SCHEDULE format (5 fields)
if [[ ! "$CRON_SCHEDULE" =~ ^([^[:space:]]+[[:space:]]+){4}[^[:space:]]+$ ]]; then
    echo "❌ ERROR: Invalid CRON_SCHEDULE format: ${CRON_SCHEDULE}"
    echo "   Expected format: 'minute hour day month weekday'"
    echo "   Example: '20 9 * * 0' (Sunday 09:20)"
    exit 1
fi

# Basic range validation for simple numeric values
IFS=' ' read -ra FIELDS <<< "$CRON_SCHEDULE"
# Minute (0-59)
if [[ "${FIELDS[0]}" =~ ^[0-9]+$ ]] && (( ${FIELDS[0]} > 59 )); then
    echo "⚠️  WARNING: Minute value ${FIELDS[0]} is out of range (0-59)"
fi
# Hour (0-23)
if [[ "${FIELDS[1]}" =~ ^[0-9]+$ ]] && (( ${FIELDS[1]} > 23 )); then
    echo "⚠️  WARNING: Hour value ${FIELDS[1]} is out of range (0-23)"
fi
# Day (1-31)
if [[ "${FIELDS[2]}" =~ ^[0-9]+$ ]] && (( ${FIELDS[2]} < 1 || ${FIELDS[2]} > 31 )); then
    echo "⚠️  WARNING: Day value ${FIELDS[2]} is out of range (1-31)"
fi
# Month (1-12)
if [[ "${FIELDS[3]}" =~ ^[0-9]+$ ]] && (( ${FIELDS[3]} < 1 || ${FIELDS[3]} > 12 )); then
    echo "⚠️  WARNING: Month value ${FIELDS[3]} is out of range (1-12)"
fi
# Weekday (0-7)
if [[ "${FIELDS[4]}" =~ ^[0-9]+$ ]] && (( ${FIELDS[4]} > 7 )); then
    echo "⚠️  WARNING: Weekday value ${FIELDS[4]} is out of range (0-7)"
fi

# Validate DISCORD_WEBHOOK_URL format if provided
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    if [[ ! "$DISCORD_WEBHOOK_URL" =~ ^https://discord(app)?.com/api/webhooks/ ]]; then
        echo "⚠️  WARNING: DISCORD_WEBHOOK_URL may be invalid"
        echo "   Expected format: https://discord.com/api/webhooks/..."
    fi
fi

# Create unified crontab with environment variables and schedule
cat > /tmp/lotto.crontab <<EOF
# Environment variables for cron job
DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}

# LottoBot schedule: Check results and purchase new tickets
${CRON_SCHEDULE} cd /app && /usr/local/bin/python /app/lotto.py >> /var/log/cron.log 2>&1
EOF

# Install crontab
crontab /tmp/lotto.crontab

# Verify installation and display installed schedule
if crontab -l > /dev/null 2>&1; then
    echo "✅ Crontab installed successfully"
    echo ""
    echo "Installed schedule:"
    echo "---"
    crontab -l | grep -v "^#" | grep -v "^$"
    echo "---"
    echo ""
    rm -f /tmp/lotto.crontab
    echo "✅ Temporary file cleaned up"
else
    echo "❌ Crontab installation failed"
    exit 1
fi

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
