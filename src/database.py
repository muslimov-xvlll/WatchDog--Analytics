from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from src.config import settings

#Создаем ассинхронный движок (echo True - временно для дебага)
engine = create_async_engine(settings.database_url, echo=True)

#Создаем фабрику сессий. Через сессии будут отправляться запросы в базу
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#Базовый класс, от которого будут наследоваться все наши модели (таблицы)
Base = declarative_base()

