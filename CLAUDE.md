# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LottoBot is a Docker-based automated Korean lottery (Lotto 6/45) purchase and winning number verification system. It uses the unofficial DH Lottery API ([dhapi](https://github.com/roeniss/dhlottery-api)) and sends notifications via Discord webhooks. The application runs on a cron schedule inside a Docker container.

## Core Architecture

### Two-Phase Operation Model

The application follows a sequential two-phase execution pattern:

1. **Phase 1 (Result Checking)**: Reads the most recent purchase log file (e.g., `lotto_log_1234.txt`), fetches winning numbers from the DH Lottery API, calculates prize matches, and appends results to the log file.

2. **Phase 2 (Purchase)**: Uses `dhapi` CLI to check account balance and purchase 5 lottery tickets (slots A-E, all auto-selection), then creates a new log file for the current round.

### Critical Components

**`lotto.py`**: Main orchestrator containing both phases. Key functions:
- `process_lotto_results()`: Phase 1 - parses log files, fetches winning numbers, checks prizes
- `check_buy_and_report_lotto()`: Phase 2 - executes dhapi commands, generates log files
- `get_lotto_round_and_target_date()`: Calculates round numbers based on first lottery date (2002-12-07)

**`entrypoint.sh`**: Container initialization script that:
- Converts environment variables (`DHLOTTERY_USERNAME`, `DHLOTTERY_PASSWORD`) to TOML credentials file at `/root/.dhapi/credentials`
- Dynamically generates `/tmp/lotto.crontab` with environment variables and schedule from `CRON_SCHEDULE`
- Installs crontab and cleans up temporary file
- Starts cron daemon and tails cron logs

### Configuration Flow

```
Project root: ./credentials → Docker env vars (DHLOTTERY_USERNAME, DHLOTTERY_PASSWORD)
                           ↓
Project root: ./.env → Docker env vars (DISCORD_WEBHOOK_URL, CRON_SCHEDULE)
                           ↓
             entrypoint.sh (container startup)
                           ↓
   /root/.dhapi/credentials (TOML format for dhapi)
   /tmp/lotto.crontab (unified crontab: env vars + schedule)
                           ↓
        crontab /tmp/lotto.crontab (install)
                           ↓
     /var/spool/cron/crontabs/root (installed crontab)
                           ↓
             cron job executes lotto.py
```

### Log File Structure

Log files use a structured text format with table-like rows:
```
=== 1234회 (2024-01-13 20:35:00 추첨)===
현재 시각: 2024-01-07 09:20:00
예치금: 5,000원
┌─────┬────────┬────┬────┬────┬────┬────┬────┐
│ A   │ 자동    │ 03 │ 12 │ 23 │ 34 │ 38 │ 45 │
│ B   │ 자동    │ 01 │ 15 │ 22 │ 29 │ 33 │ 41 │
...

=== 1234회(2024-01-13 추첨) 당첨 결과 ===
당첨 번호: [01, 12, 23, 29, 38, 41], (15)
[A, 자동, 03, 12, 23, 34, 38, 45, 3등!(5)]
[B, 자동, 01, 15, 22, 29, 33, 41, 2등!(5+)]
```

Parsing uses regex pattern matching to extract slot (A-E), mode (자동/반자동/수동), and six numbers.

## Development Commands

### Docker Operations
```bash
# Build and start container (required after code/config changes)
docker compose up -d --build

# View real-time container logs (cron output)
docker logs -f lotto-bot

# Manual test execution inside container
docker exec lotto-bot /usr/local/bin/python /app/lotto.py

# Access container shell for debugging
docker exec -it lotto-bot bash

# View cron execution logs inside container
docker exec lotto-bot cat /var/log/cron.log
```

### Local Development & Testing
```bash
# Monitor application logs from host
tail -f log/lotto_log_*.txt
tail -f log/lotto_error.log

# Test without Discord notifications
# Set DISCORD_BOT = False in lotto.py or unset DISCORD_WEBHOOK_URL in .env

# Verify credentials file generation
docker exec lotto-bot cat /root/.dhapi/credentials

# Verify installed crontab
docker exec lotto-bot crontab -l
```

### Cron Schedule Modification
Edit `CRON_SCHEDULE` in `.env` file and rebuild:
```bash
# Default: 20 9 * * 0 (Sunday 09:20 KST)
# Format: minute hour day-of-month month day-of-week
# Example: 0 21 * * 6 (Every Saturday 21:00 KST)
vim .env
docker compose up -d --build
```

## Important Constraints & Behaviors

### Purchase Limits
- Maximum 5 tickets (5,000 KRW) per round enforced by DH Lottery
- Account deposit must be managed manually on DH Lottery website
- Withdrawal only to registered bank account under user's name

### Error Handling Strategy
- Both phases execute independently with separate try-except blocks
- First execution (no previous log file) will log `FileNotFoundError` - this is expected behavior
- All errors append to `lotto_error.log` with timestamps
- Discord notifications sent for both successful operations and errors
- dhapi errors are parsed from stderr and logged with original error type

### Security Model
- No inbound ports exposed (container operates in isolation)
- Credentials never embedded in Docker image or logs
- Credentials stored in project root (`credentials`, `.env`) excluded via `.gitignore`
- Environment variables converted to TOML format at runtime by entrypoint.sh
- JSESSIONID-based authentication via dhapi (no permanent token storage)

### Timezone & Scheduling
- Container timezone: Asia/Seoul (KST)
- Lottery draw time: Every Saturday 20:35 KST
- Default execution: Sunday 09:20 KST (allows overnight for result publication)
- Round number calculation based on weeks since 2002-12-07

## Key Files Reference

- **`lotto.py`**: Main application logic (phases 1 & 2, round calculation, log parsing)
- **`entrypoint.sh`**: Credentials conversion, dynamic crontab generation, cron initialization
- **`Dockerfile`**: Python 3.11-slim base, cron installation, timezone setup
- **`docker-compose.yml`**: Volume mounts for logs, secret file loading
- **`requirements.txt`**: Python dependencies (dhapi only)
- **`credentials.example`**: Template file for DH Lottery credentials
- **`.env.example`**: Template file for environment variables (Discord webhook, cron schedule)

## Extending the Application

### Adding New Notification Channels
Follow the `send_message_to_discord()` pattern - check environment variable, add new function, call in both phases' try-except blocks.

### Modifying Purchase Strategy
Edit `dhapi buy-lotto645` command arguments in `check_buy_and_report_lotto()`. Empty strings = auto-selection. See dhapi documentation for manual/semi-auto number specification.

### Changing Log Format
Update regex pattern in both `process_lotto_results()` and `report_lotto_numbers()` to maintain consistency between Phase 1 and Phase 2 parsing.

### Environment Variable Changes
1. Add to template files (`credentials.example`, `.env.example`)
2. Update `entrypoint.sh` to handle new variables
3. Document in README.md setup section
4. If needed by cron job, add to `/tmp/lotto.crontab` generation in `entrypoint.sh`
