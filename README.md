# HR Automation Multi-Agent System

AI agents that automate three HR workflows: resume screening, new-hire onboarding and policy Q&A.
Each agent is a standalone FastAPI service backed by Google Gemini and lives in its own folder,
with its own dependencies, configuration and documentation.

| Service | Folder | What it does | Default address |
|---|---|---|---|
| **TalentScout** | [`talent_scout/`](talent_scout/API_README.md) | OCRs resumes and job descriptions, scores candidates with a deterministic rubric and generates interview questions | `uvicorn` on `127.0.0.1:8000` (use `--port 8002` alongside PolicyBot) |
| **Onboarder** | [`Onboarder/`](Onboarder/README.md) | Runs pre-boarding, day-1 setup and integration phases through specialised agents, tracked in SQLite | `127.0.0.1:8050` |
| **PolicyBot** | [`agents/policy_bot/`](agents/policy_bot/README.md) | Answers policy questions with RAG over your documents (Chroma + sentence-transformers) | API `127.0.0.1:8000`, web UI `127.0.0.1:8001` |

## Repository layout

```plaintext
.
├── talent_scout/          # Resume screening API (FastAPI, Gemini, Tesseract OCR)
│   ├── api/ services/ utils/ schemas/
│   ├── data/jobs/         # Uploaded JDs and resumes (local only, git-ignored)
│   └── tests/
├── Onboarder/             # Onboarding orchestration API (FastAPI, Gemini, SQLite)
│   ├── onboarder/         # Agents, orchestrator, database and tools
│   ├── generated_documents/  # Contracts and forms (local only, git-ignored)
│   └── tests/
└── agents/policy_bot/     # Policy Q&A (FastAPI, LangChain, Chroma, Gemini)
    ├── knowledge_base/documents/  # Your policy files
    └── tests/
```

## Getting started

Prerequisites: Python 3.10+ (PolicyBot's LangChain dependencies need it; the other two run on 3.9+)
and a [Gemini API key](https://aistudio.google.com/app/apikey). TalentScout also needs
Poppler and Tesseract (`brew install poppler tesseract` on macOS).

Use a separate virtual environment per service, since their dependencies differ:

```sh
git clone https://github.com/Devansh-236/B2B_SAAS.git
cd B2B_SAAS/<service-folder>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then configure and start the service:

- **TalentScout**: create `talent_scout/.env` with `GEMINI_API_KEY=...`, then
  `uvicorn main:app --port 8002`.
- **Onboarder**: `cp env.example .env`, set `GEMINI_API_KEY`, then `python3 main.py`
  (or `./start_server.sh`).
- **PolicyBot**: `cp env_template.txt .env`, set `GOOGLE_API_KEY`, add documents to
  `knowledge_base/documents/`, run `python setup_knowledge_base.py`, then
  `python web_interface.py` (UI + API) or `python api_server.py` (API only).

Each service has interactive API docs at `/docs`.

## Security notes

- All services bind to `127.0.0.1` by default. Before exposing Onboarder or PolicyBot on a
  network, set their API key (`ONBOARDER_API_KEY`, `POLICY_BOT_API_KEY`) and CORS origins.
  TalentScout has no authentication yet, so keep it local or put it behind an authenticating proxy.
- Uploaded resumes, candidate records and generated onboarding documents contain personal
  data. They are git-ignored; keep it that way.
- `.env` files are git-ignored. Never commit API keys.

## Running tests

All suites run offline: Gemini, OCR and embeddings are mocked.

```sh
cd talent_scout && pytest                  # API, validation and scoring tests
cd agents/policy_bot && pytest             # RAG pipeline and API tests
cd Onboarder && python3 tests/e2e_check.py # full onboarding run end to end
```

## Contributing

1. Fork the repository and create a branch (`git checkout -b feature/your-feature-name`).
2. Make your changes and run the relevant test suite.
3. Open a pull request.
