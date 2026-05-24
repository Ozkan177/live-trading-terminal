import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "data", "processed")
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")

# Modellerin kaydedileceği klasörü oluştur
os.makedirs(MODEL_DIR, exist_ok=True)

def prepare_data(df):
    """Yapay zeka için 'Geleceği' hedef olarak belirler."""
    data = df.copy()
    
    # HEDEF (Target) BELİRLEME: 
    # Eğer yarının kapanış fiyatı bugünden büyükse 1 (AL), küçükse 0 (SAT)
    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    
    # shift(-1) yaptığımız için en son günün 'yarını' yoktur, bu boş satırı siliyoruz
    data.dropna(inplace=True)
    
    # Modelin kafasını karıştırmamak için doğrudan fiyatları değil, indikatörleri kullanacağız
    # Kapanış, Açılış gibi ham fiyatları çıkarıyoruz. AI sadece trendlere ve makroya bakacak.
    features = data.drop(columns=['Target', 'Open', 'High', 'Low', 'Close'])
    labels = data['Target']
    
    return features, labels

def train_and_evaluate():
    print("-" * 50)
    print("YAPAY ZEKA MODELLERİ EĞİTİLİYOR (XGBoost)...")
    print("-" * 50)
    
    for filename in os.listdir(PROCESSED_DIR):
        if filename.endswith("_processed.csv"):
            ticker = filename.replace("_processed.csv", "")
            print(f"\n🧠 {ticker} için model eğitiliyor...")
            
            # Veriyi yükle
            filepath = os.path.join(PROCESSED_DIR, filename)
            df = pd.read_csv(filepath, index_col="Date", parse_dates=True)
            
            # Özellikleri (X) ve Hedefi (y) ayır
            X, y = prepare_data(df)
            
            # Verinin %80'ini eğitim, %20'sini test (sınav) için ayır
            # shuffle=False çok önemlidir! Finansal serilerde geçmişten geleceğe doğru test yapılmalıdır.
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            # XGBoost Modelini Tanımla
            model = xgb.XGBClassifier(
                n_estimators=100,      # Ağaç sayısı
                learning_rate=0.05,    # Öğrenme hızı (düşük olması ezberlemeyi önler)
                max_depth=5,           # Derinlik
                random_state=42,
                eval_metric="logloss"
            )
            
            # Modeli Eğit (Ders Çalış)
            model.fit(X_train, y_train)
            
            # Test verisiyle sınav yap (Görmediği verilerde tahmin yap)
            predictions = model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            
            print(f"   📊 Sınav Başarısı (Accuracy): %{accuracy * 100:.2f}")
            
            # Eğitilmiş modeli canlı sistemde kullanmak üzere kaydet
            model_path = os.path.join(MODEL_DIR, f"{ticker}_xgboost.pkl")
            joblib.dump(model, model_path)
            
            # Hangi verilerin kararı daha çok etkilediğini bul
            feature_importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
            top_3_features = feature_importances.head(3).index.tolist()
            print(f"   🔍 En çok dikkat ettiği 3 veri: {top_3_features}")
            print(f"   💾 Kaydedildi: {ticker}_xgboost.pkl")

    print("\n✅ Bütün modeller başarıyla eğitildi ve 'models' klasörüne kaydedildi!")

if __name__ == "__main__":
    train_and_evaluate()