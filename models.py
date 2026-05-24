from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime, timezone

class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    price = Column(Float)
    volume = Column(Integer)
    # Verinin kaydedildiği anki UTC zamanını otomatik atar
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))