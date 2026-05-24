import pandas as pd
import pandas_ta as ta
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "data", "processed")

# İşlenmiş veriler için yeni klasör oluştur
os.makedirs(PROCESSED_DIR, exist_ok=True)

def add_technical_indicators(df):
    """Verilen DataFrame'e finansal indikatörleri ekler."""
    # Orijinal veriyi bozmamak için kopyalıyoruz
    data = df.copy()
    
    # 1. Trend İndikatörleri
    data.ta.sma(length=10, append=True) # Kısa Vade Trend
    data.ta.sma(length=50, append=True) # Orta Vade Trend
    data.ta.sma(length=200, append=True) # Uzun Vade Trend
    data.ta.macd(append=True) # MACD
    
    # 2. Momentum İndikatörleri
    data.ta.rsi(length=14, append=True) # RSI (Aşırı Alım/Satım)
    
    # 3. Volatilite İndikatörleri
    data.ta.bbands(length=20, append=True) # Bollinger Bantları
    
    return data

def process_and_merge_data():
    print("-" * 50)
    print("VERİLER İŞLENİYOR VE İNDİKATÖRLER HESAPLANIYOR...")
    print("-" * 50)
    
    # Makro veriyi yükle
    macro_path = os.path.join(RAW_DIR, "MACRO_raw.csv")
    if os.path.exists(macro_path):
        macro_df = pd.read_csv(macro_path, index_col="Date", parse_dates=True)
    else:
        print("HATA: Makro veri bulunamadı! Önce download_history.py çalıştırılmalı.")
        return

    # Raw klasöründeki hisse dosyalarını bul
    for filename in os.listdir(RAW_DIR):
        if filename.endswith("_raw.csv") and "MACRO" not in filename:
            ticker_name = filename.replace("_raw.csv", "")
            print(f"⚙️ İşleniyor: {ticker_name}...")
            
            # Hisse verisini yükle
            file_path = os.path.join(RAW_DIR, filename)
            stock_df = pd.read_csv(file_path, index_col="Date", parse_dates=True)
            
            # Teknik indikatörleri hesapla
            stock_df = add_technical_indicators(stock_df)
            
            # Makro verilerle aynı tarihleri eşleştirerek birleştir (Inner Join)
            # Böylece yapay zeka o günkü hisse fiyatıyla o günkü Dolar ve VIX kurunu aynı satırda görecek
            merged_df = stock_df.join(macro_df, how="inner")
            
            # İndikatör hesaplamalarından (örn: SMA_200 için ilk 200 gün boştur) kaynaklı NaN (boş) değerleri sil
            merged_df.dropna(inplace=True)
            
            # İşlenmiş veriyi kaydet
            save_name = f"{ticker_name}_processed.csv"
            save_path = os.path.join(PROCESSED_DIR, save_name)
            merged_df.to_csv(save_path)
            
            print(f"   ✅ Hazır! Satır Sayısı: {len(merged_df)} | Kaydedildi: {save_name}")

    print("\n🚀 Bütün veriler yapay zeka modeli (AI) için hazır hale getirildi!")

if __name__ == "__main__":
    process_and_merge_data()