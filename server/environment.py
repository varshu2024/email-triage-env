"""
Email Triage Environment — Core Environment Logic
Implements: reset(), step(), state property
"""

import uuid
from typing import Optional

from server.models import EmailTriageAction, EmailTriageObservation, EmailTriageState
from server.data import get_task_emails, get_ground_truth
from server.tasks import get_task_config, get_all_task_names, compute_step_reward, grade


class EmailTriageEnvironment:
    """
    A real-world Email Triage environment.

    The agent receives an inbox of realistic emails and must:
      - Classify each email by urgency (urgent/normal/low)
      - Route each to the correct department
      - Draft replies for urgent issues (full-triage task)
      - Escalate critical legal/compliance items (full-triage task)

    Three tasks of increasing difficulty:
      1. classify-urgency (easy)   — classify 5 emails
      2. route-emails    (medium)  — classify + route 5 emails
      3. full-triage     (hard)    — full processing of 8 emails

    API:
      reset(task_name) → EmailTriageObservation
      step(action)     → EmailTriageObservation
      state            → EmailTriageState  (property)
    """

    def __init__(self):
        self._episode_id: str = ""
        self._step_count: int = 0
        self._task_name: str = ""
        self._task_config: dict = {}
        self._emails: list = []           # public email data (no ground truth)
        self._ground_truth: list = []     # full data including expected labels
        self._current_idx: int = 0
        self._email_actions: dict = {}    # tracking: {email_id: {action_type: value, ...}}
        self._reward_per_step: list = []
        self._done: bool = False
        self._score: float = 0.0

    # ─────────────────────────────────────
    # OpenEnv API: reset()
    # ─────────────────────────────────────
    def reset(self, task_name: Optional[str] = None) -> EmailTriageObservation:
        task_name = task_name or "classify-urgency"

        if task_name not in get_all_task_names():
            task_name = "classify-urgency"

        self._episode_id = str(uuid.uuid4())
        self._step_count = 0
        self._task_name = task_name
        self._task_config = get_task_config(task_name)
        self._emails = get_task_emails(task_name)
        self._ground_truth = get_ground_truth(task_name)
        self._current_idx = 0
        self._email_actions = {e["email_id"]: {} for e in self._emails}
        self._reward_per_step = []
        self._done = False
        self._score = 0.0

        return EmailTriageObservation(
            done=False,
            reward=0.0,
            current_email=self._emails[0] if self._emails else None,
            task_name=self._task_name,
            task_description=self._task_config.get("description", ""),
            available_actions=self._task_config.get("available_actions", []),
            feedback=f"Episode started. Task: {task_name}. {len(self._emails)} emails to process.",
            score=0.0,
            step_count=0,
            emails_processed=0,
            total_emails=len(self._emails),
        )

    # ─────────────────────────────────────
    # OpenEnv API: step()
    # ─────────────────────────────────────
    def step(self, action: EmailTriageAction) -> EmailTriageObservation:
        self._step_count += 1
        error_msg = None

        # Guard: already done
        if self._done:
            return self._build_obs(0.0, "Episode is already done. Call reset() to start a new episode.", error="Episode done")

        # Guard: validate action type
        valid_actions = {"classify", "route", "reply", "escalate", "next"}
        if action.action_type not in valid_actions:
            error_msg = f"Unknown action_type '{action.action_type}'. Valid: {sorted(valid_actions)}"
            return self._build_obs(-0.01, error_msg, error=error_msg)

        # Guard: inbox exhausted
        if self._current_idx >= len(self._emails):
            self._done = True
            self._score = grade(self._task_name, self._email_actions)
            return self._build_obs(0.0, "All emails processed.", done=True)

        current_email = self._emails[self._current_idx]
        email_id = current_email["email_id"]
        reward = 0.0
        feedback = ""

        # ── Handle: classify ──
        if action.action_type == "classify":
            valid_classes = {"urgent", "normal", "low"}
            if not action.classification or action.classification not in valid_classes:
                error_msg = f"classify requires classification: urgent|normal|low. Got: '{action.classification}'"
                return self._build_obs(-0.01, error_msg, error=error_msg)

            self._email_actions[email_id]["classification"] = action.classification
            reward = compute_step_reward(
                self._task_name, email_id, "classify", action.classification, self._ground_truth
            )
            sign = "✓ Correct!" if reward > 0 else "✗ Incorrect"
            feedback = f"[{sign}] Classified email '{current_email['subject'][:50]}' as '{action.classification}'."

        # ── Handle: route ──
        elif action.action_type == "route":
            valid_depts = {"Support", "HR", "Finance", "Legal", "Spam", "Marketing"}
            if not action.department or action.department not in valid_depts:
                error_msg = f"route requires department: Support|HR|Finance|Legal|Spam|Marketing. Got: '{action.department}'"
                return self._build_obs(-0.01, error_msg, error=error_msg)

            self._email_actions[email_id]["department"] = action.department
            reward = compute_step_reward(
                self._task_name, email_id, "route", action.department, self._ground_truth
            )
            sign = "✓ Correct!" if reward > 0 else "✗ Incorrect"
            feedback = f"[{sign}] Routed email to '{action.department}'."

        # ── Handle: reply ──
        elif action.action_type == "reply":
            if not action.reply_text or len(action.reply_text.strip()) < 10:
                error_msg = "reply requires reply_text with at least 10 characters."
                return self._build_obs(-0.01, error_msg, error=error_msg)

            self._email_actions[email_id]["reply"] = action.reply_text
            reward = compute_step_reward(
                self._task_name, email_id, "reply", action.reply_text, self._ground_truth
            )
            feedback = f"Reply drafted for '{current_email['subject'][:50]}'."

        # ── Handle: escalate ──
        elif action.action_type == "escalate":
            self._email_actions[email_id]["escalated"] = True
            reward = compute_step_reward(
                self._task_name, email_id, "escalate", "escalated", self._ground_truth
            )
            sign = "✓ Correct!" if reward > 0 else "(no escalation needed for this email)"
            feedback = f"[{sign}] Escalated email '{current_email['subject'][:50]}'."

        # ── Handle: next ──
        elif action.action_type == "next":
            self._current_idx += 1
            if self._current_idx >= len(self._emails):
                # All emails processed
                self._done = True
                self._score = grade(self._task_name, self._email_actions)
                self._reward_per_step.append(0.0)
                return self._build_obs(
                    0.0,
                    f"All {len(self._emails)} emails processed! Final score: {self._score:.2f}",
                    done=True
                )
            feedback = f"Moving to next email ({self._current_idx + 1}/{len(self._emails)})."

        # ── Penalty: max steps exceeded ──
        max_steps = self._task_config.get("max_steps", 20)
        self._reward_per_step.append(reward)

        done = False
        if self._step_count >= max_steps:
            self._done = True
            self._score = grade(self._task_name, self._email_actions)
            done = True
            feedback += f" [Max steps reached] Final score: {self._score:.2f}"

        return self._build_obs(reward, feedback, done=done, error=error_msg)

    # ─────────────────────────────────────
    # OpenEnv API: state (property)
    # ─────────────────────────────────────
    @property
    def state(self) -> EmailTriageState:
        return EmailTriageState(
            episode_id=self._episode_id,
            step_count=self._step_count,
            task_name=self._task_name,
            score=self._score,
            emails_processed=self._current_idx,
            total_emails=len(self._emails),
            done=self._done,
        )

    # ─────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────
    def _build_obs(
        self,
        reward: float,
        feedback: str,
        done: bool = False,
        error: Optional[str] = None,
    ) -> EmailTriageObservation:
        current_email = (
            self._emails[self._current_idx]
            if self._current_idx < len(self._emails)
            else None
        )
        partial_score = grade(self._task_name, self._email_actions) if self._email_actions else 0.0
        if done:
            partial_score = self._score

        return EmailTriageObservation(
            done=done,
            reward=reward,
            current_email=current_email,
            task_name=self._task_name,
            task_description=self._task_config.get("description", ""),
            available_actions=self._task_config.get("available_actions", []),
            feedback=feedback,
            score=partial_score,
            step_count=self._step_count,
            emails_processed=self._current_idx,
            total_emails=len(self._emails),
            last_action_error=error,
        )
