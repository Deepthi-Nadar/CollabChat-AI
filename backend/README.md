# CollabChat AI Backend

FastAPI backend for auth, user search, persistent chat history, chat WebSockets, shared AI panel WebSockets, and a mock AI endpoint.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `SECRET_KEY` in `.env` before deploying.

## Run

```powershell
uvicorn app.main:app --reload
```

API docs are available at `http://127.0.0.1:8000/docs`.

## Main Routes

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /users/search?query=...`
- `GET /messages/{other_user_id}`
- `POST /ai-query`
- `WS /ws/chat/{target_user_id}?token=...`
- `WS /ws/ai/{room_id}?token=...`

The default AI implementation is deterministic mock output. Replace `app/services/ai_service.py` with a real OpenAI call when you are ready to wire in model responses.
