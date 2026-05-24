from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import yfinance as ticker_api
import json
from sqlalchemy.orm import Session

# Veritabanı modüllerimizi içe aktarıyoruz
import models
from database import engine, SessionLocal

# Veritabanı tablolarını oluştur (Eğer yoksa)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Canlı Trading Terminali Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Arka planda veriyi çekip veritabanına KAYDEDEN fonksiyon
# SADECE BU FONKSİYONU DEĞİŞTİRİYORUZ
async def fetch_live_data_stream():
    tickers = ["AAPL", "MSFT", "BTC-USD"]
    while True:
        db = SessionLocal()
        try:
            for ticker in tickers:
                try:
                    data = ticker_api.Ticker(ticker)
                    todays_data = data.history(period='1d')
                    
                    if not todays_data.empty:
                        latest_price = todays_data['Close'].iloc[-1]
                        volume = todays_data['Volume'].iloc[-1]
                        
                        # 1. Veritabanına Kayıt İşlemi
                        db_record = models.StockPrice(
                            ticker=ticker, 
                            price=round(float(latest_price), 2), 
                            volume=int(volume)
                        )
                        db.add(db_record)
                        db.commit()
                        
                        # 2. Canlı Yayın (WebSocket) İşlemi
                        payload = {
                            "ticker": ticker,
                            "price": round(float(latest_price), 2),
                            "volume": int(volume),
                            "status": "success"
                        }
                        await manager.broadcast(json.dumps(payload))
                except Exception as inner_e:
                    # Tek bir hissede sorun çıkarsa sistemi çökertme, pas geç
                    print(f"{ticker} verisi çekilirken hata: {inner_e}")
            
            # Yahoo Finance bizi bot sanıp engellemesin diye süreyi 15 saniyeye çıkardık
            await asyncio.sleep(15)
        except Exception as e:
            print(f"Genel veri çekme hatası: {e}")
            await asyncio.sleep(15)
        finally:
            db.close()

 
            
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_live_data_stream())

@app.get("/")
def read_root():
    return {"message": "Canlı Trading Terminali Aktif! Veriler kaydediliyor..."}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)