from fastapi import FastAPI

app = FastAPI(
    title="WatchDog Analytics API",
    description="Система мониторинга цен",
    version="0.1.0",
)

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "WatchDog is alive!"}