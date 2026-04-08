import httpx
import logging
from src.config import settings

logger = logging.getLogger(__name__)

# ДОБАВИЛИ аргумент user_id
async def send_telegram_message(user_id: int, text: str):
    """
    Отправляет текстовое сообщение в Telegram через официальный API
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": user_id, # ТЕПЕРЬ ОТПРАВЛЯЕМ КОНКРЕТНОМУ ПОЛЬЗОВАТЕЛЮ
        "text": text,
        "parse_mode" : "HTML",
        "disable_web_page_preview": True # Убираем огромное превью сайта
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Уведомление успешно отправлено пользователю {user_id}!")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")