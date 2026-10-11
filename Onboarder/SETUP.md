# 🚀 Onboarder Setup Guide

## Quick Start

```bash
# 1. Install dependencies
python3 -m pip install -r requirements.txt

# 2. Configure environment
cp env.example .env
# Edit .env and set GEMINI_API_KEY

# 3. Start the API server (http://127.0.0.1:8050 by default)
python3 main.py
```

Or use the startup script, which checks `.env`, installs dependencies, initializes the database and starts the server:

```bash
./start_server.sh
```

The script stops with an error if `.env` is missing or `GEMINI_API_KEY` is still the placeholder value.

## `setup.py` Commands

`setup.py` initializes the SQLite database and can run a full onboarding demo without the API server.

| Option | Description |
|--------|-------------|
| `--init` | Initialize the SQLite database |
| `--status` | Show onboarding counts by status/phase and recent records |
| `--demo` | Run a full onboarding for a demo employee through the `AgentOrchestrator` (calls Gemini) |
| `--migrate` | Migrate records from a legacy JSON state file |
| `--json-file PATH` | JSON file to migrate from (default: `onboarding_state/onboarding_states.json`) |
| `--db-path PATH` | Database file to use for all of the above (default: `ONBOARDER_DB_PATH` or `onboarding.db` in the project directory) |

With no options, `setup.py` initializes the database, shows the status and runs the demo.

```bash
python3 setup.py --init
python3 setup.py --status
python3 setup.py --demo
python3 setup.py --status --db-path /tmp/onboarding.db
```

## Configuration

All settings are read from environment variables (or `.env`). See `env.example`.

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Google Gemini API key |
| `ONBOARDER_HOST` | `127.0.0.1` | Interface the server binds to |
| `ONBOARDER_PORT` | `8050` | Server port |
| `ONBOARDER_RELOAD` | `false` | Enable uvicorn auto-reload (development only) |
| `ONBOARDER_CORS_ORIGINS` | localhost:3000 and localhost:8050 origins | Comma-separated browser origins allowed by CORS |
| `ONBOARDER_API_KEY` | (unset) | If set, data endpoints require the `X-API-Key` header |
| `ONBOARDER_DB_PATH` | `onboarding.db` | SQLite database path (relative paths are resolved against the Onboarder directory) |
| `DOCUMENT_OUTPUT_DIR` | `generated_documents` | Directory for generated documents (relative to the Onboarder directory) |

If you bind to anything other than `127.0.0.1`, set `ONBOARDER_API_KEY`.

## Troubleshooting

### Port already in use
```bash
lsof -i :8050
# or run on another port
ONBOARDER_PORT=8051 python3 main.py
```

### Onboarding stuck in `IN_PROGRESS`
If the server was stopped while an onboarding was running, reset it and start again:

```bash
curl -X POST http://127.0.0.1:8050/onboarding/<employee_id>/reset
curl -X POST http://127.0.0.1:8050/onboarding/<employee_id>/start
```

### Reset the database
```bash
python3 reset_database.py
```
