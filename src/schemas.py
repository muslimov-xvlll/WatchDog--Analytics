from typing import Optional

from pydantic import BaseModel, HttpUrl, ConfigDict

# Базовая схема
class ProductBase(BaseModel):
    name: str
    url: HttpUrl
    target_price: float
    last_price: Optional[float] = 0.0

# Схема для создания товара
class ProductCreate(BaseModel):
    name : str
    url: HttpUrl
    target_price: float
    last_price: float
    user_telegram_id: int

# Схема для Чтения товара (то, что улетает в нашего бота)
class ProductRead(ProductBase):
    id: int
    is_active: bool # Отдаем статус, чтобы бот рисовал 🟢 или 🔴

    # Указываем Pydantic, что данные придут из ORM-модели (базы данных)
    model_config = ConfigDict(from_attributes=True)

class ProductUpdatePrice(BaseModel):
    target_price: float