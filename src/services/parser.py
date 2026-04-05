from http.client import responses

import httpx
from bs4 import BeautifulSoup
import logging

# Настройка базового логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_price(url: str) -> float | None:
    """
    Ассинхронно скачивает страницу и пытается найти на ней цену
    """

    #Добавляем User-Agent, чтобы сайты не отбивали нас сразу как бота
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36)"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")


            price_element = soup.select_one("p.price_color")

            if price_element:
                price_text = price_element.text.replace('£', '').replace('€', '').replace('$', '').strip()
                return float(price_text)

            logger.warning(f"Цена не найдена на странице: {url}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Ошибка сети при запросе к: {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при парсинге {url}: {e}")
            return None



