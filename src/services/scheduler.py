import asyncio
import logging
from sqlalchemy import select
from src.database import async_session_maker
from src.services.parser import fetch_price
from src.services.kafka_producer import send_price_to_kafka
from src.services.telegram_notifier import send_telegram_message
from urllib.parse import urlparse
from src.models import Product, UnsupportedDomain

logger = logging.getLogger(__name__)


async def check_prices():
    async with async_session_maker() as session:
        result = await session.execute(select(Product).where(Product.is_active == True))
        products = result.scalars().all()

        if not products:
            logger.info("🤷‍♂️ В базе пока нет активных товаров для отслеживания.")
            return

        for product in products:
            logger.info(f"🔍 Планировщик взял в работу товар ID={product.id} (URL: {product.url})")
            price = await fetch_price(product.url)

            if price is None:
                # --- ЛОГИКА АНАЛИТИКИ (ЧЕРНЫЙ СПИСОК) ---
                domain = urlparse(product.url).netloc

                # Проверяем, есть ли уже этот домен в базе неподдерживаемых
                res = await session.execute(
                    select(UnsupportedDomain).where(UnsupportedDomain.domain == domain)
                )
                unsupported = res.scalar_one_or_none()

                if unsupported:
                    # Если домен уже там — просто увеличиваем счетчик "хитов"
                    unsupported.request_count += 1
                    logger.info(f"📈 Обновили счетчик для {domain}: {unsupported.request_count}")
                else:
                    # Если домена еще нет — создаем первую запись
                    logger.warning(f"🤖 Новый неподдерживаемый домен обнаружен: {domain}. Добавляем в аналитику.")
                    new_unsupported = UnsupportedDomain(domain=domain, request_count=1)
                    session.add(new_unsupported)

                # --- ЛОГИКА УВЕДОМЛЕНИЯ ПОЛЬЗОВАТЕЛЯ ---
                if not product.unsupported_notified:
                    logger.info(f"✉️ Отправляем извинения в Telegram для товара ID={product.id}")
                    msg = (
                        f"⚠️ <b>Отслеживание приостановлено</b>\n\n"
                        f"К сожалению, сайт <code>{domain}</code> сейчас не поддерживается.\n"
                        f"Мы уже передали эту информацию разработчикам!"
                    )
                    await send_telegram_message(msg)

                    # Отключаем товар в БД, чтобы планировщик его больше не трогал
                    product.is_active = False
                    product.unsupported_notified = True

                # Сохраняем изменения (инкремент счетчика и статус товара)
                await session.commit()
                continue

            # Если цена нашлась успешно
            logger.info(f"🎯 Товар ID={product.id}: цена {price} найдена. Отправляем в Kafka.")
            await send_price_to_kafka(producer_id=product.id, price=price)


async def start_scheduler():
    logger.info("⏰ Фоновый планировщик успешно запущен!")
    while True:
        try:
            logger.info("🔄 Планировщик начинает обход всех активных товаров...")
            await check_prices()
            logger.info("💤 Обход завершен, планировщик засыпает на 30 секунд...")
        except Exception as e:
            # exc_info=True покажет нам в логах точную строку, где произошла ошибка!
            logger.error(f"❌ Критическая ошибка в цикле планировщика: {e}", exc_info=True)

        await asyncio.sleep(30)