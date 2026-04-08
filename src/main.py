import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Импортируем движок и базу
from src.database import engine, Base
# Обязательно импортируем модели перед созданием таблиц, чтобы SQLAlchemy их увидела
from src.models import Product, PriceHistory, UnsupportedDomain

# Фоновые процессы
from src.services.kafka_consumer import start_consuming
from src.services.scheduler import start_scheduler

# Импортируем наши роутеры
from src.routers import product_router, utils_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. ИНИЦИАЛИЗИРУЕМ БАЗУ ДАННЫХ
    logger.info("Инициализация базы данных: создаем таблицы...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. ЗАПУСКАЕМ ФОНОВЫЕ ПРОЦЕССЫ
    logger.info("Старт сервера: запускаем фоновые процессы...")
    app.state.consumer_task = asyncio.create_task(start_consuming())
    app.state.scheduler_task = asyncio.create_task(start_scheduler())

    yield # Сервер принимает запросы

    # 3. ОСТАНАВЛИВАЕМ СЕРВЕР И ПРОЦЕССЫ
    logger.info("Остановка сервера: останавливаем фоновые процессы...")
    app.state.consumer_task.cancel()
    app.state.scheduler_task.cancel()

    try:
        await app.state.consumer_task
    except asyncio.CancelledError:
        pass

    try:
        await app.state.scheduler_task
    except asyncio.CancelledError:
        pass

    # 4. ЗАКРЫВАЕМ БАЗУ
    await engine.dispose()


# СОЗДАЕМ ПРИЛОЖЕНИЕ
app = FastAPI(
    title="WatchDog Analytics API",
    description="Микросервисная система мониторинга цен",
    version="0.1.0",
    lifespan=lifespan
)

# ПОДКЛЮЧАЕМ НАШИ РУЧКИ
app.include_router(product_router)
app.include_router(utils_router)

# Оставляем простую ручку для проверки работоспособности сервера (Healthcheck)
@app.get("/ping", tags=["System"])
async def ping():
    return {"status": "ok", "message": "WatchDog is alive!"}