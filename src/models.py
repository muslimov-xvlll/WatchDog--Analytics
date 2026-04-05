from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, func

from src.database import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)

    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ForeignKey указывает, что эта колонка ссылается на id из таблицы products
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    # Цену делаем Float (вещественное число), так как могут быть копейки/центы
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Дата создания записи. server_default=func.now() заставит сам Postgres
    # автоматически подставлять текущее время при добавлении новой строки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Обратная связь с таблицей Product
    product = relationship("Product", back_populates="prices")