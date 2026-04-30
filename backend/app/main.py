from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.messages import router as messages_router
from app.api.users import router as users_router
from app.db.database import Base, engine
from app.models import Message, User
from app.websockets.chat_ws import router as websocket_router


load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CollabChat AI API")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(messages_router)
app.include_router(ai_router)
app.include_router(websocket_router)


@app.get("/")
def home():
    return {"message": "CollabChat AI backend running"}
