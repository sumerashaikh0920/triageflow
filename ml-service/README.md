# TriageFlow ML Service

A standalone ML microservice for **TriageFlow**, a customer-support ticket
triage platform. It classifies incoming tickets, recommends a routing
team, and closes the loop with a human-feedback-driven retraining
pipeline — designed to sit next to an existing FastAPI/PostgreSQL backend
as an independently deployable service.

```
Ticket subject/body
        │
        ▼
 POST /predict ──► category / subcategory / urgency / sentiment
        │           + confidence + routing_team + reason
        ▼
  Agent reviews, optionally corrects labels
        │
        ▼
   POST /feedback ──► ticket_feedback table
        │
        ▼
  QA approves correction ──► POST /feedback/{id}/review
        │
        ▼
  Retraining trigger (weekly OR N approved corrections)
        │
        ▼
  validate → snapshot → train → evaluate → compare → register
        │
        ▼
  Human approves candidate ──► POST /models/{version}/approve
        │
        ▼
  Human deploys candidate ──► POST /models/{version}/activate
```

---

## Contents

- [Quick start](#quick-start)
- [Architecture](#architecture)
- [API reference](#api-reference)
- [Data format](#data-format)
- [Local inference](#local-inference)
- [Training](#training)
- [Evaluation](#evaluation)
- [Feedback ingestion](#feedback-ingestion)
- [Retraining pipeline](#retraining-pipeline)
- [Model versioning & registry](#model-versioning--registry)
- [Integrating with the main FastAPI backend](#integrating-with-the-main-fastapi-backend)
- [Tests](#tests)
- [Docker](#docker)
- [Design notes & known simplifications](#design-notes--known-simplifications)

---

## Quick start

### Option A — Docker (recommended)

```bash
docker compose up --build
```

This starts Postgres + the ML service. On first boot the service
auto-bootstraps: it trains a lightweight TF-IDF + LogisticRegression
baseline on the bundled example dataset (`data/example_tickets.csv`),
registers it, auto-approves it, and activates it — so `/predict` works
immediately with **no manual training step**.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"subject": "Cannot log in", "body": "My password reset link is broken and I am locked out, urgent."}'
```

### Option B — Local Python

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # defaults to a local SQLite file, no Postgres needed
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

---

## Architecture

```
app/
├── main.py                  FastAPI app: /predict, /health, feedback & registry admin routes
├── config.py                Settings (env-driven; SQLite fallback for zero-setup local dev)
├── schemas.py                Pydantic request/response models
├── labels.py                  Shared label taxonomy (category/subcategory/urgency/sentiment)
├── db.py / models_db.py         SQLAlchemy engine + ORM (ticket_feedback, model_registry)
│
├── inference/
│   ├── predictor.py           Live prediction service: active model → heuristic fallback
│   ├── heuristic.py            Zero-dependency keyword classifier (ultimate fallback)
│   ├── transformer_predictor.py Adapter: fine-tuned transformer → common predict() interface
│   └── routing.py + routing_rules.yaml   Configurable category+urgency → team routing
│
├── training/
│   ├── dataset.py              Load/validate/split labeled ticket data
│   ├── sklearn_baseline.py     TF-IDF + LogisticRegression (default, CPU-fast)
│   ├── transformer_model.py    Multi-task DistilBERT (shared encoder, 4 heads)
│   ├── train.py                CLI + library entry points for both trainers
│   └── evaluate.py             Accuracy / weighted F1 / per-label F1 / confusion matrix / latency
│
├── feedback/
│   ├── ingest.py                Record & query agent/QA corrections
│   └── export.py                Validate + snapshot approved corrections → versioned dataset
│
├── registry/
│   ├── model_registry.py        Rollback-compatible model lifecycle (register/approve/activate/rollback)
│   └── bootstrap.py             First-run auto-bootstrap of the default baseline model
│
└── retrain/
    ├── scheduler.py              Weekly / min-corrections trigger evaluation
    └── pipeline.py                8-stage retraining orchestration
```

---

## API reference

| Method | Path                        | Purpose                                              |
|--------|-----------------------------|-------------------------------------------------------|
| POST   | `/predict`                  | Classify a ticket, get routing + explanation           |
| GET    | `/health`                   | Liveness/readiness + active model info                 |
| POST   | `/feedback`                 | Record an agent/QA correction                            |
| GET    | `/feedback?review_status=`  | List feedback (optionally filtered)                       |
| POST   | `/feedback/{id}/review`     | Approve/reject a correction                                 |
| GET    | `/models`                   | List all registry entries (full history)                     |
| GET    | `/models/active`            | Current active model's metadata                                |
| POST   | `/models/{version}/approve` | Approve a candidate (blocked if it regressed)                    |
| POST   | `/models/{version}/activate`| Deploy an approved, non-regressed model                            |
| POST   | `/models/{version}/rollback`| Reactivate a previously retired model                                |
| POST   | `/retrain/check`             | Evaluate triggers without training anything                            |
| POST   | `/retrain/run`               | Run the retraining pipeline (registers a candidate; never auto-deploys)  |

### `POST /predict` example response

```json
{
  "ticket_id": "T-4471",
  "category": "technical",
  "subcategory": "technical_outage",
  "urgency": "critical",
  "sentiment": "negative",
  "confidence": {
    "category": 0.94,
    "subcategory": 0.81,
    "urgency": 0.88,
    "sentiment": 0.77
  },
  "overall_confidence": 0.85,
  "routing_team": "incident_response",
  "reason": "Predicted by model 'sklearn-baseline-20260810-091203' (sklearn_baseline); category driven by strongest lexical/semantic signal, urgency by escalation language, sentiment by tone. Routed to 'incident_response': Matched rule category='technical' urgency='critical'.",
  "model_version": "sklearn-baseline-20260810-091203",
  "model_type": "sklearn_baseline",
  "model_timestamp": "2026-08-10T09:12:03Z",
  "predicted_at": "2026-08-11T10:02:41Z",
  "latency_ms": 4.213
}
```

---

## Data format

Training data (`data/example_tickets.csv` and feedback exports) is a flat
CSV with one row per labeled ticket:

| column        | type   | notes                                              |
|----------------|--------|-----------------------------------------------------|
| `ticket_id`    | string | unique id                                             |
| `subject`      | string | ticket subject line                                     |
| `body`         | string | ticket body text                                          |
| `category`     | enum   | see `app/labels.py::CATEGORIES`                             |
| `subcategory`  | enum   | see `app/labels.py::SUBCATEGORIES` (must match its parent category) |
| `urgency`      | enum   | `low` \| `medium` \| `high` \| `critical`                     |
| `sentiment`    | enum   | `negative` \| `neutral` \| `positive`                            |
| `created_at`   | date   | used to compute the dataset's date range for registry metadata     |

`app/training/dataset.py::validate_labels()` rejects any row with an
out-of-taxonomy label before it's allowed into training.

---

## Local inference

```bash
uvicorn app.main:app --reload
curl -X POST localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"subject": "Refund please", "body": "I was charged twice this month, please refund me."}'
```

If no model is registered yet (fresh DB, bootstrap disabled/failed) or the
active artifact fails to load for any reason, `/predict` still returns a
full, structurally valid response using the pure keyword heuristic in
`app/inference/heuristic.py` — the `reason` field and `model_type:
"heuristic_fallback"` make this explicit rather than silently degrading.

---

## Training

Two trainers share the same dataset/label interfaces:

```bash
# Fast default: TF-IDF + LogisticRegression, one pipeline per label field.
python -m app.training.train --mode baseline

# Fine-tune a multi-task transformer (shared DistilBERT encoder, 4 heads).
python -m app.training.train --mode transformer --epochs 3
```

Both write a self-contained, versioned artifact directory under
`models/<version>/` (e.g. `models/sklearn-baseline-20260810-091203/` or
`models/transformer-20260810-091530/`) containing the trained
weights/pipelines, tokenizer (transformer only), label mappings, and a
`training_manifest.json`.

The transformer trainer is a plain PyTorch loop (not `Trainer`) so a
single shared encoder can feed four independent classification heads
(category/subcategory/urgency/sentiment) with one loss term per head. It
runs fine on CPU for the bundled example dataset; for real-scale data, run
it on a GPU box and point `--dataset` at your full export.

---

## Evaluation

```bash
python -m app.training.evaluate \
  --artifact-dir models/sklearn-baseline-20260810-091203 \
  --model-type sklearn_baseline \
  --out eval_report.json
```

Produces, per label field, and overall:

- accuracy
- weighted F1
- per-label (per-class) F1
- confusion matrix
- prediction latency (mean / p50 / p95 / max, ms)
- confidence distribution (mean / min / max /5-bucket histogram)

`app/training/evaluate.py::evaluate_predictions()` is a pure function over
already-computed predictions, kept separate from model loading so metric
math is unit-tested independently of any model artifact (see
`tests/test_metrics.py`).

---

## Feedback ingestion

Agents/QA reviewers submit corrections via `POST /feedback`:

```json
{
  "ticket_id": "T-4471",
  "ticket_text": "My password reset link is broken...",
  "original_category": "account",
  "original_subcategory": "account_login",
  "original_urgency": "medium",
  "original_sentiment": "neutral",
  "original_confidence": 0.61,
  "model_version": "sklearn-baseline-20260810-091203",
  "corrected_urgency": "high",
  "feedback_source": "agent"
}
```

Only the fields that were actually wrong need a `corrected_*` value —
anything left `null` falls back to the original prediction
(`TicketFeedback.effective_label()`), so partial corrections are fully
supported. A QA reviewer then calls:

```bash
curl -X POST localhost:8000/feedback/17/review \
  -H "Content-Type: application/json" -d '{"review_status": "approved", "reviewer": "qa_jane"}'
```

Approved-but-not-yet-exported corrections are what the count-based
retraining trigger counts (`GET /retrain/check`).

---

## Retraining pipeline

Trigger it manually:

```bash
curl -X POST "localhost:8000/retrain/run?mode=baseline"
```

or let the background scheduler (APScheduler, checked daily) surface when
either condition is met — weekly age of the active model, or
`RETRAIN_MIN_APPROVED_CORRECTIONS` approved corrections pending export.
`/retrain/run` performs, in order:

1. **validate_labels** — rejects out-of-taxonomy corrections
2. **snapshot_dataset** — merges valid approved corrections with the base
   dataset into a new versioned CSV under `data/feedback_exports/<version>/`
3. **train** — sklearn baseline or transformer, per `mode`
4. **evaluate** — full metric report on a held-out split
5. **compare_against_current** — candidate's weighted F1 vs. the active
   model's, with a configurable tolerance (`RETRAIN_REGRESSION_TOLERANCE`)
6. **register_candidate** — always written to the registry (win or lose)
   for a full audit trail
7. **require_approval** — candidate is left `approval_status='pending'`;
   nothing beyond this point happens automatically
8. **deploy/activate** — a separate, explicit `POST
   /models/{version}/approve` then `POST /models/{version}/activate` call

**Regression safeguard:** if the candidate's headline metric
(`category_weighted_f1`) drops beyond tolerance vs. the active model, the
registry row is flagged `regressed_vs_active=True`. This is enforced at
the registry layer itself — `approve()` and `activate()` both refuse a
flagged row even if some other code path tries to force
`approval_status='approved'` directly (see
`tests/test_regression_guard.py`).

---

## Model versioning & registry

`model_registry` (SQL table, `app/models_db.py::ModelRegistryEntry`) is
the single source of truth for every trained model:

| field                  | meaning                                              |
|-------------------------|--------------------------------------------------------|
| `version`               | unique id, e.g. `sklearn-baseline-20260810-091203`         |
| `model_type`             | `sklearn_baseline` \| `transformer`                            |
| `dataset_start/end`       | date range of the training data                                  |
| `trained_at`               | training timestamp                                                 |
| `metrics`                   | full evaluation report (JSON)                                          |
| `approval_status`            | `pending` → `approved` \| `rejected`                                        |
| `deployment_status`           | `staged` → `active` → `retired`                                                |
| `is_active`                     | exactly one row is `True` at a time                                                |
| `regressed_vs_active`             | permanent block flag, set by the retraining pipeline                                  |

**Rollback:** `activate()` never deletes a model — it demotes the
previous active model to `deployment_status='retired'`. `POST
/models/{version}/rollback` just reactivates any retired-but-still-approved
version, as long as its artifact directory still exists under `models/`
(mounted as a Docker volume so it survives container rebuilds).

---

## Integrating with the main FastAPI backend

This service is designed to be called **synchronously over HTTP** from
the main backend when a ticket is created/updated:

```python
# in the main backend, e.g. app/services/triage_client.py
import httpx

ML_SERVICE_URL = "http://ml-service:8000"  # docker-compose service name

async def classify_ticket(ticket_id: str, subject: str, body: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{ML_SERVICE_URL}/predict",
            json={"ticket_id": ticket_id, "subject": subject, "body": body},
        )
        resp.raise_for_status()
        return resp.json()
```

For high-throughput ingestion, swap the sync call for a queue (the
backend publishes `ticket.created` events; a worker calls `/predict` and
writes results back) — the API contract doesn't change either way.

**Shared database:** both services can point `DATABASE_URL` at the same
Postgres instance. The ML service only owns `ticket_feedback` and
`model_registry` — it never writes to the backend's own tables. If you'd
rather keep full separation, point the ML service at a dedicated
schema/database and have the backend call `POST /feedback` instead of
writing to `ticket_feedback` directly.

**Feedback loop wiring:** when an agent corrects a ticket in the main
backend's UI, the backend should call `POST /feedback` on this service
(not write directly to the DB) so validation and the review workflow stay
consistent regardless of which service owns the actual table.

---

## Tests

```bash
pip install -r requirements.txt
pytest
```

Coverage includes:

- `test_predict.py` — `/predict` response shape, label validity, input validation
- `test_fallback.py` — heuristic classifier correctness + predictor's fallback path when no model is loaded
- `test_feedback.py` — feedback ingestion, review, versioned dataset export, invalid-label rejection
- `test_metrics.py` — accuracy/F1/confusion-matrix/latency/confidence math (pure function, no model needed)
- `test_regression_guard.py` — regressed candidates can never be approved or activated, even if forced

Each test runs against an isolated temp SQLite DB (see `tests/conftest.py`)
— no external services required.

---

## Docker

```bash
docker compose up --build          # Postgres + ML service
docker compose exec ml-service pytest
docker compose exec ml-service python -m app.training.train --mode baseline
```

`models/` and `data/feedback_exports/` are bind-mounted so trained
artifacts and dataset snapshots survive `docker compose down` /
`--build`.

---

## Design notes & known simplifications

- **Subcategory** is modeled as its own flat, category-prefixed label
  space (e.g. `billing_refund`) rather than a nested per-category
  classifier. This keeps all four tasks structurally identical (same
  training code, same evaluation code) at the cost of the model having to
  implicitly learn the category↔subcategory relationship — the predictor
  layer additionally hard-checks consistency and falls back to a
  category-consistent default subcategory if the two heads disagree.
- **Bootstrap model** is intentionally auto-approved (`system-bootstrap`)
  since it has no active model to regress against — every subsequent
  model must go through human approval.
- **Weekly scheduler** logs a signal when triggered rather than paging
  anyone directly; wire `_maybe_start_scheduler()`'s job in `app/main.py`
  to your alerting stack (Slack webhook, PagerDuty, etc.) as needed.
- **Example dataset** (30 rows) is enough to exercise every code path
  (training, evaluation, stratified split) but is not enough data to
  expect strong real-world accuracy — it's a portfolio/dev fixture, not a
  production dataset.
