import httpx
import logging
from src.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_message(text: str):
    """
    Отправляет текстовое сообщение в Telegram через официальный API
    """
    #Формируем ссылку с нашим токеном
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    #Собираем сообщение и прописываем кому отправляем
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode" : "HTML" # Позволит нам делать текст жирным с помощью тегов
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status() # Проверяем, что Telegram ответил статусом 200 OK
            logger.info("Уведомление успешно отправлено в Telegram!")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")


