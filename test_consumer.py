import asyncio
from aiokafka import AIOKafkaConsumer

async def consume():
    # Создаем слушателя
    consumer = AIOKafkaConsumer(
        'product_prices',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest', # Говорим Kafka: Отдай мне данные с самого начала
        group_id="test_group_1"
    )

    print("Подключение к Kafka...")
    await consumer.start()
    print("✅ Успешно! Слушаем топик 'product_prices'...\n")

    try:
        async for msg in consumer:
            print(f"Поймано сообщние")
            print(f"Раздел (Partition): {msg.partition}, Смещение (Offset): {msg.offset}")
            print(f"Данные: {msg.value.decode('utf-8')}\n")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await consumer.stop()
if __name__ == "__main__":
    asyncio.run(consume())