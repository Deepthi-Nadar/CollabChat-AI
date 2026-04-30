from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("➡️ WS HIT")
    await websocket.accept()
    print("✅ CONNECTED")

    while True:
        data = await websocket.receive_text()
        print("Message:", data)
        await websocket.send_text(f"Echo: {data}")