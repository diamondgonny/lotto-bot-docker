# Repository Guidelines

## Project Structure & Module Organization
- `lotto.py` orchestrates authentication, result checking, and purchases; keep core logic modular when adding helpers near the top-level workflow.
- `docker/` contains deployment docs and shares context for container usage; mirror updates between `Dockerfile`, `entrypoint.sh`, and the docs.
- `.credentials.example` and `.env.example` provide templates for credentials and environment variables (including `CRON_SCHEDULE`); never commit real credentials.
- `entrypoint.sh` dynamically generates and installs the crontab with environment variables and schedule; modify when changing automation or adding cron-accessible environment variables.
- Logs populate `log/` at runtime; keep files writable but ignored by git.

## Build, Test, and Development Commands
**Note**: This project is Docker-only. Virtual environment (venv) setup is not supported.

- `docker compose up -d --build` builds and launches the scheduled bot container.
- `docker logs -f lotto-bot` monitors runtime output and cron execution.
- `docker exec lotto-bot /usr/local/bin/python /app/lotto.py` runs a manual test inside the container.
- `tail -f log/lotto_log_*.txt` monitors lotto logs from the host.
- Set empty `DISCORD_BOT` in `lotto.py` for testing without notifications.

## Coding Style & Naming Conventions
Follow Python 3.7+ standards with 4-space indentation. Use `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants (`DISCORD_BOT`, `KST`). Keep side-effectful calls in functions and leave the module import section tidy. Prefer explicit string formatting (`f"...`) and reusable helpers when parsing logs.

## Testing Guidelines
Automated tests are not yet in place; validate changes by running `python lotto.py` against a copied log fixture in `log/`. Confirm cron compatibility by rebuilding the container and inspecting `/var/log/cron.log` inside Docker. Document manual steps for new flows in PR descriptions.

## Commit & Pull Request Guidelines
Recent history uses conventional prefixes (`docs:`, `fix:`). Keep messages imperative and scoped to one change (`feat: add lotto retry strategy`). PRs should detail the scenario, configuration touched (`.credentials`, `cron`), manual verification steps, and attach screenshots for Discord-facing changes. Link related issues or discussions when available.

## Security & Configuration Tips
**Docker Setup**: Secrets live in project root as `.credentials` (environment variable format: `DHLOTTERY_USERNAME`, `DHLOTTERY_PASSWORD`) and `.env` (Discord webhook, cron schedule), loaded via `docker-compose.yml` env_file directive at container startup. Both files are excluded from version control via `.gitignore`. At container startup, `entrypoint.sh` sets up log directory permissions (`/app/log` with `700` for lottobot-only access) for the non-root lottobot user (UID/GID 1000), converts credentials to TOML format at `/home/lottobot/.dhapi/credentials` (owned by lottobot:lottobot with `600` permissions), then dynamically generates `/tmp/lotto.crontab` with environment variables (including masked `DISCORD_WEBHOOK_URL`) and the schedule from `CRON_SCHEDULE`, installs it via `crontab` command, and cleans up the temporary file. The cron daemon runs as root but executes Python scripts via `/usr/sbin/runuser -u lottobot` for privilege separation. Reference `.credentials.example` and `.env.example` for scaffolding and set file permissions to 600 if needed. When extending HTTP calls, reuse the existing session handling in `dhapi` and mention any new environment variables in both templates and docs. If a new variable needs to be accessible to the cron job, add it to the crontab generation section in `entrypoint.sh`. Audit logs before sharing them externally—they may contain round numbers or purchase metadata.
