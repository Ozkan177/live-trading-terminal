import yfinance as yf
import pandas as pd
import json
import os
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR

# --- YAHOO ENGELİNİ AŞMAK İÇİN TARAYICI KİMLİĞİ (USER-AGENT) ---
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})

def load_tickers(json_name="katilim_listesi.json"):
    json_path = os.path.join(PROJECT_ROOT, json_name)
    if not os.path.exists(json_path):
        print(f"Uyarı: {json_name} bulunamadı. Varsayılan hisse listesi kullanılıyor.")
        return ["FONET.IS", "YEOTK.IS", "TUREX.IS", "ALKLC.IS"]
        
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)

def fetch_historical_data(ticker, period="5y", interval="1d"):
    print(f"📊 {ticker} verileri çekiliyor...")
    
    try:
        # Session'ı yfinance'e dahil ediyoruz
        stock = yf.Ticker(ticker, session=session)
        df = stock.history(period=period, interval=interval)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.index = df.index.tz_localize(None) 
            return df
        else:
            print(f"   [!] {ticker} için veri dönmedi (Delist olmuş veya IP banı devam ediyor).")
            return pd.DataFrame()
    except Exception as e:
        print(f"   [X] {ticker} çekilirken hata oluştu: {e}")
        return pd.DataFrame()

def save_raw_data():
    tickers = load_tickers()
    save_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    os.makedirs(save_dir, exist_ok=True)
    
    print("-" * 50)
    print("HİSSE VERİLERİ ÇEKİLİYOR (Yapay Zeka Eğitim Seti)")
    print("-" * 50)
    
    for ticker in tickers:
        df = fetch_historical_data(ticker)
        if not df.empty:
            file_name = f"{ticker.replace('.IS', '')}_raw.csv"
            file_path = os.path.join(save_dir, file_name)
            df.to_csv(file_path)
            print(f"   -> Kaydedildi: {file_name}")
        time.sleep(3) # Bot algılamasına karşı 3 saniye bekleme
    
    print("\n" + "-" * 50)
    print("🌍 Makro Ekonomik Veriler Çekiliyor (Yapay Zekanın 6. Hissi)...")
    print("-" * 50)
    
    macro_symbols = {
        "USDTRY": "TRY=X",    
        "VIX": "^VIX",        
        "GOLD": "GC=F",       
        "BIST100": "XU100.IS" 
    }
    
    macro_df = pd.DataFrame()
    
    for name, symbol in macro_symbols.items():
        print(f" ⏳ {name} ({symbol}) çekiliyor...")
        try:
            data = yf.Ticker(symbol, session=session).history(period="5y", interval="1d")
            
            if not data.empty:
                data.index = data.index.tz_localize(None)
                macro_df[name] = data['Close'] 
        except Exception as e:
             print(f"   [X] {name} hatası: {e}")
             
        time.sleep(3) 
            
    macro_df.ffill(inplace=True) 
    macro_df.dropna(inplace=True)
    
    macro_path = os.path.join(save_dir, "MACRO_raw.csv")
    macro_df.to_csv(macro_path)
    print(f"\n✅ Tüm veriler başarıyla güncellendi! Makro veriler hazır: MACRO_raw.csv")

if __name__ == "__main__":
    save_raw_data()