import pandas as pd
import pandas_ta as ta
import yfinance as yf
import joblib
import os
import warnings
warnings.filterwarnings("ignore") # Sıkıcı Pandas uyarılarını gizle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")

# Bellekte yüklü modelleri tutacağımız sözlük
loaded_models = {}

def load_all_models():
    """Klasördeki tüm XGBoost modellerini RAM'e yükler."""
    if not os.path.exists(MODEL_DIR):
        return
        
    for filename in os.listdir(MODEL_DIR):
        if filename.endswith("_xgboost.pkl"):
            ticker = filename.replace("_xgboost.pkl", "")
            filepath = os.path.join(MODEL_DIR, filename)
            loaded_models[ticker] = joblib.load(filepath)
            print(f"🧠 [AI] {ticker} modeli canlı sistem için belleğe alındı.")

def predict_live_signal(ticker):
    """Gelen canlı hisse için anlık indikatörleri hesaplayıp AI'a sorar."""
    if ticker not in loaded_models:
        return "MODEL_YOK"
        
    model = loaded_models[ticker]
    
    try:
        yahoo_ticker = f"{ticker}.IS"
        df = yf.download(yahoo_ticker, period="1y", interval="1d", progress=False)
        
        if df.empty:
            return "VERI_HATASI"
            
        # 🔥 KRİTİK DÜZELTME: yfinance kütüphanesinin oluşturduğu MultiIndex (Çift Katmanlı) 
        # sütun yapısını pandas-ta'nın anlayacağı tek katmanlı (Single Index) yapıya düzleştiriyoruz.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # İndikatörleri on-the-fly (anında) hesapla
        df.ta.sma(length=10, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.macd(append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.bbands(length=20, append=True)
        
        # Ham Fiyatları çıkarıyoruz, AI sadece trendlere bakacak
        features = df.copy().drop(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'], errors='ignore')
        
        # Son günün (bugünün/o anın) verisini al
        latest_data = features.iloc[[-1]]
        
        # Modelin eğitim sırasında gördüğü sütunları eşitle (Makro veriler yoksa 0 ata)
        for col in model.feature_names_in_:
            if col not in latest_data.columns:
                latest_data[col] = 0.0
                
        # Sütun sırasını modelin beklediği sıraya diz
        latest_data = latest_data[model.feature_names_in_]
        
        # Yapay Zeka Karar Veriyor!
        prediction = model.predict(latest_data)
        
        if prediction[0] == 1:
            return "AL 🟢"
        else:
            return "SAT 🔴"
            
    except Exception as e:
        print(f"AI Tahmin Hatası ({ticker}): {e}")
        return "HATA"

# Dosya ilk okunduğunda modelleri yükle
load_all_models()