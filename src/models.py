from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

from src.database import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    target_price: Mapped[int] = mapped_column(Integer, nullable=False)