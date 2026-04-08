import logging
from urllib.parse import urlparse
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from src.dependencies import get_db
from src.schemas import ProductRead, ProductCreate, ProductUpdatePrice
from src.models import Product, UnsupportedDomain
from src.services.parser import fetch_price
from src.database import async_session_maker


logger = logging.getLogger(__name__)

# --- РОУТЕРЫ ---
# Роутер для основных действий с товарами
product_router = APIRouter(prefix="/products", tags=["Products"])

# Роутер для дополнительных утилит
utils_router = APIRouter(tags=["Utilities"])


# ==========================================
# ЭНДПОИНТЫ: ТОВАРЫ (Products)
# ==========================================

@product_router.post("/", response_model=ProductRead)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    # --- 1. ПРОВЕРКА ЛИМИТА (ПЕЙВОЛ) ---
    FREE_LIMIT = 3

    # Считаем, сколько товаров уже есть у этого пользователя
    count_query = select(func.count(Product.id)).where(Product.user_telegram_id == product.user_telegram_id)
    result = await db.execute(count_query)
    user_products_count = result.scalar()

    if user_products_count >= FREE_LIMIT:
        # Если лимит исчерпан, возвращаем ошибку 403 (Forbidden)
        raise HTTPException(
            status_code=403,
            detail="LIMIT_REACHED"
        )

    # --- 2. ЕСЛИ ЛИМИТ НЕ ИСЧЕРПАН, СОХРАНЯЕМ ТОВАР ---
    new_product = Product(
        name=product.name,
        url=str(product.url),
        target_price=product.target_price,
        last_price=product.last_price,
        user_telegram_id=product.user_telegram_id
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return new_product


@product_router.get("/", response_model=List[ProductRead])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products


# ==========================================
# ЭНДПОИНТЫ: УТИЛИТЫ (Utilities)
# ==========================================

class URLCheckRequest(BaseModel):
    url: str


@utils_router.post("/check-url/", summary="Проверить поддержку сайта (до подписки)")
async def check_url_support(request: URLCheckRequest):
    # Очищаем от пробелов и добавляем https:// если пользователь забыл
    url = request.url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    domain = urlparse(url).netloc
    logger.info(f"🔎 Пользователь запросил проверку домена: {domain}")

    async with async_session_maker() as session:
        # Проверяем черный список
        result = await session.execute(
            select(UnsupportedDomain).where(UnsupportedDomain.domain == domain)
        )
        unsupported = result.scalar_one_or_none()

        if unsupported:
            unsupported.request_count += 1
            await session.commit()
            logger.info(
                f"🛑 ЭКОНОМИЯ: Домен {domain} в черном списке. Запросов: {unsupported.request_count}. Отклоняем.")
            return {
                "is_supported": False,
                "message": "❌ Мы знаем об этом сайте и уже работаем над его интеграцией! Спасибо за ожидание."
            }

        # Если домена нет в списке - пытаемся распарсить
        logger.info(f"🌐 Домен {domain} не найден в базе. Запускаем умный парсер...")
        price = await fetch_price(request.url)

        if price is not None:
            logger.info(f"✅ УСПЕХ: Домен {domain} успешно распарсился!")
            return {"is_supported": True, "price": price, "message": f"✅ Сайт поддерживается! Текущая цена: {price}"}
        else:
            new_unsupported = UnsupportedDomain(domain=domain, request_count=1)
            session.add(new_unsupported)
            await session.commit()
            logger.warning(f"⚠️ ПРОВАЛ: Домен {domain} не содержит JSON-LD. Заносим в черный список.")
            return {
                "is_supported": False,
                "message": "❌ Извините, этот сайт пока не поддерживается. Мы зафиксировали ваш запрос и передали разработчикам!"
            }


@product_router.get("/user/{telegram_id}", response_model=List[ProductRead])
async def get_user_product(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Получить список всех товаров конкретного пользователя"""
    result = await db.execute(
        select(Product).where(Product.user_telegram_id == telegram_id)
    )
    return result.scalars().all()

@product_router.patch("/{product_id}/price", response_model=ProductRead)
async def update_product_price(
        product_id: int,
        price_data: ProductUpdatePrice,
        db: AsyncSession = Depends(get_db)
):
    """Изменить целевую цену товара"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    product.target_price = price_data.target_price
    product.is_active = True

    await db.commit()
    await db.refresh(product)
    return product


@product_router.delete("/{product_id}", response_model=ProductRead)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить товар и вернуть его данные для уведомления"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Создаем копию данных для ответа, прежде чем удалить из БД
    product_data = ProductRead.model_validate(product)

    await db.delete(product)
    await db.commit()

    return product_data  # Теперь возвращаем JSON с именем товара