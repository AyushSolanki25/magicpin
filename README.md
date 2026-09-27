# Vera AI Assistant Bot — Submission README

## 1. Approach Overview

Our solution implements a **4-Context Deterministic Composition Engine** for Vera, magicpin's merchant AI assistant. It bridges slow-changing vertical domain knowledge (`CategoryContext`), live merchant snapshot & history (`MerchantContext`), event triggers (`TriggerContext`), and customer relationship records (`CustomerContext`).

### Core Architecture Highlights

1. **Stateful REST Endpoint Contract:** Implements all 5 required endpoints (`/v1/context`, `/v1/tick`, `/v1/reply`, `/v1/healthz`, `/v1/metadata`) using FastAPI.
2. **Context Versioning & Deduplication:** Idempotent context storage keyed on `(scope, context_id)` with version enforcement.
3. **Multi-Turn Intent & Auto-Reply Filter:** Tracks merchant replies, detects opt-outs/automated replies, and handles intent transitions.
4. **Compulsion Optimization:** Uses specificity, category fit, merchant fit, trigger relevance, and a single primary CTA.

---

## 2. Directory & Component Structure

```text
magicpin/
├── bot.py                  # FastAPI REST server
├── composer.py             # Core composition & reply engine
├── state.py                # Context store and conversation tracker
├── generate_submission.py  # Benchmark builder
├── submission.jsonl        # Benchmark outputs
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 3. Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the web server:

```bash
uvicorn bot:app --host 0.0.0.0 --port 8080
```

Open:

```text
http://localhost:8080/
http://localhost:8080/docs
http://localhost:8080/v1/healthz
```

You can also run `python bot.py`; it uses the `PORT` environment variable when available and falls back to port 8080 locally.

---

## 4. Deploy on Render

Create a **Web Service** using this GitHub repository and the `main` branch.

Use these settings:

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
uvicorn bot:app --host 0.0.0.0 --port $PORT
```

No hard-coded Render port is required. Render supplies `$PORT` automatically.

After deployment, verify:

```text
https://YOUR-SERVICE.onrender.com/
https://YOUR-SERVICE.onrender.com/v1/healthz
https://YOUR-SERVICE.onrender.com/docs
```

The root endpoint should return a small JSON response confirming that the web service is running.

## 5. Generate Submission JSONL

```bash
python generate_submission.py
```

## 6. API Endpoints

- `GET /` — service status
- `GET /v1/healthz` — health check
- `GET /v1/metadata` — team and project metadata
- `POST /v1/context` — push context
- `POST /v1/tick` — process available triggers
- `POST /v1/reply` — process a merchant reply
- `/docs` — interactive FastAPI Swagger documentation
