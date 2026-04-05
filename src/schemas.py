from pydantic import BaseModel, HttpUrl, ConfigDict

# Базовая схема
class ProductBase(BaseModel):
    name: str
    url: HttpUrl
    target_price: int

# Схема для создания товара
class ProductCreate(ProductBase):
    pass

# Схема для Чтения товара
class ProductRead(ProductBase):
    id: int

    # Указываем Pydantic V2, что данные придут не из обычного словара
    # а из ORM-модели, чтобы он смог их правильно прочитать
    model_config = ConfigDict(from_attributes=True)
