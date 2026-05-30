# 🎫 Support CRM — Customer Ticketing System

A full-stack customer support ticketing system built with **Python + FastAPI**, **SQLite**, and **vanilla HTML/JS/Tailwind CSS**.

Built as part of the Datastraw Technologies Internship Assessment.

---

## 🚀 Live Demo

> [Add your Railway URL here after deployment]

---

## 📸 Features

| Feature | Description |
|---|---|
| ✅ Create Tickets | Customer name, email, subject, description, priority |
| ✅ List All Tickets | Clean list with ID, name, status, priority, date |
| ✅ Search | Live search across name, email, subject, ID, description |
| ✅ Filter by Status | Open / In Progress / Closed |
| ✅ Filter by Priority | High / Medium / Low |
| ✅ View & Update | Full detail view with status update + notes |
| ✅ Notes/Comments | Add timestamped notes to any ticket |
| ✅ Stats Dashboard | Summary cards showing ticket counts |
| ✅ Delete Tickets | Remove tickets and their notes |
| ✅ Keyboard Shortcuts | Press `N` for new ticket, `Esc` to close modals |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11 + FastAPI
- **Database:** SQLite (file-based, zero config)
- **Frontend:** HTML + Tailwind CSS + Vanilla JavaScript
- **Deploy:** Railway.app

---

## 🏗️ Project Structure

```
support-crm/
├── main.py          # FastAPI app — all routes & business logic
├── database.py      # SQLite connection & table creation
├── models.py        # Pydantic data models (request/response validation)
├── requirements.txt # Python dependencies
├── railway.toml     # Railway deployment config
├── .env.example     # Environment variable template
├── .gitignore       # Files excluded from Git
└── static/
    └── index.html   # Entire frontend (SPA with vanilla JS)
```

---

## ⚙️ Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/support-crm.git
cd support-crm
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env if needed (defaults work fine for local dev)
```

### 5. Run the server
```bash
python main.py
# OR
uvicorn main:app --reload
```

### 6. Open the app
- **Frontend:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/tickets` | Create a new ticket |
| `GET` | `/api/tickets` | List tickets (search/filter via query params) |
| `GET` | `/api/tickets/{ticket_id}` | Get full ticket + notes |
| `PUT` | `/api/tickets/{ticket_id}` | Update status and/or add note |
| `DELETE` | `/api/tickets/{ticket_id}` | Delete a ticket |
| `GET` | `/api/stats` | Get summary statistics |

### Query Parameters for GET /api/tickets
- `?search=john` — search across name, email, subject, description, ID
- `?status=Open` — filter by status (Open, In Progress, Closed)
- `?priority=High` — filter by priority (High, Medium, Low)
- Combine: `?status=Open&search=billing&priority=High`

---

## 🚢 Deployment (Railway.app)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects Python and uses `railway.toml` for the start command
5. Add environment variable: `DATABASE_PATH=support_crm.db`
6. Done! Railway gives you a public URL.

---

## 🗄️ Database Schema

```sql
-- Tickets table
CREATE TABLE tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id      TEXT UNIQUE NOT NULL,     -- e.g. TKT-001
    customer_name  TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    subject        TEXT NOT NULL,
    description    TEXT NOT NULL,
    status         TEXT DEFAULT 'Open',       -- Open | In Progress | Closed
    priority       TEXT DEFAULT 'Medium',     -- Low | Medium | High
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- Notes table
CREATE TABLE notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  TEXT NOT NULL REFERENCES tickets(ticket_id),
    note_text  TEXT NOT NULL,
    author     TEXT DEFAULT 'Support Agent',
    created_at TEXT NOT NULL
);
```

---

## 🤔 Architecture Decisions

1. **SQLite over PostgreSQL** — Zero setup, file-based, perfect for this scale. Railway persists it fine.
2. **Vanilla JS over React** — Keeps it simple. No build step, no bundler, just one HTML file.
3. **FastAPI over Flask** — Auto-generates Swagger docs, built-in Pydantic validation, async-ready.
4. **Relative API URLs** — Frontend calls `/api/...` not `http://localhost:8000/api/...`, so it works on any domain after deployment.

---

## 💡 If I Had More Time

- Add user authentication (login/logout)
- Email notifications when tickets are created/updated
- CSV export for tickets
- Ticket assignment to specific agents
- Real-time updates via WebSockets

---

## 👨‍💻 Built by

[Your Name] — [Your Email]