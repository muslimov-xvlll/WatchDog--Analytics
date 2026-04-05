from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

from src.services.kafka_consumer import start_consuming
from src.routers import router as product_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Этот блок выполнится только при старте сервера
    print ("Старт сервера: запускаем фоновые процессы...")

    # Запускаем слушателя на независимую фоновую задачБ чтобы не перенагружать сервер
    app.state.consumer_task = asyncio.create_task(start_consuming())

    yield

    # Этот блок выполнится только при остановке сервера
    print("Остановка сервера: останавливаем фоновые процессы...")
    app.state.consumer_task.cancel()

    try:
        await app.state.consumer_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="WatchDog-Analytics API", lifespan=lifespan)
app.include_router(product_router, prefix="/products", tags=["Products"])













# app = FastAPI(
#     title="WatchDog Analytics API",
#     description="Система мониторинга цен",
#     version="0.1.0",
# )
#
# app.include_router(product_router)
#
# @app.get("/ping")
# async def ping():
#     return {"status": "ok", "message": "WatchDog is alive!"}