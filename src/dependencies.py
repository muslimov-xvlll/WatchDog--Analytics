from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import async_session_maker

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # async with гарантирует, что сессия закроется даже при ошибке
    async with async_session_maker () as session:
        yield session