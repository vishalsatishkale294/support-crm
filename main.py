"""
main.py — FastAPI application entry point.

FastAPI auto-generates interactive docs at /docs (Swagger UI).
Visit http://localhost:8000/docs to test your API visually!
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional
import os

from database import get_db, init_db
from models import (
    CreateTicketRequest, UpdateTicketRequest,
    TicketListItem, TicketDetail, NoteResponse
)

# APP SETUP

app = FastAPI(
    title="Support CRM API",
    description="Customer Support Ticketing System built with FastAPI + SQLite",
    version="1.0.0"
)

# CORS - allows your frontend (even on a different domain) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, replace * with your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static folder (our HTML frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


# STARTUP

@app.on_event("startup")
def startup_event():
    """Runs once when the server starts — creates DB tables if needed."""
    init_db()


# HELPER FUNCTIONS 

def now_iso() -> str:
    """Returns current UTC time as ISO string e.g. 2025-01-15T10:30:00Z"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_ticket_id(conn) -> str:
    """
    Generates the next ticket ID like TKT-001, TKT-002, etc.
    Counts existing tickets and increments by 1.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM tickets")
    count = cursor.fetchone()["total"]
    return f"TKT-{str(count + 1).zfill(3)}"   # zfill(3) → pads to 3 digits


def row_to_dict(row) -> dict:
    """Converts a sqlite3.Row object to a plain Python dict."""
    return dict(row)


# ROUTES

@app.get("/")
def serve_frontend():
    """Serves the main HTML page at the root URL."""
    return FileResponse("static/index.html")


# 1.CREATE TICKET 

@app.post("/api/tickets", status_code=201)
def create_ticket(body: CreateTicketRequest):
    """
    POST /api/tickets
    Creates a new support ticket.
    Returns the new ticket_id and timestamp.
    """
    conn = get_db()
    try:
        ts = now_iso()
        ticket_id = generate_ticket_id(conn)

        conn.execute("""
            INSERT INTO tickets
                (ticket_id, customer_name, customer_email, subject, description,
                 status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'Open', ?, ?, ?)
        """, (
            ticket_id,
            body.customer_name.strip(),
            body.customer_email.strip().lower(),
            body.subject.strip(),
            body.description.strip(),
            body.priority,
            ts, ts
        ))
        conn.commit()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "created_at": ts,
            "message": f"Ticket {ticket_id} created successfully!"
        }
    finally:
        conn.close()  # Always close the connection


# 2.LIST TICKETS (with search + filter)

@app.get("/api/tickets")
def list_tickets(
    status: Optional[str] = Query(None, description="Filter: Open | In Progress | Closed"),
    search: Optional[str] = Query(None, description="Search name, email, subject, ID"),
    priority: Optional[str] = Query(None, description="Filter: Low | Medium | High"),
    limit: int = Query(100, description="Max tickets to return"),
    offset: int = Query(0, description="Pagination offset")
):
    conn = get_db()
    try:
        # Build query dynamically based on filters provided
        sql = "SELECT * FROM tickets WHERE 1=1"
        params = []

        if status:
            sql += " AND LOWER(status) = LOWER(?)"
            params.append(status)

        if priority:
            sql += " AND LOWER(priority) = LOWER(?)"
            params.append(priority)

        if search:
            # Search across multiple columns using LIKE
            sql += """ AND (
                LOWER(customer_name)  LIKE LOWER(?) OR
                LOWER(customer_email) LIKE LOWER(?) OR
                LOWER(subject)        LIKE LOWER(?) OR
                LOWER(ticket_id)      LIKE LOWER(?) OR
                LOWER(description)    LIKE LOWER(?)
            )"""
            term = f"%{search}%"
            params.extend([term, term, term, term, term])

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Count total for pagination info
        count_sql = sql.replace("SELECT *", "SELECT COUNT(*)", 1)
        count_sql = count_sql[:count_sql.rfind("ORDER BY")]  # Remove ORDER/LIMIT
        count_sql = count_sql + " ORDER BY created_at DESC"
        cursor.execute(count_sql.replace(" LIMIT ? OFFSET ?", ""),
                       params[:-2] if params else [])

        return {
            "tickets": [row_to_dict(r) for r in rows],
            "count": len(rows)
        }
    finally:
        conn.close()


# 3.GET SINGLE TICKET (with notes)

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    """
    GET /api/tickets/TKT-001
    Returns full ticket details including all notes.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Fetch the ticket
        cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
        ticket = cursor.fetchone()

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        # Fetch associated notes
        cursor.execute(
            "SELECT * FROM notes WHERE ticket_id = ? ORDER BY created_at ASC",
            (ticket_id,)
        )
        notes = cursor.fetchall()

        result = row_to_dict(ticket)
        result["notes"] = [row_to_dict(n) for n in notes]
        return result

    finally:
        conn.close()


# 4.UPDATE TICKET

@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: UpdateTicketRequest):
    """
    PUT /api/tickets/TKT-001
    Update status and/or add a note.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Make sure ticket exists
        cursor.execute("SELECT id FROM tickets WHERE ticket_id = ?", (ticket_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        ts = now_iso()

        # Update status if provided
        if body.status:
            valid_statuses = ["Open", "In Progress", "Closed"]
            if body.status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Choose from: {valid_statuses}"
                )
            conn.execute(
                "UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?",
                (body.status, ts, ticket_id)
            )

        # Add note if provided
        if body.note_text and body.note_text.strip():
            conn.execute("""
                INSERT INTO notes (ticket_id, note_text, author, created_at)
                VALUES (?, ?, ?, ?)
            """, (ticket_id, body.note_text.strip(), body.author, ts))
            # Also update the ticket's updated_at
            conn.execute(
                "UPDATE tickets SET updated_at = ? WHERE ticket_id = ?",
                (ts, ticket_id)
            )

        conn.commit()
        return {"success": True, "updated_at": ts}

    finally:
        conn.close()


# 5.DELETE TICKET

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str):
    """
    DELETE /api/tickets/TKT-001
    Removes a ticket and all its notes. (Bonus feature!)
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tickets WHERE ticket_id = ?", (ticket_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        conn.execute("DELETE FROM notes WHERE ticket_id = ?", (ticket_id,))
        conn.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
        conn.commit()

        return {"success": True, "message": f"Ticket {ticket_id} deleted"}
    finally:
        conn.close()


# 6.STATS ENDPOINT

@app.get("/api/stats")
def get_stats():
    """
    GET /api/stats
    Returns ticket counts by status — used for the dashboard summary cards.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_priority
            FROM tickets
        """)
        row = cursor.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


#RUN (for local development)

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run with reload=True → auto-restarts when you save a file
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)