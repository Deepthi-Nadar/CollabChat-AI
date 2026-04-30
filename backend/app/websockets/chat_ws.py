import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.database import SessionLocal
from app.models.message import Message
from app.models.user import User
from app.services.ai_service import create_ai_response


router = APIRouter(tags=["websockets"])

chat_rooms: dict[str, list[WebSocket]] = defaultdict(list)
ai_rooms: dict[str, list[WebSocket]] = defaultdict(list)
ai_locks: dict[str, str | None] = defaultdict(lambda: None)


def generate_room_id(user1: str | int, user2: str | int) -> str:
    return "_".join(sorted([str(user1), str(user2)]))


def get_ws_user(websocket: WebSocket) -> dict | None:
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


async def broadcast(room: list[WebSocket], message: dict):
    disconnected = []
    for connection in room:
        try:
            await connection.send_json(message)
        except RuntimeError:
            disconnected.append(connection)

    for connection in disconnected:
        if connection in room:
            room.remove(connection)


def save_message(sender_id: int, receiver_id: int, content: str, message_type: str = "text") -> Message:
    db = SessionLocal()
    try:
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    finally:
        db.close()


def user_exists(user_id: int) -> bool:
    db = SessionLocal()
    try:
        return db.get(User, user_id) is not None
    finally:
        db.close()


@router.websocket("/ws/chat/{target_user_id}")
async def websocket_chat(websocket: WebSocket, target_user_id: int):
    user = get_ws_user(websocket)
    if not user or not user_exists(target_user_id):
        await websocket.close(code=1008)
        return

    current_user_id = int(user["user_id"])
    current_username = user.get("username", str(current_user_id))
    room_id = generate_room_id(current_user_id, target_user_id)
    room = chat_rooms[room_id]

    await websocket.accept()
    room.append(websocket)
    await broadcast(room, {"type": "presence", "room_id": room_id, "user_id": current_user_id, "online": True})

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except json.JSONDecodeError:
                payload = {"type": "chat_message", "message": raw_data}

            event_type = payload.get("type", "chat_message")
            content = str(payload.get("message", "")).strip()

            if event_type == "typing":
                await broadcast(
                    room,
                    {
                        "type": "typing",
                        "user_id": current_user_id,
                        "username": current_username,
                        "is_typing": bool(payload.get("is_typing", True)),
                    },
                )
                continue

            if not content:
                continue

            if content.lower().startswith("@ai"):
                prompt = content[3:].strip()
                await broadcast(
                    room,
                    {
                        "type": "ai_prompt",
                        "room_id": room_id,
                        "user_id": current_user_id,
                        "username": current_username,
                        "prompt": prompt,
                    },
                )
                continue

            message = save_message(
                sender_id=current_user_id,
                receiver_id=target_user_id,
                content=content,
                message_type=str(payload.get("message_type", "text")),
            )
            await broadcast(
                room,
                {
                    "type": "chat_message",
                    "id": message.id,
                    "room_id": room_id,
                    "user_id": current_user_id,
                    "sender_id": current_user_id,
                    "receiver_id": target_user_id,
                    "username": current_username,
                    "message": message.content,
                    "message_type": message.message_type,
                    "timestamp": message.timestamp.isoformat(),
                },
            )
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in room:
            room.remove(websocket)
        await broadcast(room, {"type": "presence", "room_id": room_id, "user_id": current_user_id, "online": False})


@router.websocket("/ws/ai/{room_id}")
async def websocket_ai(websocket: WebSocket, room_id: str):
    user = get_ws_user(websocket)
    if not user:
        await websocket.close(code=1008)
        return

    current_user_id = str(user["user_id"])
    current_username = user.get("username", current_user_id)
    room = ai_rooms[room_id]

    await websocket.accept()
    room.append(websocket)
    await websocket.send_json({"type": "lock_status", "locked_by": ai_locks[room_id]})

    try:
        while True:
            payload = json.loads(await websocket.receive_text())
            prompt = str(payload.get("prompt", "")).strip()
            if payload.get("type") != "ai_query" or not prompt:
                continue

            if ai_locks[room_id] and ai_locks[room_id] != current_user_id:
                await websocket.send_json(
                    {
                        "type": "ai_busy",
                        "locked_by": ai_locks[room_id],
                        "message": "Another user is typing for AI.",
                    }
                )
                continue

            ai_locks[room_id] = current_user_id
            await broadcast(
                room,
                {
                    "type": "ai_typing",
                    "user_id": current_user_id,
                    "username": current_username,
                    "is_typing": True,
                    "message": f"{current_username} is typing for AI...",
                },
            )

            await asyncio.sleep(0.2)
            response = create_ai_response(prompt)
            await broadcast(
                room,
                {
                    "type": "ai_response",
                    "user_id": current_user_id,
                    "username": current_username,
                    "prompt": prompt,
                    "response": response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            ai_locks[room_id] = None
            await broadcast(room, {"type": "ai_typing", "is_typing": False, "message": ""})
            await broadcast(room, {"type": "lock_status", "locked_by": None})
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in room:
            room.remove(websocket)
        if ai_locks[room_id] == current_user_id:
            ai_locks[room_id] = None
            await broadcast(room, {"type": "lock_status", "locked_by": None})
