# CollabChat AI

CollabChat AI is a full-stack real-time chat application with a shared AI workspace. Users can register, log in, search for other users, chat one-to-one over WebSockets, see typing indicators, and collaborate with an AI assistant inside a shared panel using `@ai`.

The AI panel can generate code, explanations, project files, and other responses. When the AI returns named code blocks such as `index.html`, `style.css`, or `server.js`, the frontend shows separate download buttons for each file.

## Features

- User registration and login with JWT authentication
- Password hashing with bcrypt
- User search
- One-to-one real-time chat with WebSockets
- Persistent chat history with SQLite and SQLAlchemy
- Typing indicators
- Shared AI panel per chat room
- AI lock system so only one user queries AI at a time
- OpenAI-powered AI responses
- Separate download buttons for AI-generated files
- Responsive React UI with dark mode
- Deployment-ready config for Render and Vercel

## Tech Stack

**Frontend**

- React
- Vite
- Axios
- Native WebSocket API
- CSS
- lucide-react icons

**Backend**

- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- JWT auth with `python-jose`
- OpenAI Python SDK
- WebSockets

## Project Structure

```text
collabchat-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── websockets/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── render.yaml
├── DEPLOYMENT.md
└── README.md
```

## Local Setup

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Update `backend/.env`:

```env
SECRET_KEY=your-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./collabchat.db
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=3500
```

Run the backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

### 2. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm.cmd run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## How To Use

1. Register two users, for example `alice` and `bob`.
2. Log in as one user.
3. Search for the other user in the sidebar.
4. Open the chat and send messages.
5. Open another browser/incognito window and log in as the second user.
6. Type `@ai` followed by a prompt, for example:

```text
@ai Make an Express.js API with login route
```

The AI response appears in the shared AI panel. If the response contains named files, download buttons appear automatically.

## Environment Variables

### Backend

```env
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./collabchat.db
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=3500
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### Frontend

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

## Deployment

Recommended deployment:

- Backend: Render
- Frontend: Vercel

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

## Security Notes

- Do not commit `backend/.env`.
- Do not put real API keys in `.env.example`.
- Rotate any API key that was accidentally committed or pasted publicly.
- Set `ALLOWED_ORIGINS` to your deployed frontend URL in production.

## License

This project is for learning and portfolio use. Add a license file if you plan to distribute it publicly.
