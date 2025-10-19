# Repository Guidelines

## Project Structure & Module Organization
- `lotto.py` orchestrates authentication, result checking, and purchases; keep core logic modular when adding helpers near the top-level workflow.
- `docker/` contains deployment docs and shares context for container usage; mirror updates between `Dockerfile`, `entrypoint.sh`, and the docs.
- `.secrets-template/` hosts TOML and env templates; never commit real credentials.
- `crontab` and `entrypoint.sh` define the scheduled run inside the container; adjust both when changing automation.
- Logs populate `log/` at runtime; keep files writable but ignored by git.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` creates the local virtualenv expected by `lotto.py` when `USE_VENV=True`.
- `pip install -r requirements.txt` installs `dhapi` and `python-dotenv`.
- `python lotto.py` executes a single run (checks last log and purchases next round); pass `DISCORD_BOT=False` in code for offline debugging.
- `docker-compose up -d --build` builds and launches the scheduled bot; tail with `docker logs -f lottobot` for runtime inspection.

## Coding Style & Naming Conventions
Follow Python 3.7+ standards with 4-space indentation. Use `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module constants (`DISCORD_BOT`, `KST`). Keep side-effectful calls in functions and leave the module import section tidy. Prefer explicit string formatting (`f"...`) and reusable helpers when parsing logs.

## Testing Guidelines
Automated tests are not yet in place; validate changes by running `python lotto.py` against a copied log fixture in `log/`. Confirm cron compatibility by rebuilding the container and inspecting `/var/log/cron.log` inside Docker. Document manual steps for new flows in PR descriptions.

## Commit & Pull Request Guidelines
Recent history uses conventional prefixes (`docs:`, `fix:`). Keep messages imperative and scoped to one change (`feat: add lotto retry strategy`). PRs should detail the scenario, configuration touched (`.env`, `cron`), manual verification steps, and attach screenshots for Discord-facing changes. Link related issues or discussions when available.

## Security & Configuration Tips
Secrets live in `~/.dhapi/credentials` and project `.env`; reference `.secrets-template/` for scaffolding and avoid hardcoding tokens. When extending HTTP calls, reuse the existing session handling in `dhapi` and mention any new environment variables in both templates and docs. Audit logs before sharing them externally—they may contain round numbers or purchase metadata.
