# ride-matcher-service

Concurrent aiohttp API server + Telegram bot service.

## Components

* `ApiServerService` (aiohttp) with middleware + `/healthz` (includes uptime & request_id) and structured request
  logging.
* `TelegramBotService` wraps `python-telegram-bot` with clean async lifecycle (only starts if `TELEGRAM_BOT_TOKEN`
  present).

## Running

Set environment variables as needed (create a `.env` file for local dev):

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
LOG_LEVEL=DEBUG
HTTP_PORT=8000
```

Start the service:

```bash
python -m main
```

Health check:

```bash
curl http://localhost:8000/healthz
```

Graceful shutdown via Ctrl+C (SIGINT) or SIGTERM stops bot then API server.

## Structure

* `main.py` orchestrates startup & shutdown.
* `app/api/` modular API server: `service.py`, `routes/health.py`, `middleware/logging.py`.
* `app/api_server.py` deprecated shim.
* `app/telegram/` modular bot: `service.py`, `config.py`, `handlers/`.
* `app/telegram_bot.py` deprecated shim.
* `config/settings.py` Pydantic settings.
* `config/log_setup.py` basic logging config.

## Development

Install requirements:

```bash
pip install -r requirements.txt
```

Run with hot reload (optional suggestion – e.g. using `watchfiles`): add `watchfiles` to requirements and run:

```bash
watchfiles 'python main.py'
```

## Future ideas

* Add structured logging (JSON) for production.
* Add tests for handlers & lifecycle.
* Add more API endpoints.

# Ride Matcher Service

A service for matching ride requests with train schedules using the Yandex Schedules API.

## Configuration

This project uses Pydantic BaseSettings for configuration management.

### Quick Start

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API key:

   ```bash
   YANDEX_SCHEDULES_API_KEY=your_api_key_here
   ```

3. Use the config in your code:

   ```python
   from config import get_config

   config = get_config()
   api_key = config.yandex_schedules_api_key
   timezone = config.result_timezone
   ```

### Environment Variables

* `YANDEX_SCHEDULES_API_KEY` (required): Your Yandex Schedules API key
* `RESULT_TIMEZONE` (optional): Timezone for results (default: "Europe/Moscow")
* `ENVIRONMENT` (optional): Environment name (default: "development")
* `LOG_LEVEL` (optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) default: INFO
* `HTTP_HOST` / `HTTP_PORT` (optional): Host/port for health & future HTTP endpoints (defaults: 0.0.0.0:8000)
* `TELEGRAM_BOT_TOKEN` (optional): If provided, the Telegram bot will start; omitted disables bot
* `POSTGRES_URL` / `DATABASE_URL` (required for persistence): PostgreSQL connection string (e.g. `postgresql://user:pass@host:5432/dbname`). If it starts with `postgresql://`, the service automatically normalizes it to `postgres://` for Tortoise ORM compatibility. Legacy `POSTGRESQL_URI` is still accepted for backward compatibility.
* `REDIS_URL` (optional but preferred): Full Redis connection URL (e.g. `redis://default:password@host:6379/0`). When set, it takes precedence over the host/port fields below. Legacy `REDIS_URI` remains supported.
* `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_USERNAME`, `REDIS_PASSWORD` (optional): Fallback Redis parameters used only when `REDIS_URL` is not provided.

### Running (HTTP health + Telegram bot)

Run both services with a single command:

```bash
python main.py
```

The aiohttp health endpoint will be available at: `http://localhost:8000/healthz` (adjust port via `HTTP_PORT`).

If `TELEGRAM_BOT_TOKEN` is set in the environment, the bot will start polling concurrently; otherwise it is skipped.

Graceful shutdown: press Ctrl+C (SIGINT) and both the HTTP server and the bot polling loop will stop cleanly.

On startup you'll see a single consolidated line summarizing runtime config, e.g.:

```text
2025-09-18 20:00:00,123 | INFO | __main__ | Starting service | env=development | timezone=Europe/Moscow | log_level=DEBUG | http=0.0.0.0:8000 | bot=enabled
```

### Architecture

The entrypoint (`main.py`) is intentionally thin: it configures logging, logs environment context, and delegates
lifecycle management to `ServiceManager` (`app/runtime.py`). This keeps startup/shutdown logic isolated from business
code.

### Example `.env` snippet

```dotenv
ENVIRONMENT=development
LOG_LEVEL=DEBUG
HTTP_PORT=8080
TELEGRAM_BOT_TOKEN=123456:ABC-DEF_your_token_here
```

Remove or comment `TELEGRAM_BOT_TOKEN` to disable the bot locally.
