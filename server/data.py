"""
Email Triage Environment — Deterministic Email Datasets
All datasets are hardcoded for reproducibility across evaluations.
"""

# ─────────────────────────────────────────────
# Task 1: classify-urgency  (Easy — 5 emails)
# Agent must classify each email: urgent / normal / low
# ─────────────────────────────────────────────
CLASSIFY_EMAILS = [
    {
        "email_id": "c001",
        "subject": "URGENT: Production database server is DOWN",
        "sender": "alerts@company.com",
        "body": (
            "Critical alert: Our main production database has crashed. ALL services are down. "
            "Customers cannot log in or access data. Every minute of downtime costs us revenue. "
            "Please respond immediately — escalate to senior engineering NOW."
        ),
        "timestamp": "2024-03-15 09:03:00",
        "expected_classification": "urgent",
    },
    {
        "email_id": "c002",
        "subject": "Team Building Event — Save the Date",
        "sender": "hr@company.com",
        "body": (
            "Hi team! We are planning a team building day on April 20th. "
            "Fun activities, lunch, and team bonding await. Please fill out the availability form "
            "by end of next week. Looking forward to seeing everyone there!"
        ),
        "timestamp": "2024-03-15 09:15:00",
        "expected_classification": "low",
    },
    {
        "email_id": "c003",
        "subject": "Action Required: Contract Renewal Due Friday",
        "sender": "vendor@acmecorp.com",
        "body": (
            "Dear Partner, this is a reminder that your annual service contract is due for renewal "
            "this Friday, March 17th. Please review the updated terms and sign the attached agreement. "
            "Contact us if you have any questions."
        ),
        "timestamp": "2024-03-15 10:00:00",
        "expected_classification": "normal",
    },
    {
        "email_id": "c004",
        "subject": "CRITICAL: Suspected Data Breach — Customer PII Exposed",
        "sender": "security@company.com",
        "body": (
            "SECURITY ALERT: Our intrusion detection system has flagged unusual data exfiltration "
            "from the customer database. Potentially 50,000 customer records including PII may have "
            "been accessed. Immediate containment required. Legal and compliance must be notified NOW."
        ),
        "timestamp": "2024-03-15 10:30:00",
        "expected_classification": "urgent",
    },
    {
        "email_id": "c005",
        "subject": "Newsletter: Q1 2024 Company Updates",
        "sender": "newsletter@company.com",
        "body": (
            "Hello! Here are this quarter's highlights: We grew revenue by 15%, launched 3 new "
            "product features, and welcomed 12 new team members. Read the full newsletter at "
            "our internal portal. Have a great week!"
        ),
        "timestamp": "2024-03-15 11:00:00",
        "expected_classification": "low",
    },
]

# ─────────────────────────────────────────────
# Task 2: route-emails  (Medium — 5 emails)
# Agent must classify + route emails to the correct department
# ─────────────────────────────────────────────
ROUTE_EMAILS = [
    {
        "email_id": "r001",
        "subject": "Cannot log into my account — locked out for 3 days",
        "sender": "john.doe@gmail.com",
        "body": (
            "Hi, I have been unable to log into my account for 3 days now. "
            "I tried resetting my password but the reset email never arrives. "
            "I have important files in my account. Please help urgently."
        ),
        "timestamp": "2024-03-15 08:00:00",
        "expected_classification": "urgent",
        "expected_department": "Support",
    },
    {
        "email_id": "r002",
        "subject": "Request for Parental Leave Policy Details",
        "sender": "employee.jane@company.com",
        "body": (
            "Hi, I am expecting a baby in June and would like to understand my parental leave "
            "entitlements. Could you share the current parental leave policy and let me know "
            "what documentation I need to submit? Thank you."
        ),
        "timestamp": "2024-03-15 08:30:00",
        "expected_classification": "normal",
        "expected_department": "HR",
    },
    {
        "email_id": "r003",
        "subject": "Invoice #INV-2024-891 — Payment Confirmation Needed",
        "sender": "billing@supplierxyz.com",
        "body": (
            "Dear Accounts Team, invoice #INV-2024-891 for $24,500 was due on March 10th and "
            "we have not received payment. This is our third reminder. Please confirm payment "
            "status or contact us immediately to avoid service interruption."
        ),
        "timestamp": "2024-03-15 09:00:00",
        "expected_classification": "urgent",
        "expected_department": "Finance",
    },
    {
        "email_id": "r004",
        "subject": "Legal Notice: Patent Infringement Claim — Immediate Response Required",
        "sender": "legal@techpatents.com",
        "body": (
            "NOTICE: Our client alleges that your product infringes on Patent US10,123,456. "
            "You are hereby required to cease and desist the infringing activity within 14 days "
            "or face litigation. Please direct all correspondence to our legal team."
        ),
        "timestamp": "2024-03-15 09:15:00",
        "expected_classification": "urgent",
        "expected_department": "Legal",
    },
    {
        "email_id": "r005",
        "subject": "Congratulations! You have won a $1,000 Amazon gift card",
        "sender": "noreply@free-prizes-2024.xyz",
        "body": (
            "You have been selected as our lucky winner! Click here to claim your $1,000 Amazon "
            "gift card. Offer expires in 24 hours. Just verify your details at our secure site. "
            "Act now before your prize expires!"
        ),
        "timestamp": "2024-03-15 09:30:00",
        "expected_classification": "low",
        "expected_department": "Spam",
    },
]

