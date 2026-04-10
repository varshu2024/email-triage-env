"""
Email Triage Environment — FastAPI Server
Implements the OpenEnv HTTP API:
  GET  /health          → health check
  POST /reset           → reset episode (optional ?task=<name>)
  POST /step            → execute action
  GET  /state           → current episode state
  GET  /tasks           → list all available tasks
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.models import EmailTriageAction, EmailTriageObservation, EmailTriageState
from server.environment import EmailTriageEnvironment
from server.tasks import get_all_task_names, TASK_CONFIGS

# ── App Setup ────────────────────────────────
app = FastAPI(
    title="Email Triage Environment",
    description=(
        "A real-world OpenEnv environment for email triage. "
        "An AI agent reads an inbox, classifies emails by urgency, routes them to departments, "
        "drafts replies, and escalates critical issues."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single environment instance per server process
env = EmailTriageEnvironment()


# ── Endpoints ────────────────────────────────

@app.get("/health")
def health():
    """Health check — returns 200 if server is running."""
    return {"status": "ok", "env": "email-triage-env", "version": "1.0.0"}


@app.post("/reset", response_model=EmailTriageObservation)
def reset(task: str = Query(default="classify-urgency", description="Task name")):
    """
    Reset the environment and start a new episode.

    Args:
        task: Task name — one of: classify-urgency, route-emails, full-triage
    Returns:
        Initial observation with current email and task description.
    """
    obs = env.reset(task_name=task)
    return obs


@app.post("/step", response_model=EmailTriageObservation)
def step(action: EmailTriageAction):
    """
    Execute one action in the environment.

    Action fields:
      - action_type: classify | route | reply | escalate | next
      - classification: urgent | normal | low  (for classify)
      - department: Support | HR | Finance | Legal | Spam  (for route)
      - reply_text: string  (for reply)
    Returns:
        Observation with reward, feedback, done flag, and current score.
    """
    obs = env.step(action)
    return obs


@app.get("/state", response_model=EmailTriageState)
def state():
    """
    Get current episode state (without advancing the environment).

    Returns:
        State with episode_id, step_count, task_name, score, emails_processed.
    """
    return env.state


@app.get("/tasks")
def tasks():
    """List all available tasks with descriptions."""
    return {
        "tasks": [
            {
                "name": cfg["name"],
                "difficulty": cfg["difficulty"],
                "max_steps": cfg["max_steps"],
                "description": cfg["description"],
                "available_actions": cfg["available_actions"],
            }
            for cfg in TASK_CONFIGS.values()
        ]
    }


@app.get("/")
def root():
    """Root endpoint — links to docs."""
    return {
        "env": "email-triage-env",
        "description": "Real-world Email Triage OpenEnv environment",
        "docs": "/docs",
        "tasks": get_all_task_names(),
        "endpoints": {
            "health": "GET /health",
            "reset": "POST /reset?task=<task_name>",
            "step": "POST /step",
            "state": "GET /state",
            "tasks": "GET /tasks",
        },
    }
