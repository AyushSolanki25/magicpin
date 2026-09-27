# Vera AI Assistant Bot — Submission README

## 1. Approach Overview

Our solution implements a **4-Context Deterministic Composition Engine** for Vera, magicpin's merchant AI assistant. It bridges slow-changing vertical domain knowledge (`CategoryContext`), live merchant snapshot & history (`MerchantContext`), event triggers (`TriggerContext`), and customer relationship records (`CustomerContext`).

### Core Architecture Highlights

1. **Stateful REST Endpoint Contract**: Implements all 5 required endpoints (`/v1/context`, `/v1/tick`, `/v1/reply`, `/v1/healthz`, `/v1/metadata`) using FastAPI.
2. **Context Versioning & Deduplication**: Idempotent context storage keyed on `(scope, context_id)` with version enforcement to guarantee state consistency across ticks.
3. **Multi-Turn Intent & Auto-Reply Filter**:
   - **Auto-Reply Detection**: Tracks merchant reply repetitions and canned WhatsApp Business signatures (`"Thank you for contacting..."`, `"automated message"`). Backs off or exits gracefully to eliminate turn pollution.
   - **Intent Transition Handler**: When a merchant signals commitment (`"yes"`, `"do it"`, `"go ahead"`, `"update my profile"`), Vera switches from qualifying mode to immediate execution reporting.
   - **Hostile/Opt-Out Exit**: Respects merchant opt-outs (`"stop"`, `"spam"`) with immediate polite closure and zero-spam enforcement.
4. **5-Dimension Compulsion Optimization**:
   - **Specificity**: Anchors on verifiable numbers (views, calls, CTR vs peer medians, prices like `₹299`, and research citations like `JIDA Oct 2026 p.14`).
   - **Category Fit**: Strict voice matching (clinical/peer for dentists, warm for salons, practical for pharmacies, operator-tone for restaurants). Taboo terms like `"guaranteed"` are strictly avoided.
   - **Merchant Fit**: Personalizes to locality, owner name, active catalog offers, and language preferences (`hi-en mix` Hindi-English code-mix).
   - **Trigger Relevance**: Explicitly connects *why now* to the trigger payload.
   - **Single Primary CTA**: Ensures every outbound ends in a single low-friction CTA (binary YES/NO or open-ended single question).

---

## 2. Directory & Component Structure

```
vera_bot/
├── bot.py                  # FastAPI REST server for judge harness integration
├── composer.py             # Core 4-Context composition & reply engine
├── state.py                # Thread-safe context store, version manager & conversation tracker
├── generate_submission.py  # Benchmark builder for submission.jsonl (30 test pairs)
├── submission.jsonl        # Outputs for 30 canonical test pairs
└── README.md               # Architecture documentation & execution guide
```

---

## 3. How to Run & Verify

### Step 1: Generate submission JSONL
```bash
python vera_bot/generate_submission.py
```

### Step 2: Start the Vera Bot REST Server
```bash
python vera_bot/bot.py
# Server starts at http://localhost:8080
```

### Step 3: Run the Official Judge Simulator
In another terminal:
```bash
python judge_simulator.py
```
This runs warmup, tick tests, auto-reply detection, intent transitions, and hostile scenario evaluations.