# ─────────────────────────────────────────────
# Task 3: full-triage  (Hard — 8 emails)
# Agent must classify + route all, draft replies for 2 urgent,
# and escalate 1 legal issue.
# ─────────────────────────────────────────────
TRIAGE_EMAILS = [
    {
        "email_id": "t001",
        "subject": "ALERT: Payment gateway down — transactions failing",
        "sender": "monitoring@company.com",
        "body": (
            "CRITICAL: Our payment gateway has been throwing errors for the last 20 minutes. "
            "All checkout transactions are failing. Estimated revenue loss: $5,000/minute. "
            "Engineering please investigate and restore service immediately."
        ),
        "timestamp": "2024-03-15 07:00:00",
        "expected_classification": "urgent",
        "expected_department": "Support",
        "requires_reply": True,
        "requires_escalation": False,
        "reply_keywords": ["team", "investigating", "update", "resolve", "working"],
    },
    {
        "email_id": "t002",
        "subject": "RE: Q1 Budget Approval — Final Numbers",
        "sender": "cfo@company.com",
        "body": (
            "Hi, attached are the final Q1 budget numbers for your review. Please sign off "
            "by Thursday so we can submit to the board. Let me know if you have any questions."
        ),
        "timestamp": "2024-03-15 07:30:00",
        "expected_classification": "normal",
        "expected_department": "Finance",
        "requires_reply": False,
        "requires_escalation": False,
        "reply_keywords": [],
    },
    {
        "email_id": "t003",
        "subject": "LEGAL: Cease and Desist — Trade Secret Misappropriation",
        "sender": "attorneys@lawfirm.com",
        "body": (
            "This letter serves as formal notice that FormerEmployee, now working at your company, "
            "has misappropriated confidential trade secrets from our client. We demand you immediately "
            "cease using this information. Failure to comply will result in emergency injunctive relief. "
            "Respond within 72 hours."
        ),
        "timestamp": "2024-03-15 08:00:00",
        "expected_classification": "urgent",
        "expected_department": "Legal",
        "requires_reply": False,
        "requires_escalation": True,
    },
    {
        "email_id": "t004",
        "subject": "New Employee Onboarding Checklist",
        "sender": "hr@company.com",
        "body": (
            "Please find attached the onboarding checklist for our new hire starting Monday. "
            "Please ensure workstation setup, system access, and welcome kit are ready by Friday."
        ),
        "timestamp": "2024-03-15 08:30:00",
        "expected_classification": "normal",
        "expected_department": "HR",
        "requires_reply": False,
        "requires_escalation": False,
        "reply_keywords": [],
    },
    {
        "email_id": "t005",
        "subject": "Server outage — main application unresponsive for 45 minutes",
        "sender": "devops@company.com",
        "body": (
            "The main application server (app-prod-01) has been unresponsive for 45 minutes. "
            "Health checks are failing. Auto-scaling has kicked in but not resolved the issue. "
            "We need immediate senior engineering involvement to diagnose and fix this."
        ),
        "timestamp": "2024-03-15 09:00:00",
        "expected_classification": "urgent",
        "expected_department": "Support",
        "requires_reply": True,
        "requires_escalation": False,
        "reply_keywords": ["escalat", "senior", "team", "investigating", "working", "resolve"],
    },
    {
        "email_id": "t006",
        "subject": "Special Offer: 50% off Premium Subscription — Today Only!",
        "sender": "offers@spamsite.com",
        "body": (
            "Don't miss out! Get our premium subscription at 50% off today only. "
            "Click the link below to unlock exclusive benefits. Limited time offer!"
        ),
        "timestamp": "2024-03-15 09:30:00",
        "expected_classification": "low",
        "expected_department": "Spam",
        "requires_reply": False,
        "requires_escalation": False,
        "reply_keywords": [],
    },
    {
        "email_id": "t007",
        "subject": "Annual Performance Review Schedule — Please Confirm Availability",
        "sender": "hr@company.com",
        "body": (
            "Dear team, annual performance reviews are scheduled for April 1-5. "
            "Please confirm your availability by replying to this email."
        ),
        "timestamp": "2024-03-15 10:00:00",
        "expected_classification": "normal",
        "expected_department": "HR",
        "requires_reply": False,
        "requires_escalation": False,
        "reply_keywords": [],
    },
    {
        "email_id": "t008",
        "subject": "Partnership Proposal from Horizon Tech — Strategic Alliance",
        "sender": "ceo@horizontech.com",
        "body": (
            "Hi, Horizon Tech is proposing a strategic partnership to co-develop AI solutions. "
            "We believe synergies could be worth $2M annually. Can we schedule a call next week "
            "to discuss further?"
        ),
        "timestamp": "2024-03-15 10:30:00",
        "expected_classification": "normal",
        "expected_department": "Finance",
        "requires_reply": False,
        "requires_escalation": False,
        "reply_keywords": [],
    },
]


def get_task_emails(task_name: str):
    """Return the email list for a given task (no expected_ fields exposed to agent)."""
    data_map = {
        "classify-urgency": CLASSIFY_EMAILS,
        "route-emails": ROUTE_EMAILS,
        "full-triage": TRIAGE_EMAILS,
    }
    raw = data_map.get(task_name, [])
    # Strip internal grading fields before exposing to agent
    public_keys = {"email_id", "subject", "sender", "body", "timestamp"}
    return [{k: v for k, v in email.items() if k in public_keys} for email in raw]


def get_ground_truth(task_name: str):
    """Return the full data including expected fields (for graders)."""
    data_map = {
        "classify-urgency": CLASSIFY_EMAILS,
        "route-emails": ROUTE_EMAILS,
        "full-triage": TRIAGE_EMAILS,
    }
    return data_map.get(task_name, [])
