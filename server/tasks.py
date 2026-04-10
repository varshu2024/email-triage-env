"""
Email Triage Environment — Task Definitions & Graders
Each task has: config, description, max_steps, and a grade() function.
All graders are deterministic and return a score in [0.0, 1.0].
"""

from server.data import get_ground_truth


# ─────────────────────────────────────────────
# Task Metadata
# ─────────────────────────────────────────────
TASK_CONFIGS = {
    "classify-urgency": {
        "name": "classify-urgency",
        "difficulty": "easy",
        "max_steps": 12,
        "description": (
            "You have an inbox with 5 emails. For each email, classify it as "
            "'urgent', 'normal', or 'low' priority based on the subject and body. "
            "Use action_type='classify' with the classification field. "
            "Use action_type='next' to advance to the next email after classifying. "
            "Goal: Correctly classify all 5 emails."
        ),
        "available_actions": ["classify (classification: urgent|normal|low)", "next"],
    },
    "route-emails": {
        "name": "route-emails",
        "difficulty": "medium",
        "max_steps": 16,
        "description": (
            "You have an inbox with 5 emails. For each email: "
            "(1) Classify it as 'urgent', 'normal', or 'low'. "
            "(2) Route it to the correct department: Support, HR, Finance, Legal, or Spam. "
            "Use action_type='next' to advance after handling each email. "
            "Goal: Classify and route all emails correctly."
        ),
        "available_actions": [
            "classify (classification: urgent|normal|low)",
            "route (department: Support|HR|Finance|Legal|Spam)",
            "next",
        ],
    },
    "full-triage": {
        "name": "full-triage",
        "difficulty": "hard",
        "max_steps": 24,
        "description": (
            "You have an inbox with 8 emails requiring full triage. For each email: "
            "(1) Classify urgency: urgent|normal|low. "
            "(2) Route to correct department: Support|HR|Finance|Legal|Spam. "
            "(3) For emails requiring a reply (urgent + Support issues), use action_type='reply' "
            "    with a helpful reply_text acknowledging the issue and promising action. "
            "(4) Escalate legal/compliance threats using action_type='escalate'. "
            "Use action_type='next' to advance after handling each email. "
            "Goal: Correctly triage all 8 emails — classify, route, reply to urgent issues, "
            "and escalate critical legal matters."
        ),
        "available_actions": [
            "classify (classification: urgent|normal|low)",
            "route (department: Support|HR|Finance|Legal|Spam|Marketing)",
            "reply (reply_text: your draft reply)",
            "escalate",
            "next",
        ],
    },
}


def get_task_config(task_name: str) -> dict:
    return TASK_CONFIGS.get(task_name, {})


def get_all_task_names() -> list:
    return list(TASK_CONFIGS.keys())


# ─────────────────────────────────────────────
# Reward Signals (per-step, during episode)
# ─────────────────────────────────────────────

def compute_step_reward(task_name: str, email_id: str, action_type: str,
                        action_value: str, ground_truth: list) -> float:
    """
    Compute immediate reward for a single action on a specific email.
    Returns a float in [0.0, 0.2].
    """
    gt_map = {e["email_id"]: e for e in ground_truth}
    gt = gt_map.get(email_id)
    if gt is None:
        return 0.0

    if task_name == "classify-urgency":
        if action_type == "classify":
            return 0.2 if action_value == gt.get("expected_classification") else 0.0

    elif task_name == "route-emails":
        if action_type == "classify":
            return 0.1 if action_value == gt.get("expected_classification") else 0.0
        if action_type == "route":
            return 0.1 if action_value == gt.get("expected_department") else 0.0

    elif task_name == "full-triage":
        if action_type == "classify":
            return 0.06 if action_value == gt.get("expected_classification") else 0.0
        if action_type == "route":
            return 0.06 if action_value == gt.get("expected_department") else 0.0
        if action_type == "reply" and gt.get("requires_reply"):
            # Partial reward for drafting any reply to a required email
            return 0.06 if action_value and len(action_value.strip()) > 10 else 0.0
        if action_type == "escalate" and gt.get("requires_escalation"):
            return 0.06
    return 0.0


