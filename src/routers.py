from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.dependencies import get_db
from src.schemas import ProductRead, ProductCreate
from src.models import Product

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    # str(product.url) нужен, так как HttpUrl в Pydantic - это сложный объект, а БД ждет строку
    new_product = Product(
        name=product.name,
        url=str(product.url),
        target_price=product.target_price
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return new_product

@router.get("/", response_model=List[ProductRead])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products