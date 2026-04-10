"""
Email Triage Environment — inference.py
========================================
Mandatory inference script for Scaler OpenEnv Hackathon Round 1.

MANDATORY ENVIRONMENT VARIABLES:
  API_BASE_URL   The API endpoint for the LLM.
  MODEL_NAME     The model identifier to use for inference.
  HF_TOKEN       Your Hugging Face / API key.

  ENV_BASE_URL   (optional) URL of running environment server.
                 Defaults to http://localhost:7860 (starts local server if needed).

STDOUT FORMAT (exact, do not modify):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import subprocess
import sys
import time
from typing import Optional

import requests
from openai import OpenAI

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL") or "http://localhost:7860"
BENCHMARK = "email-triage-env"
MAX_STEPS = 8

TASKS = ["classify-urgency", "route-emails", "full-triage"]

# ─────────────────────────────────────────────
# System Prompt for Agent
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert email triage assistant. Your job is to process emails in an inbox by taking structured actions.

AVAILABLE ACTIONS (output one per turn as valid JSON):
1. Classify urgency:   {"action_type": "classify", "classification": "urgent|normal|low"}
2. Route to dept:      {"action_type": "route", "department": "Support|HR|Finance|Legal|Spam|Marketing"}
3. Draft a reply:      {"action_type": "reply", "reply_text": "Your reply here..."}
4. Escalate email:     {"action_type": "escalate"}
5. Go to next email:   {"action_type": "next"}

RULES:
- Output ONLY valid JSON on a single line — no markdown, no explanation.
- Classify BEFORE routing.
- Use 'escalate' for legal/compliance threats.
- Use 'reply' for urgent issues that need a response draft.
- Use 'next' when done with the current email.
- Urgency guide: 'urgent'=immediate attention needed, 'normal'=standard priority, 'low'=no rush.
- Department guide: Support=technical/account issues, HR=people/policies, Finance=billing/payments, Legal=legal threats, Spam=junk/phishing.
"""


# ─────────────────────────────────────────────
# Server Management
# ─────────────────────────────────────────────
_server_proc: Optional[subprocess.Popen] = None


