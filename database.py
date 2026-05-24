from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Şimdilik yerelde hızlı test için SQLite kullanıyoruz.
# Sunucuya geçtiğimizde bu satırı PostgreSQL URL'si ile değiştireceğiz.
SQLALCHEMY_DATABASE_URL = "sqlite:///./trading_data.db"

# SQLite asenkron işlemlerde thread hatası vermesin diye "check_same_thread" kapatılır
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Veritabanı oturumu açıp kapatmak için yardımcı fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()