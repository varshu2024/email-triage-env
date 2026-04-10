---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 📧 Email Triage Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

A real-world **Email Triage & Prioritization** environment for training and evaluating AI agents using the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework.

Agents process realistic corporate email inboxes — classifying urgency, routing to departments, drafting replies, and escalating critical issues — exactly as a human email assistant would.

---

## 🌍 Real-World Motivation

Email overload is a genuine productivity crisis: the average professional spends **28% of their workday reading and answering email** (McKinsey). An AI agent that can intelligently triage emails — prioritizing urgent issues, routing to the right team, and drafting appropriate replies — has immediate practical value for enterprise productivity tools.

---

## 🗺️ Environment Overview

| Property | Value |
|----------|-------|
| **Task domain** | Corporate email triage |
| **Action space** | Discrete + text (classify, route, reply, escalate, next) |
| **Observation space** | Structured email + task context |
| **Reward type** | Dense (per-step) + terminal |
| **Episodes** | Up to 24 steps |
| **Tasks** | 3 (easy → medium → hard) |

---

## ✉️ Action Space

| Action | Required Field | Valid Values |
|--------|---------------|--------------|
| `classify` | `classification` | `urgent` \| `normal` \| `low` |
| `route` | `department` | `Support` \| `HR` \| `Finance` \| `Legal` \| `Spam` \| `Marketing` |
| `reply` | `reply_text` | Any string (≥10 chars) |
| `escalate` | — | (no extra fields) |
| `next` | — | Advance to next email |

**JSON example:**
```json
{"action_type": "classify", "classification": "urgent"}
{"action_type": "route", "department": "Legal"}
{"action_type": "reply", "reply_text": "Our team is investigating this immediately and will update you within the hour."}
{"action_type": "escalate"}
{"action_type": "next"}
```

---

## 👁️ Observation Space

Each `step()` and `reset()` returns an `EmailTriageObservation`:

| Field | Type | Description |
|-------|------|-------------|
| `done` | `bool` | Whether episode has ended |
| `reward` | `float` | Reward from last action (0.0–0.2) |
| `current_email` | `dict` | Email currently being processed |
| `task_name` | `str` | Active task identifier |
| `task_description` | `str` | Full task instructions |
| `available_actions` | `list[str]` | Actions valid in this task |
| `feedback` | `str` | Human-readable result of last action |
| `score` | `float` | Running episode score (0.0–1.0) |
| `step_count` | `int` | Steps taken so far |
| `emails_processed` | `int` | Emails completed |
| `total_emails` | `int` | Total emails in inbox |
| `last_action_error` | `str \| null` | Error message if action was invalid |

**Current Email fields:** `email_id`, `subject`, `sender`, `body`, `timestamp`

---

## 📋 Tasks

### Task 1: `classify-urgency` 🟢 Easy

**Objective:** Classify 5 emails as `urgent`, `normal`, or `low` priority.

**Max steps:** 12 | **Scoring:** correct_count / 5

**Reward per step:** +0.20 per correct classification, 0.00 if wrong

**Example inbox:** Server outage alerts, team events, contract renewals, security breaches, newsletters.

---

### Task 2: `route-emails` 🟡 Medium

**Objective:** Classify + route 5 emails to the correct department (Support, HR, Finance, Legal, Spam).

**Max steps:** 16 | **Scoring:** 0.3 × classify_score + 0.7 × route_score

**Reward per step:** +0.10 per correct classification, +0.10 per correct route

**Example inbox:** Login issues → Support, parental leave query → HR, overdue invoice → Finance, legal notice → Legal, phishing email → Spam.

---

### Task 3: `full-triage` 🔴 Hard

**Objective:** Fully process 8 emails — classify + route all, draft replies for urgent support issues, and escalate legal threats.

**Max steps:** 24

**Scoring formula:**
```
score = 0.25 × classify_accuracy
      + 0.25 × route_accuracy
      + 0.25 × reply_quality   (keyword-based grader)
      + 0.25 × escalation_rate (of required escalations)
```

**Reply quality:** Grader checks for relevant keywords (e.g., "investigating", "team", "resolve", "update") — full marks for ≥2 keywords, partial for 1.

---

## 🏆 Reward Design

The reward function provides **dense signals** throughout the episode:

| Action | Condition | Reward |
|--------|-----------|--------|
| `classify` | Correct urgency | +0.20 (task 1), +0.10 (task 2), +0.06 (task 3) |
| `classify` | Wrong urgency | 0.00 |
| `route` | Correct department | +0.10 (task 2), +0.06 (task 3) |
| `route` | Wrong department | 0.00 |
| `reply` | Required + adequate text | +0.06 (task 3) |
| `escalate` | Required escalation | +0.06 (task 3) |
| Invalid action | e.g. missing field | -0.01 (small penalty) |

---

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

Then interact:
```bash
curl http://localhost:7860/health
curl -X POST "http://localhost:7860/reset?task=classify-urgency"
curl -X POST http://localhost:7860/step \
     -H "Content-Type: application/json" \
     -d '{"action_type": "classify", "classification": "urgent"}'
```

### Option 2: Local (Python)

```bash
pip install -r server/requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

### API Docs

Visit http://localhost:7860/docs for interactive Swagger UI.

---

## 🤖 Running the Inference Script

```bash
# Set environment variables
export HF_TOKEN="your-hf-token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

# Optional: if env server is already running (e.g., HF Space)
export ENV_BASE_URL="https://your-space.hf.space"

# Run inference (starts local server automatically if ENV_BASE_URL not set)
python inference.py
```

**Expected output format:**
```
[START] task=classify-urgency env=email-triage-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action={"action_type":"classify","classification":"urgent"} reward=0.20 done=false error=null
...
[END] success=true steps=8 score=0.80 rewards=0.20,0.00,0.20,0.20,0.00,0.00,0.20,0.00
```

---

## 📊 Baseline Scores

Measured with `Qwen/Qwen2.5-72B-Instruct` via HF Router:

| Task | Score | Notes |
|------|-------|-------|
| classify-urgency | ~0.80 | Strong at urgency detection |
| route-emails | ~0.65 | Occasionally confuses Support vs Legal |
| full-triage | ~0.55 | Struggles with reply drafting requirements |

---

## 🏗️ Project Structure

```
email-triage-env/
├── inference.py         # 🔴 Mandatory inference script (root level)
├── openenv.yaml         # Environment manifest
├── Dockerfile           # Container definition
├── pyproject.toml       # Package config & dependencies
├── README.md            # This file
├── __init__.py          # Root package exports
└── server/
    ├── __init__.py
    ├── app.py           # FastAPI application & endpoints
    ├── environment.py   # Core environment logic (reset/step/state)
    ├── tasks.py         # Task configs + graders
    ├── data.py          # Deterministic email datasets
    ├── models.py        # Pydantic models (Action/Observation/State)
    └── requirements.txt # Python dependencies
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/reset?task=<name>` | POST | Start new episode |
| `/step` | POST | Execute action |
| `/state` | GET | Get episode state |
| `/tasks` | GET | List all tasks |
| `/docs` | GET | Interactive API docs |

---

## 🚢 Deploying to Hugging Face Spaces

1. Create a new Space on Hugging Face (Docker type)
2. Push this repository
3. Set Space hardware: CPU Basic (2 vCPU, 16GB RAM)
4. The Space will auto-build and expose the environment

**Required Space secrets (optional for inference):**
- `HF_TOKEN`
- `API_BASE_URL`
- `MODEL_NAME`

---

## 📜 License

Apache 2.0 — see [LICENSE](LICENSE)
