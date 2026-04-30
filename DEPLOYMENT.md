# Deploy CollabChat AI

This project deploys as two services:

- Backend: FastAPI on Render
- Frontend: Vite React on Vercel

## Before Deploying

Do not commit secrets. Keep real keys only in platform environment variables.

Required backend environment variables:

```env
SECRET_KEY=use-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./collabchat.db
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=3500
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

Required frontend environment variables:

```env
VITE_API_URL=https://your-backend-domain.onrender.com
VITE_WS_URL=wss://your-backend-domain.onrender.com
```

## Backend on Render

1. Push this repo to GitHub.
2. In Render, create a new Web Service from the repo.
3. Set Root Directory to `backend`.
4. Use:

```text
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Add the backend environment variables above.
6. Deploy.

After deploy, test:

```text
https://your-backend-domain.onrender.com/
```

## Frontend on Vercel

1. Import the same GitHub repo in Vercel.
2. Set Root Directory to `frontend`.
3. Use:

```text
Build Command: npm run build
Output Directory: dist
```

4. Add `VITE_API_URL` and `VITE_WS_URL`.
5. Deploy.

## Final Step

After Vercel gives you a frontend URL, go back to Render and set:

```env
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

Redeploy the backend once after changing that variable.
