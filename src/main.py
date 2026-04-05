from fastapi import FastAPI
from src.routers import router as product_router

app = FastAPI(
    title="WatchDog Analytics API",
    description="Система мониторинга цен",
    version="0.1.0",
)

app.include_router(product_router)

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "WatchDog is alive!"}