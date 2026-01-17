from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Crypto ML Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

@app.get("/")
async def root():
    return {"message": "Crypto ML Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/indicators/{symbol}")
async def get_indicators(symbol: str):
    taapi_key = os.getenv("TAAPI_API_KEY")
    if not taapi_key:
        return {"error": "TAAPI API key not configured"}
    
    async with aiohttp.ClientSession() as session:
        url = f"https://api.taapi.io/rsi?secret={taapi_key}&exchange=binance&symbol={symbol}/USDT&interval=5m"
        async with session.get(url) as response:
            rsi_data = await response.json()
            return {"symbol": symbol, "indicators": {"rsi": rsi_data.get("value")}}

@app.websocket("/ws/price")
async def websocket_price(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"message": "Echo: " + data})
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
