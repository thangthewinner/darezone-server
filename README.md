# DareZone Backend

FastAPI backend for DareZone - A habit-building social application (B2C).

## Quick Start

```bash
# 1. Setup environment
cd darezone-server
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
# Edit .env with your Supabase credentials

# 4. Run server
python main.py
```

Server runs at: `http://localhost:8000`

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Reference:** See [API_DOCS.md](API_DOCS.md)

## Project Structure

```
darezone-server/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/                # Config, security, dependencies
│   ├── api/v1/              # API endpoints
│   ├── schemas/             # Pydantic models
│   ├── services/            # Business logic
│   └── middleware/          # Custom middleware
├── tests/                   # Test suite
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── main.py                  # Entry point
```

## Environment Variables

Required in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Development

```bash
# Run tests
pytest

# Format code
black app tests

# Type checking
mypy app
```

## Features

✅ **Phase 1 & 2 Complete:**
- User authentication (Supabase)
- Challenge management
- Daily check-ins
- Friendship system
- Notifications
- Media upload
- Hitch reminders
- Stats & history

## Tech Stack

- **Framework:** FastAPI 0.104+
- **Database:** Supabase PostgreSQL
- **Auth:** Supabase Auth (JWT)
- **Python:** 3.11+
