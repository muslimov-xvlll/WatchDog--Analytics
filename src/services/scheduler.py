import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models import Product
from src.services.parser import fetch_price
from src.services.kafka_producer import send_price_to_kafka

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#Интервал парсера цен
CHECK_INTERVAL_SECONDS = 30

async def check_all_prices():
    """
    Достает все товары из БД и по очереди отправляет их в парсер
    """
    logger.info("Планировщик начинает обход всех товаров...")

    async with async_session_maker() as session:
        #Достаем все записи из Product
        result = await session.execute(select(Product))
        products = result.scalars().all()

        if not products:
            logger.info("Пока не чего отслеживать")
            return

        for product in products:
            logger.info(f"Проверяем товар ID={product.id}")
            try:
                # Идем парсить
                price = await fetch_price(product.url)

                if price is not None:
                    # Кидаем в Kafka
                    await send_price_to_kafka(product.id, price)
                else:
                    logger.warning(f"Не удалось найти цену для ID={product.id}")
            except Exception as e:
                logger.error(f"Ошибка при обработке ID={product.id}: {e}")
    logger.info("Обход завершен, планировщик засыпает...")

async def start_scheduler():
    """
    Бесконечный цикл планировщика
    """
    logger.info("Фоновый планировщик успешно запущен")
    try:
        while True:
            await check_all_prices()
            #Засыпаем, отдавая процессорное время другим задачам
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("Планировщик остановлен")


