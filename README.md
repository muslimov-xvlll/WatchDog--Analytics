# 🐾 WatchDog‑Analytics — сервис для мониторинга цен и уведомлений о снижении

WatchDog‑Analytics — это Telegram‑бот и backend‑сервис, который позволяет пользователям отслеживать цены на товары с любых сайтов и получать уведомления при снижении до целевой стоимости.  
Проект ориентирован на **масштабируемость**, **асинхронность**, **очереди Kafka** и **монетизацию через Telegram Stars**.

---

## 🚀 Основные возможности

- Отслеживание цен на товары с любых сайтов  
- Уведомления при снижении цены  
- Ограничение бесплатного тарифа (3 товара)  
- Платная подписка через **Telegram Stars**  
- Асинхронный парсинг товаров  
- Kafka‑очереди для распределения задач  
- Black List сайтов, где парсинг временно отключён  
- Docker‑окружение для быстрого запуска

---

## 🧱 Архитектура проекта
```txt
watchdog/
│── migrations/              # Миграции БД (Alembic)
│── src/
│     ├── bot/
│     │     └── main.py      # Telegram-бот, обработка команд
│     ├── services/
│     │     ├── kafka_consumer.py   # Получение сообщений из Kafka
│     │     ├── kafka_producer.py   # Отправка задач в Kafka
│     │     ├── parser.py           # Парсинг цен с сайтов
│     │     ├── scheduler.py        # Планировщик задач
│     │     ├── telegram_notifier.py# Отправка уведомлений пользователям
│     │     ├── config.py           # Настройки окружения
│     │     ├── database.py         # Подключение к PostgreSQL
│     │     ├── dependencies.py     # DI и вспомогательные зависимости
│     │     ├── main.py             # Точка входа FastAPI
│     │     ├── models.py           # ORM-модели (SQLAlchemy async)
│     │     ├── routers.py          # API-роуты
│     │     └── schemas.py          # Pydantic-схемы
│── Dockerfile
│── docker-compose.yml
│── alembic.ini
│── pyproject.toml
│── poetry.lock
│── test_consumer.py
│── .gitignore
```

---

## 🧩 Ключевые компоненты

- **FastAPI** — backend и API  
- **Asyncio + aiohttp** — асинхронный парсинг  
- **Kafka** — очереди задач  
- **PostgreSQL** — хранение пользователей и товаров  
- **Docker** — изолированное окружение  
- **Telegram Stars** — монетизация  

---

## 🛠 Технологический стек

- Python 3.10+  
- FastAPI  
- Asyncio / aiohttp  
- BeautifulSoup4  
- Kafka  
- PostgreSQL  
- SQLAlchemy (async)  
- Docker / docker‑compose  
- Poetry  

---

## ▶️ Запуск проекта

### 1. Клонировать репозиторий
```bash
git clone https://github.com/yourname/watchdog-analytics.git
cd watchdog-analytics
```

### 2. Установить зависимости
```bash
poetry install
```

### 3. Запустить инфраструктуру (Kafka + PostgreSQL)
```bash
docker-compose up -d
```

### 4. Запустить приложение
```bash
poetry run python src/services/main.py
```


## 📬 Контакты
Если хотите обсудить проект или сотрудничество — буду рад связаться.

tg: @back_xvll
