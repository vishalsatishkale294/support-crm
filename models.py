"""
models.py — Data models using Pydantic.

Pydantic validates data automatically.
Example: If customer_email is missing, FastAPI returns a 422 error before your code even runs.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ── REQUEST MODELS (what the client SENDS to us) ──────────────────────────────

class CreateTicketRequest(BaseModel):
    """Used for POST /api/tickets"""
    customer_name: str
    customer_email: str          # Basic string — EmailStr needs extra package
    subject: str
    description: str
    priority: Optional[str] = "Medium"   # Default priority if not provided


class UpdateTicketRequest(BaseModel):
    """Used for PUT /api/tickets/{ticket_id}"""
    status: Optional[str] = None        # Can update status, note, or both
    note_text: Optional[str] = None
    author: Optional[str] = "Support Agent"


# ── RESPONSE MODELS (what we SEND back to the client) ─────────────────────────

class NoteResponse(BaseModel):
    """A single note/comment on a ticket"""
    id: int
    ticket_id: str
    note_text: str
    author: str
    created_at: str


class TicketListItem(BaseModel):
    """Lightweight — used in the list view (no notes, no full description)"""
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    status: str
    priority: str
    created_at: str
    updated_at: str


class TicketDetail(BaseModel):
    """Full ticket with notes — used in the detail view"""
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    notes: List[NoteResponse] = []