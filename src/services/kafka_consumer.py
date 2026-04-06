import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from src.database import async_session_maker
from src.models import PriceHistory, Product

# Настраиваем логгер для этого файла
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def save_price_to_db(product_id: int, price: float):
    async with async_session_maker() as session:
        new_price_record = PriceHistory(product_id=product_id, price=price)
        session.add(new_price_record)

        # Достаем информацию о самом товаре из базы
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()

        if product:
            # Сравниваем цены
            if price <= product.target_price:
                logger.warning(
                    f"\n\nБИНГО! Товар ID={product.id} достиг цели!"
                    f"Текущая цена: {price} <= Желаемая: {product.target_price}. Пора покупать!\n\n"
                )
            else:
                logger.info(
                    f"\n\nТовар ID={product.id}. Текущая цена {price} "
                    f"пока выше желаемой {product.target_price}. Ждем...\n\n"
                )
        await session.commit()


async def start_consuming():
    consumer = AIOKafkaConsumer(
        'product_prices',
        bootstrap_servers='kafka:9092',
        # Дадим группе финальное красивое имя
        group_id="watchdog_db_writer_main",
        auto_offset_reset='earliest',
        #Исправленный десериализатор
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    # --- ДОБАВЛЯЕМ БЛОК ПОВТОРНЫХ ПОПЫТОК ---
    connected = False
    for i in range(6):  # Делаем 6 попыток (итого 30 секунд ожидания)
        try:
            logger.info(f"Попытка подключения к Kafka ({i + 1}/6)...")
            await consumer.start()
            connected = True
            break  # Если подключились, выходим из цикла
        except Exception as e:
            logger.warning(f"Kafka еще не готова. Ждем 5 секунд... Ошибка: {e}")
            await asyncio.sleep(5)

    if not connected:
        logger.error("КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к Kafka!")
        return  # Выходим из функции, Слушатель не запустится
    # ----------------------------------------
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