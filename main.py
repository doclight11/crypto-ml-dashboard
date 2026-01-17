from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto ML Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            font-size: 1rem;
            color: #888;
            margin-bottom: 10px;
        }
        .card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d2ff;
        }
        .card .change {
            font-size: 0.9rem;
            margin-top: 5px;
        }
        .positive { color: #00ff88; }
        .negative { color: #ff4757; }
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background: rgba(0,210,255,0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            background: #00ff88;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .price-list {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
        }
        .price-item {
            display: flex;
            justify-content: space-between;
            padding: 15px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .price-item:last-child { border-bottom: none; }
        .crypto-name { font-weight: bold; }
        .crypto-price { color: #00d2ff; font-weight: bold; }
        #rsi-result {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }
        button {
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
        }
        button:hover { opacity: 0.9; }
        select, input {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 10px 15px;
            border-radius: 8px;
            color: white;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Crypto ML Dashboard</h1>

        <div class="status">
            <div class="status-dot"></div>
            <span>API Status: Online</span>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Bitcoin (BTC)</h2>
                <div class="value" id="btc-price">Loading...</div>
                <div class="change positive" id="btc-change">--</div>
            </div>
            <div class="card">
                <h2>Ethereum (ETH)</h2>
                <div class="value" id="eth-price">Loading...</div>
                <div class="change positive" id="eth-change">--</div>
            </div>
            <div class="card">
                <h2>Total Market Cap</h2>
                <div class="value" id="market-cap">$2.1T</div>
                <div class="change positive">+2.4%</div>
            </div>
        </div>

        <div class="card">
            <h2>RSI Indicator Lookup</h2>
            <div style="margin-top: 15px;">
                <input type="text" id="symbol-input" placeholder="Enter symbol (e.g., BTC)" value="BTC">
                <button onclick="fetchRSI()">Get RSI</button>
            </div>
            <div id="rsi-result"></div>
        </div>

        <div class="price-list" style="margin-top: 20px;">
            <h2 style="margin-bottom: 15px; color: #888;">Top Cryptocurrencies</h2>
            <div class="price-item">
                <span class="crypto-name">Bitcoin</span>
                <span class="crypto-price" id="list-btc">--</span>
            </div>
            <div class="price-item">
                <span class="crypto-name">Ethereum</span>
                <span class="crypto-price" id="list-eth">--</span>
            </div>
            <div class="price-item">
                <span class="crypto-name">Solana</span>
                <span class="crypto-price" id="list-sol">--</span>
            </div>
            <div class="price-item">
                <span class="crypto-name">Cardano</span>
                <span class="crypto-price" id="list-ada">--</span>
            </div>
        </div>
    </div>

    <script>
        async function fetchPrices() {
            try {
                const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,cardano&vs_currencies=usd&include_24hr_change=true');
                const data = await response.json();

                document.getElementById('btc-price').textContent = '$' + data.bitcoin.usd.toLocaleString();
                document.getElementById('eth-price').textContent = '$' + data.ethereum.usd.toLocaleString();
                document.getElementById('list-btc').textContent = '$' + data.bitcoin.usd.toLocaleString();
                document.getElementById('list-eth').textContent = '$' + data.ethereum.usd.toLocaleString();
                document.getElementById('list-sol').textContent = '$' + data.solana.usd.toLocaleString();
                document.getElementById('list-ada').textContent = '$' + data.cardano.usd.toLocaleString();

                const btcChange = data.bitcoin.usd_24h_change.toFixed(2);
                const ethChange = data.ethereum.usd_24h_change.toFixed(2);
                document.getElementById('btc-change').textContent = (btcChange >= 0 ? '+' : '') + btcChange + '%';
                document.getElementById('btc-change').className = 'change ' + (btcChange >= 0 ? 'positive' : 'negative');
                document.getElementById('eth-change').textContent = (ethChange >= 0 ? '+' : '') + ethChange + '%';
                document.getElementById('eth-change').className = 'change ' + (ethChange >= 0 ? 'positive' : 'negative');
            } catch (error) {
                console.error('Error fetching prices:', error);
            }
        }

        async function fetchRSI() {
            const symbol = document.getElementById('symbol-input').value.toUpperCase();
            const resultDiv = document.getElementById('rsi-result');
            resultDiv.innerHTML = 'Loading...';

            try {
                const response = await fetch('/api/indicators/' + symbol);
                const data = await response.json();

                if (data.error) {
                    resultDiv.innerHTML = '<span style="color: #ff4757;">Error: ' + data.error + '</span>';
                } else {
                    const rsi = data.indicators?.rsi || 'N/A';
                    let rsiColor = '#00d2ff';
                    let rsiStatus = 'Neutral';
                    if (rsi !== 'N/A') {
                        if (rsi > 70) { rsiColor = '#ff4757'; rsiStatus = 'Overbought'; }
                        else if (rsi < 30) { rsiColor = '#00ff88'; rsiStatus = 'Oversold'; }
                    }
                    resultDiv.innerHTML = '<strong>' + symbol + ' RSI:</strong> <span style="color: ' + rsiColor + '; font-size: 1.5rem;">' + (typeof rsi === 'number' ? rsi.toFixed(2) : rsi) + '</span> <span style="color: #888;">(' + rsiStatus + ')</span>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<span style="color: #ff4757;">Error fetching RSI</span>';
            }
        }

        fetchPrices();
        setInterval(fetchPrices, 30000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return DASHBOARD_HTML

@app.get("/api/status")
async def api_status():
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
            for connection in active_connections:
                await connection.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
