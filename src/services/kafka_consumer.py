import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from src.database import async_session_maker
from src.models import PriceHistory

# Настраиваем логгер для этого файла
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def save_price_to_db(product_id: int, price: float):
    async with async_session_maker() as session:
        new_price_record = PriceHistory(product_id=product_id, price=price)
        session.add(new_price_record)
        await session.commit()
        logger.info(f"Сохранено в БД: товар ID={product_id}, цена={price}")


async def start_consuming():
    consumer = AIOKafkaConsumer(
        'product_prices',
        bootstrap_servers='localhost:9092',
        # Дадим группе финальное красивое имя
        group_id="watchdog_db_writer_main",
        # Наш исправленный десериализатор!
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    await consumer.start()
    logger.info("Фоновый слушатель Kafka успешно подключился и ждет сообщений...")

    try:
        async for msg in consumer:
            data = msg.value
            logger.info(f"Поймано сообщение из Kafka: {data}")

            try:
                await save_price_to_db(product_id=data['product_id'], price=data['price'])
            except Exception as e:
                logger.error(f"Ошибка сохранения в БД для сообщения {data}: {e}")

    except asyncio.CancelledError:
        logger.info("Задача слушателя отменена (Сервер останавливается)")
    except Exception as e:
        logger.error(f"Критическая ошибка в цикле слушателя: {e}")
    finally:
        logger.info("Слушатель отключается от брокера Kafka")
        await consumer.stop()