# ─────────────────────────────────────────────
# Final Graders (end-of-episode, 0.0–1.0)
# ─────────────────────────────────────────────

def grade_classify_urgency(email_actions: dict) -> float:
    """
    Task 1: classify-urgency
    Score = correct_classifications / 5
    email_actions: {email_id: {"classification": str, ...}}
    """
    ground_truth = get_ground_truth("classify-urgency")
    gt_map = {e["email_id"]: e["expected_classification"] for e in ground_truth}

    total = len(gt_map)
    if total == 0:
        return 0.0

    correct = sum(
        1
        for eid, expected in gt_map.items()
        if email_actions.get(eid, {}).get("classification") == expected
    )
    return round(correct / total, 4)


def grade_route_emails(email_actions: dict) -> float:
    """
    Task 2: route-emails
    Score = 0.3 * (correct_classifications/5) + 0.7 * (correct_routes/5)
    """
    ground_truth = get_ground_truth("route-emails")
    total = len(ground_truth)
    if total == 0:
        return 0.0

    correct_classify = 0
    correct_route = 0

    for e in ground_truth:
        eid = e["email_id"]
        agent_actions = email_actions.get(eid, {})
        if agent_actions.get("classification") == e["expected_classification"]:
            correct_classify += 1
        if agent_actions.get("department") == e["expected_department"]:
            correct_route += 1

    classify_score = correct_classify / total
    route_score = correct_route / total
    return round(0.3 * classify_score + 0.7 * route_score, 4)


def _reply_quality(reply_text: str, keywords: list) -> float:
    """Score reply quality: 1.0 if ≥2 keywords found, 0.5 if 1, 0.0 if none."""
    if not reply_text or not keywords:
        return 0.0
    reply_lower = reply_text.lower()
    found = sum(1 for kw in keywords if kw.lower() in reply_lower)
    if found >= 2:
        return 1.0
    elif found == 1:
        return 0.5
    return 0.0


def grade_full_triage(email_actions: dict) -> float:
    """
    Task 3: full-triage
    Score = 0.25 * classify_score
           + 0.25 * route_score
           + 0.25 * reply_score
           + 0.25 * escalation_score
    """
    ground_truth = get_ground_truth("full-triage")
    total = len(ground_truth)
    if total == 0:
        return 0.0

    correct_classify = 0
    correct_route = 0
    reply_scores = []
    escalation_hits = 0
    escalation_required = 0

    for e in ground_truth:
        eid = e["email_id"]
        agent_actions = email_actions.get(eid, {})

        # Classification
        if agent_actions.get("classification") == e["expected_classification"]:
            correct_classify += 1

        # Routing
        if agent_actions.get("department") == e["expected_department"]:
            correct_route += 1

        # Reply quality (only for emails requiring reply)
        if e.get("requires_reply"):
            reply_text = agent_actions.get("reply", "")
            keywords = e.get("reply_keywords", [])
            reply_scores.append(_reply_quality(reply_text, keywords))

        # Escalation
        if e.get("requires_escalation"):
            escalation_required += 1
            if agent_actions.get("escalated", False):
                escalation_hits += 1

    classify_score = correct_classify / total
    route_score = correct_route / total
    reply_score = (sum(reply_scores) / len(reply_scores)) if reply_scores else 1.0
    escalation_score = (escalation_hits / escalation_required) if escalation_required > 0 else 1.0

    final = 0.25 * classify_score + 0.25 * route_score + 0.25 * reply_score + 0.25 * escalation_score
    return round(final, 4)


# ─────────────────────────────────────────────
# Unified Grader Dispatcher
# ─────────────────────────────────────────────
GRADERS = {
    "classify-urgency": grade_classify_urgency,
    "route-emails": grade_route_emails,
    "full-triage": grade_full_triage,
}


def grade(task_name: str, email_actions: dict) -> float:
    """Grade the full episode and return a score in [0.0, 1.0]."""
    grader = GRADERS.get(task_name)
    if grader is None:
        return 0.0
    return grader(email_actions)
