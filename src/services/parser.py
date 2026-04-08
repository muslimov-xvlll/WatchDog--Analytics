from http.client import responses

import httpx
from bs4 import BeautifulSoup
import json
import logging

from click import clear

# Настройка базового логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- НОВАЯ СЕКЦИЯ: Ищейка по JSON ---
def find_product_data(data):
    """
    Рекурсивно обыскивает JSON-объект любой сложности
    в поисках словаря, где @type == 'Product'
    """
    if isinstance(data, dict):
        # Иногда @type - это строка, а иногда список (например ["Product", "Thing"])
        item_type = data.get('@type', '')
        if item_type == 'Product' or (isinstance(item_type, list) and 'Product' in item_type):
            return data

        # Если это не товар, проверяем все вложенные словари (например, внутри @graph)
        for key, value in data.items():
            result = find_product_data(value)
            if result:
                return result

    elif isinstance(data, list):
        # Если это список, проверяем каждый элемент
        for item in data:
            result = find_product_data(item)
            if result:
                return result

    return None


# -----------------------------------

async def fetch_price(url: str) -> float | None:
    """
    Универсальный парсер. Ищет цену через микроразметку json_ld,
    если не находит - возвращает None
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error(f"Ошибка при скачивании страницы {url}: {e}")
            return None

        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                # Используем нашу новую функцию-ищейку
                product_item = find_product_data(data)

                if product_item:
                    offers = product_item.get('offers')
                    if not offers:
                        continue

                    # Offers тоже бывает списком или словарем
                    if isinstance(offers, list):
                        offer = offers[0]
                    else:
                        offer = offers

                    price = offer.get('price')
                    if price is not None:
                        logger.info(f"🧠 Умный парсер нашел цену: {price}")
                        clean_price = str(price).replace(',', '.')
                        return float(clean_price)

            except (json.JSONDecodeError, ValueError):
                continue
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при разборе JSON-LD: {e}")

            logger.warning(f"⚠️ JSON-LD с товаром не найден на странице {url}")
            return None
