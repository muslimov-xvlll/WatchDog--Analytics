import json
from aiokafka import AIOKafkaProducer
import logging

logger = logging.getLogger(__name__)

#Настройка подключения. Позже вынесу в config.py
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
KAFKA_TOPIC_PRICES = "product_prices"

async def send_price_to_kafka(producer_id: int, price: float):
    """
    Отправляет информацию об обновленной цене в Kafka
    """
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
        # Учим продюсера автоматически превращать словари Python в JSON-строки
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await producer.start()
    try:
        payload = {
            "product_id": producer_id,
            "price": price
        }
        # Отправляем сообщение в topic
        await producer.send_and_wait(KAFKA_TOPIC_PRICES, payload)
        logger.info(f"Sent price update to Kafka: {payload}")
    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}")
    finally:
        await producer.stop()
