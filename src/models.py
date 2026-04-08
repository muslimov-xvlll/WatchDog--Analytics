from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, BigInteger
from sqlalchemy.sql import func
from src.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    target_price = Column(Float, nullable=False)
    last_price = Column(Float, nullable=True)

    user_telegram_id = Column(BigInteger, nullable=False)

    is_active = Column(Boolean, default=True)  # Активен ли парсинг этого товара
    unsupported_notified = Column(Boolean, default=False)  # Отправляли ли мы извинения
    is_subscribed = Column(Boolean, default=False)  # Заглушка для будущей подписки


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)


class UnsupportedDomain(Base):
    __tablename__ = "unsupported_domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, nullable=False)
    request_count = Column(Integer, default=1)  # Счетчик запросов
    created_at = Column(DateTime(timezone=True), server_default=func.now())