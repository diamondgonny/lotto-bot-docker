# Repository Guidelines

## Project Structure & Module Organization
- `lotto.py` orchestrates authentication, result checking, and purchases; keep core logic modular when adding helpers near the top-level workflow.
- `docker/` contains deployment docs and shares context for container usage; mirror updates between `Dockerfile`, `entrypoint.sh`, and the docs.
- `.secrets-template/` hosts TOML and env templates; never commit real credentials.
- `crontab` and `entrypoint.sh` define the scheduled run inside the container; adjust both when changing automation.
- Logs populate `log/` at runtime; keep files writable but ignored by git.

## Build, Test, and Development Commands
**Note**: This project is Docker-only. Virtual environment (venv) setup is not supported.

- `docker compose up -d --build` builds and launches the scheduled bot container.
- `docker logs -f lottobot` monitors runtime output and cron execution.
- `docker exec lottobot /usr/local/bin/python /app/lotto.py` runs a manual test inside the container.
- `tail -f ~/docker/lottobot/logs/lotto_log_*.txt` monitors lotto logs from the host.
- Set empty `DISCORD_BOT` in `lotto.py` for testing without notifications.

## Coding Style & Naming Conventions
Follow Python 3.7+ standards with 4-space indentation. Use `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants (`DISCORD_BOT`, `KST`). Keep side-effectful calls in functions and leave the module import section tidy. Prefer explicit string formatting (`f"...`) and reusable helpers when parsing logs.

## Testing Guidelines
Automated tests are not yet in place; validate changes by running `python lotto.py` against a copied log fixture in `log/`. Confirm cron compatibility by rebuilding the container and inspecting `/var/log/cron.log` inside Docker. Document manual steps for new flows in PR descriptions.

## Commit & Pull Request Guidelines
Recent history uses conventional prefixes (`docs:`, `fix:`). Keep messages imperative and scoped to one change (`feat: add lotto retry strategy`). PRs should detail the scenario, configuration touched (`credentials`, `cron`), manual verification steps, and attach screenshots for Discord-facing changes. Link related issues or discussions when available.

## Security & Configuration Tips
**Docker Setup**: Secrets live in `~/.secrets/lottobot/credentials` (environment variable format: `DHLOTTERY_USERNAME`, `DHLOTTERY_PASSWORD`) and `~/.secrets/lottobot/.env` (Discord webhook), loaded via `docker-compose.yml` env_file directive at container startup. Credentials are converted to TOML format by `entrypoint.sh`, and the `DISCORD_WEBHOOK_URL` environment variable is written to `/etc/lotto-cron` for cron job access. Reference `.secrets-template/` for scaffolding and set file permissions to 600 for files and 700 for the directory. When extending HTTP calls, reuse the existing session handling in `dhapi` and mention any new environment variables in both templates and docs. Audit logs before sharing them externally—they may contain round numbers or purchase metadata.
