"""
Email Triage Environment — Pydantic Models
Typed Action, Observation, and State models following the OpenEnv spec.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class Email(BaseModel):
    """Represents a single email in the inbox."""
    email_id: str
    subject: str
    sender: str
    body: str
    timestamp: str


class EmailTriageAction(BaseModel):
    """
    Action an agent can take on an email.

    action_type options:
      - 'classify'  : Label current email urgency (requires classification field)
      - 'route'     : Route current email to a department (requires department field)
      - 'reply'     : Draft a reply to current email (requires reply_text field)
      - 'escalate'  : Flag email for human escalation
      - 'next'      : Advance to the next email in the inbox
    """
    action_type: str = Field(..., description="One of: classify, route, reply, escalate, next")
    classification: Optional[str] = Field(None, description="urgent | normal | low")
    department: Optional[str] = Field(None, description="Support | HR | Finance | Legal | Spam | Marketing")
    reply_text: Optional[str] = Field(None, description="Draft reply text for the current email")
    reasoning: Optional[str] = Field(None, description="Agent's reasoning (optional, not graded)")


class EmailTriageObservation(BaseModel):
    """
    Observation returned after each step.

    Includes the current email, task instructions, feedback from last action,
    running score, and episode status.
    """
    done: bool = False
    reward: float = 0.0
    current_email: Optional[Dict[str, Any]] = None
    task_name: str = ""
    task_description: str = ""
    available_actions: List[str] = Field(default_factory=list)
    feedback: str = ""
    score: float = 0.0
    step_count: int = 0
    emails_processed: int = 0
    total_emails: int = 0
    last_action_error: Optional[str] = None


class EmailTriageState(BaseModel):
    """
    Episode-level state metadata (OpenEnv state() API).
    """
    episode_id: str = ""
    step_count: int = 0
    task_name: str = ""
    score: float = 0.0
    emails_processed: int = 0
    total_emails: int = 0
    done: bool = False
