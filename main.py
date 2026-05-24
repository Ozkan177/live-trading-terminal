from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import yfinance as ticker_api
import json

app = FastAPI(title="Canlı Trading Terminali Backend API")

# Frontend bağlantılarına izin vermek için CORS ayarı
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Aktif WebSocket bağlantılarını yönetmek için sınıf
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Arka planda sürekli çalışıp veri çeken ve yayınlayan asenkron fonksiyon
async def fetch_live_data_stream():
    # İlk aşamada test için küresel/bölgesel bir hisse veya varlık listesi
    tickers = ["AAPL", "MSFT", "BTC-USD"]
    while True:
        try:
            for ticker in tickers:
                # Yahoo Finance üzerinden anlık fiyatı simüle etmek için veri çekiyoruz
                data = ticker_api.Ticker(ticker)
                todays_data = data.history(period='1d')
                
                if not todays_data.empty:
                    latest_price = todays_data['Close'].iloc[-1]
                    volume = todays_data['Volume'].iloc[-1]
                    
                    payload = {
                        "ticker": ticker,
                        "price": round(latest_price, 2),
                        "volume": int(volume),
                        "status": "success"
                    }
                    
                    # Bağlı olan tüm tarayıcılara/ekranlara veriyi canlı fırlat
                    await manager.broadcast(json.dumps(payload))
            
            # Sunucuyu yormamak ve API sınırlarına takılmamak için saniyelik bekleme
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Veri çekme hatası: {e}")
            await asyncio.sleep(5)

# Backend ayağa kalktığında veri akışını arka planda otomatik başlat
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_live_data_stream())

@app.get("/")
def read_root():
    return {"message": "Canlı Trading Terminali Backend Aktif!"}

# Frontend'in canlı grafikleri besleyeceği WebSocket kanalı
@websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # İstemciden gelebilecek mesajları (örn: hisse değiştirme talebi) dinle
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)