def start_local_server() -> bool:
    """Start a local uvicorn server if ENV_BASE_URL points to localhost."""
    global _server_proc
    if "localhost" not in ENV_BASE_URL and "127.0.0.1" not in ENV_BASE_URL:
        return True  # Using remote server — no need to start

    port = ENV_BASE_URL.split(":")[-1].split("/")[0] if ":" in ENV_BASE_URL else "7860"

    print(f"[INFO] Starting local server on port {port}...", file=sys.stderr)
    _server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.app:app",
         "--host", "0.0.0.0", "--port", str(port), "--log-level", "error"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 30s for server to be ready
    for attempt in range(30):
        try:
            resp = requests.get(f"{ENV_BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                print(f"[INFO] Server ready after {attempt + 1}s.", file=sys.stderr)
                return True
        except Exception:
            pass
        time.sleep(1)

    print("[ERROR] Server failed to start within 30 seconds.", file=sys.stderr)
    return False


def stop_local_server():
    """Terminate the local server process."""
    global _server_proc
    if _server_proc:
        _server_proc.terminate()
        _server_proc = None


# ─────────────────────────────────────────────
# Observation Formatting
# ─────────────────────────────────────────────
def format_observation(obs: dict) -> str:
    """Format observation dict into a human-readable string for the LLM."""
    parts = []

    current = obs.get("current_email")
    if current:
        parts.append(f"=== CURRENT EMAIL ===")
        parts.append(f"From:    {current.get('sender', '')}")
        parts.append(f"Subject: {current.get('subject', '')}")
        parts.append(f"Time:    {current.get('timestamp', '')}")
        parts.append(f"Body:\n{current.get('body', '')}")
        parts.append("")

    parts.append(f"=== STATUS ===")
    parts.append(f"Task: {obs.get('task_name', '')} | "
                 f"Email {obs.get('emails_processed', 0) + 1}/{obs.get('total_emails', 0)} | "
                 f"Step: {obs.get('step_count', 0)}")
    if obs.get("feedback"):
        parts.append(f"Feedback: {obs['feedback']}")
    parts.append(f"Current Score: {obs.get('score', 0.0):.2f}")
    parts.append("")
    parts.append("Available actions: " + ", ".join(obs.get("available_actions", [])))
    parts.append("\nOutput your action as a single line of JSON:")

    return "\n".join(parts)


# ─────────────────────────────────────────────
# Action Parsing
# ─────────────────────────────────────────────
def parse_action(text: str) -> dict:
    """Parse LLM output into a valid action dict."""
    text = text.strip()

    # Remove markdown code fences if present
    if "```" in text:
        lines = text.split("\n")
        json_lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(json_lines).strip()

    # Try to extract JSON from the text
    # Find first { ... }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        action = json.loads(text)
        # Validate action_type
        valid = {"classify", "route", "reply", "escalate", "next"}
        if action.get("action_type") not in valid:
            return {"action_type": "next"}
        return action
    except json.JSONDecodeError:
        # Fallback: try to detect intent from plain text
        text_lower = text.lower()
        if "urgent" in text_lower:
            return {"action_type": "classify", "classification": "urgent"}
        if "normal" in text_lower:
            return {"action_type": "classify", "classification": "normal"}
        if "low" in text_lower:
            return {"action_type": "classify", "classification": "low"}
        return {"action_type": "next"}


# ─────────────────────────────────────────────
# Task Runner
# ─────────────────────────────────────────────
def run_task(task_name: str, client: OpenAI) -> dict:
    """Run one full episode for a given task. Returns score and reward list."""
    rewards = []
    steps = 0
    done = False
    final_score = 0.0

    # Reset environment
    try:
        resp = requests.post(f"{ENV_BASE_URL}/reset?task={task_name}", timeout=10)
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}")
        print(f"[END] success=false steps=0 score=0.00 rewards=")
        return {"score": 0.0, "rewards": [], "success": False}

    # Log start
    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"You are starting task: {task_name}\n"
            f"Instructions: {obs.get('task_description', '')}\n\n"
            + format_observation(obs)
        )},
    ]

    while not done and steps < MAX_STEPS:
        # Get action from LLM
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=256,
                temperature=0.0,
            )
            action_text = response.choices[0].message.content.strip()
        except Exception as e:
            action_text = '{"action_type": "next"}'

        messages.append({"role": "assistant", "content": action_text})

        # Parse action
        action = parse_action(action_text)
        action_str = json.dumps(action, separators=(",", ":"))

        # Execute step
        error_val = "null"
        try:
            step_resp = requests.post(
                f"{ENV_BASE_URL}/step",
                json=action,
                timeout=15,
            )
            step_resp.raise_for_status()
            obs = step_resp.json()

            reward = float(obs.get("reward", 0.0))
            done = bool(obs.get("done", False))
            final_score = float(obs.get("score", 0.0))
            error_raw = obs.get("last_action_error")
            error_val = error_raw.replace("\n", " ") if error_raw else "null"

        except Exception as e:
            reward = 0.0
            error_val = str(e).replace("\n", " ")[:80]

        steps += 1
        rewards.append(reward)
        done_str = "true" if done else "false"

        # STEP log line (exact format)
        print(f"[STEP] step={steps} action={action_str} reward={reward:.2f} done={done_str} error={error_val}")

        if not done:
            messages.append({"role": "user", "content": format_observation(obs)})

    success = final_score >= 0.5
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    # END log line (exact format)
    print(f"[END] success={success_str} steps={steps} score={final_score:.2f} rewards={rewards_str}")

    return {"score": final_score, "rewards": rewards, "success": success}


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    # Start server if needed
    if not start_local_server():
        print("[ERROR] Could not connect to environment server.", file=sys.stderr)
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
    )

    # Run all tasks
    results = {}
    for task in TASKS:
        result = run_task(task, client)
        results[task] = result

    # Summary to stderr (not stdout, to avoid interfering with log format)
    print("\n=== SUMMARY ===", file=sys.stderr)
    for task, res in results.items():
        print(f"  {task}: score={res['score']:.2f}, success={res['success']}", file=sys.stderr)

    # Cleanup
    stop_local_server()


if __name__ == "__main__":
    main()
